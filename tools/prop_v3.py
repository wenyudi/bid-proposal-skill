#!/usr/bin/env python3
"""proposal v3 canonical state, context compiler and delivery gates.

The module intentionally depends only on the Python standard library.  It is
imported by ``prop_tools.py`` so the historic command surface stays intact.

Canonical files are the only writable source of truth.  Everything under
``derived/`` is reproducible and is therefore never accepted as an authority
for a canonical mutation.
"""

import copy
import calendar
import datetime
import hashlib
import json
import os
import re
import shutil
import tempfile
import uuid


ENGINE = "v3"
ENGINE_VERSION = "3.0"
POLICY_VERSION = "proposal-v3/policy-1"
CONTEXT_POLICY_VERSION = "proposal-v3/context-1"
REALIZATION_POLICY_VERSION = "proposal-v3/realization-1"
FIT_POLICY_VERSION = "proposal-v3/customer-fit-1"

SAFE_PUBLICATION_VISIBILITIES = {
    "public", "tender", "authorized_source", "approved_anonymized", "named",
}
ALLOWED_EVIDENCE_USES = {
    "matching", "benchmark", "proposal_narrative", "bidder_capability",
    "commitment_authority", "anonymized_publication", "named_publication",
    "qualification_attachment", "numeric_result", "client_name", "logo",
    "testimonial", "capability_reasoning",
}

CANONICAL_FILES = (
    "requirements.json",
    "customer-value.json",
    "delivery-plan.json",
    "strategy.json",
    "intel-pool.json",
)

SCHEMA_VERSIONS = {
    "requirements.json": "requirements/v3",
    "customer-value.json": "customer-value/v1",
    "delivery-plan.json": "delivery-plan/v1",
    "strategy.json": "strategy/v3",
    "intel-pool.json": "intel-pool/v3",
    "source-manifest.json": "source-manifest/v1",
    "run-manifest.json": "run-manifest/v1",
    "changeset": "changeset/v1",
    "brief": "context-brief/v1",
    "snapshot": "generation-snapshot/v1",
    "realization": "realization/v1",
    "coverage": "coverage/v1",
    "fit": "customer-fit/v1",
}

ENTITY_COLLECTIONS = {
    "requirements.json": ("mandatory", "scoring", "deliverables"),
    "customer-value.json": (
        "roles", "needs", "criteria", "role_need_links",
        "need_criterion_links", "role_criterion_links", "value_propositions",
        "claims", "metrics", "evidence_links", "role_conflicts",
    ),
    "delivery-plan.json": (
        "delivery_roles", "actions", "resource_envelopes",
        "customer_dependencies", "acceptance_contracts",
    ),
    "strategy.json": ("decision_jobs", "sections"),
    "intel-pool.json": ("evidence",),
}

COLLECTION_TYPES = {
    "mandatory": "requirement",
    "scoring": "requirement",
    "deliverables": "requirement",
    "roles": "customer_role",
    "needs": "customer_need",
    "criteria": "decision_criterion",
    "role_need_links": "role_need_link",
    "need_criterion_links": "need_criterion_link",
    "role_criterion_links": "role_criterion_link",
    "value_propositions": "value_proposition",
    "claims": "claim",
    "metrics": "metric",
    "evidence_links": "evidence_link",
    "role_conflicts": "role_conflict",
    "delivery_roles": "delivery_role",
    "actions": "delivery_action",
    "resource_envelopes": "resource_envelope",
    "customer_dependencies": "customer_dependency",
    "acceptance_contracts": "acceptance_contract",
    "decision_jobs": "decision_job",
    "sections": "section",
    "evidence": "evidence",
}

VP_STATES = {
    "candidate", "investigating", "qualified", "selected", "publishable",
    "rejected", "superseded",
}
NEED_STATES = {"candidate", "active", "contested", "superseded", "rejected"}
CLAIM_STATES = {"candidate", "draft_ready", "publishable", "contested", "withdrawn"}
CONTENT_KINDS = {"fact", "insight", "proposal", "target"}
EPISTEMIC_STATES = {"evidenced", "inferred", "assumed"}
COMMITMENT_LEVELS = {"none", "intended", "committed"}
JOB_KINDS = {"understand", "believe", "value", "deliver", "safe", "choose"}
CONTRIBUTIONS = {
    "introduce", "prove", "operationalize", "measure", "schedule", "resource",
    "accept", "price", "derisk", "summarize", "required_restatement",
}


def _read_json(path):
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def _read_text(path):
    with open(path, "r", encoding="utf-8-sig") as handle:
        return handle.read()


def _write_text_atomic(path, content):
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=".prop-v3-", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(temp_path, path)
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def _write_json_atomic(path, value):
    _write_text_atomic(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def _canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def content_hash(value):
    if isinstance(value, str):
        payload = value.encode("utf-8")
    else:
        payload = _canonical_json(value).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def file_hash(path):
    with open(path, "rb") as handle:
        return "sha256:" + hashlib.sha256(handle.read()).hexdigest()


def path_hash(path):
    """Hash a file or a directory tree without storing its contents."""
    if os.path.isfile(path):
        return file_hash(path)
    if os.path.isdir(path):
        records = []
        for root, dirs, files in os.walk(path):
            dirs.sort()
            for filename in sorted(files):
                full_path = os.path.join(root, filename)
                relative = os.path.relpath(full_path, path).replace(os.sep, "/")
                records.append({"path": relative, "hash": file_hash(full_path)})
        return content_hash(records)
    raise OSError("source path does not exist: %s" % path)


def _seal_source_manifest(manifest, base_dir):
    sealed = copy.deepcopy(manifest)
    for item in _as_list(sealed.get("sources")):
        if not isinstance(item, dict):
            continue
        source_path = item.get("path")
        if not source_path:
            continue
        resolved = source_path if os.path.isabs(source_path) else os.path.join(base_dir, source_path)
        if os.path.exists(resolved):
            actual = path_hash(resolved)
            supplied = item.get("hash")
            if supplied and supplied != actual:
                raise ValueError("source hash mismatch for %s" % (item.get("id") or source_path))
            item["hash"] = actual
            item["hash_provenance"] = "tool_computed"
        elif item.get("hash"):
            item.setdefault("hash_provenance", "presealed_unverified")
    return sealed


def _now_iso():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()


def _nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def _as_list(value):
    return value if isinstance(value, list) else []


def _ref_list(entity, *names):
    values = []
    for name in names:
        raw = entity.get(name)
        if isinstance(raw, str) and raw:
            values.append(raw)
        elif isinstance(raw, list):
            values.extend(item for item in raw if isinstance(item, str) and item)
    return values


def _entity_id(entity):
    if not isinstance(entity, dict):
        return None
    return entity.get("id") or entity.get("ref")


def _evidence_is_current(evidence):
    if not isinstance(evidence, dict) or evidence.get("status") != "active":
        return False
    valid_until = evidence.get("valid_until")
    if valid_until:
        match = re.match(r"^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?", str(valid_until))
        if match:
            year = int(match.group(1))
            month = int(match.group(2) or 12)
            day = int(match.group(3) or calendar.monthrange(year, month)[1])
            try:
                if datetime.date(year, month, day) < datetime.date.today():
                    return False
            except ValueError:
                return False
    return True


def _evidence_allowed_for(evidence, use):
    return use in _as_list((evidence or {}).get("allowed_uses"))


def _evidence_projection_ready(evidence, use="proposal_narrative"):
    if not isinstance(evidence, dict):
        return False
    if evidence.get("visibility") not in SAFE_PUBLICATION_VISIBILITIES:
        return False
    if not _evidence_allowed_for(evidence, use):
        return False
    if evidence.get("visibility") == "approved_anonymized":
        return (_nonempty(evidence.get("approved_projection"))
                and _nonempty(evidence.get("safe_title")))
    return _nonempty(evidence.get("approved_projection") or evidence.get("content"))


def _claim_proof_task(claim):
    explicit = claim.get("proof_task")
    if explicit:
        return explicit
    if (claim.get("content_kind") in ("proposal", "target")
            and (claim.get("commitment_level") == "committed"
                 or claim.get("risk_level") in ("high", "critical"))):
        return "bidder_capability"
    return "proposal_narrative"


def _evidence_support_usable(link, evidence, risk_level="medium",
                             proof_task="proposal_narrative"):
    if not isinstance(link, dict) or link.get("relation", "supports") != "supports":
        return False
    if not _evidence_is_current(evidence):
        return False
    if not _evidence_projection_ready(evidence, "proposal_narrative"):
        return False
    if proof_task != "proposal_narrative" and not _evidence_allowed_for(evidence, proof_task):
        return False
    if proof_task == "bidder_capability" and (
            evidence.get("third_party") is True
            or evidence.get("kind") in ("third_party_case", "buyer_case", "industry_case")):
        return False
    if link.get("strength") in (None, "weak", "unknown"):
        return False
    if not _nonempty(link.get("reason")) or not _nonempty(link.get("scope")):
        return False
    quality = evidence.get("quality")
    if risk_level in ("high", "critical"):
        return quality in ("high", "verified") and link.get("strength") in ("direct", "strong")
    return quality in ("medium", "high", "verified")


def _default_document(filename):
    base = {"schema_version": SCHEMA_VERSIONS[filename], "revision": 1}
    if filename == "requirements.json":
        base.update({
            "project_name": "", "project_no": "", "buyer": "",
            "budget_cap": {"value": None, "unit": ""},
            "mandatory": [], "scoring": [], "deliverables": [],
        })
    elif filename == "customer-value.json":
        base.update({
            "roles": [], "needs": [], "criteria": [],
            "role_need_links": [], "need_criterion_links": [],
            "role_criterion_links": [], "value_propositions": [],
            "claims": [], "metrics": [], "evidence_links": [],
            "role_conflicts": [], "change_log": [],
        })
    elif filename == "delivery-plan.json":
        base.update({
            "delivery_roles": [], "actions": [], "resource_envelopes": [],
            "customer_dependencies": [], "acceptance_contracts": [],
            "change_log": [],
        })
    elif filename == "strategy.json":
        base.update({
            "title": "", "depth_mode": "standard",
            "narrative": {"mode": "logic", "rationale": "", "through_line": ""},
            "decision_map": {"destination": "", "not_yet_specified": [], "out_of_scope": []},
            "open_questions": [], "decision_jobs": [], "sections": [],
            "change_log": [],
        })
    elif filename == "intel-pool.json":
        base.update({"evidence": [], "gaps": [], "research_manifest": {}, "change_log": []})
    return base


def _ensure_layout(state_dir):
    os.makedirs(state_dir, exist_ok=True)
    for relative in (
        "derived/briefs/sections", "derived/briefs/redteam",
        "derived/realization", "derived/manifests", "proposals/changes",
        "proposals/diagnostics", "sections",
    ):
        os.makedirs(os.path.join(state_dir, relative), exist_ok=True)


def init_state(state_dir, mode="standard", lang="zh", source_manifest=None,
               overwrite=False):
    """Create an empty v3 run. Existing canonical state is never overwritten."""
    _ensure_layout(state_dir)
    existing = [name for name in CANONICAL_FILES if os.path.exists(os.path.join(state_dir, name))]
    if existing and not overwrite:
        return {"passed": False, "issues": ["canonical state already exists: " + ", ".join(existing)]}

    if source_manifest:
        source = copy.deepcopy(source_manifest)
        source.setdefault("schema_version", SCHEMA_VERSIONS["source-manifest.json"])
    else:
        source = {"schema_version": SCHEMA_VERSIONS["source-manifest.json"], "sources": []}
    source.setdefault("revision", 1)
    try:
        source = _seal_source_manifest(source, state_dir)
    except ValueError as exc:
        return {"passed": False, "issues": [str(exc)]}

    for filename in CANONICAL_FILES:
        _write_json_atomic(os.path.join(state_dir, filename), _default_document(filename))
    _write_json_atomic(os.path.join(state_dir, "source-manifest.json"), source)

    run = {
        "schema_version": SCHEMA_VERSIONS["run-manifest.json"],
        "revision": 1,
        "engine": ENGINE,
        "engine_version": ENGINE_VERSION,
        "fallback_policy": "explicit",
        "mode": mode,
        "lang": lang,
        "capabilities": [
            "customer_value", "delivery_plan", "task2_5", "compiled_context",
            "realization", "requirement_realization", "safe_projection",
            "scoped_authority", "customer_fit", "last_good",
        ],
        "policy_version": POLICY_VERSION,
    }
    _write_json_atomic(os.path.join(state_dir, "run-manifest.json"), run)
    return {"passed": True, "issues": [], "state_dir": os.path.abspath(state_dir), "engine": ENGINE}


def _stable_id(prefix, seed, used):
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:10].upper()
    candidate = "%s-%s" % (prefix, digest)
    serial = 2
    while candidate in used:
        candidate = "%s-%s-%s" % (prefix, digest, serial)
        serial += 1
    used.add(candidate)
    return candidate


def _legacy_evidence(legacy, used):
    records = []
    topics = legacy if isinstance(legacy, list) else _as_list((legacy or {}).get("topics"))
    for topic_index, topic in enumerate(topics):
        if not isinstance(topic, dict):
            continue
        topic_name = topic.get("topic") or "legacy-topic-%s" % (topic_index + 1)
        for index, fact in enumerate(_as_list(topic.get("facts"))):
            if not isinstance(fact, dict):
                continue
            seed = "fact|%s|%s|%s" % (topic_name, fact.get("fact", ""), fact.get("url", ""))
            records.append({
                "id": _stable_id("EV", seed, used),
                "kind": "public_fact",
                "title": fact.get("title") or fact.get("fact") or "旧情报事实",
                "content": fact.get("fact") or "",
                "source": fact.get("src") or "",
                "url": fact.get("url") or "",
                "observed_at": str(fact.get("yr") or ""),
                "visibility": "public" if fact.get("url") else "unknown",
                "quality": fact.get("conf") or "unknown",
                "status": "active",
                "allowed_uses": ["benchmark"],
                "provenance": {"adapter": "legacy-v2.1", "topic": topic_name, "index": index},
            })
        for index, case in enumerate(_as_list(topic.get("cases"))):
            if not isinstance(case, dict):
                continue
            seed = "case|%s|%s|%s" % (topic_name, case.get("name", ""), case.get("url", ""))
            from_material = bool(case.get("from_material"))
            records.append({
                "id": _stable_id("EV", seed, used),
                "kind": "case_evidence_candidate",
                "title": case.get("name") or "旧案例",
                "content": case.get("what") or case.get("why_relevant") or "",
                "result": case.get("result") or "",
                "source": case.get("who") or case.get("path") or "",
                "url": case.get("url") or "",
                "visibility": "unknown" if from_material else ("public" if case.get("url") else "unknown"),
                "quality": "asserted_from_text" if from_material else "unknown",
                "status": "candidate",
                "allowed_uses": ["matching"] if from_material else ["benchmark"],
                "provenance": {"adapter": "legacy-v2.1", "topic": topic_name, "index": index},
            })
        for index, insight in enumerate(_as_list(topic.get("insights"))):
            text = insight if isinstance(insight, str) else _canonical_json(insight)
            seed = "insight|%s|%s" % (topic_name, text)
            records.append({
                "id": _stable_id("EV", seed, used),
                "kind": "legacy_insight_candidate",
                "title": "旧情报洞察",
                "content": text,
                "visibility": "internal",
                "quality": "unknown",
                "status": "candidate",
                "allowed_uses": ["matching"],
                "provenance": {"adapter": "legacy-v2.1", "topic": topic_name, "index": index},
            })
    return records


def _migrate_legacy_documents(source_dir):
    used = set()
    mapping = {"schema_version": "legacy-to-v3-map/v1", "source_dir": os.path.abspath(source_dir), "entities": []}

    def read_or_default(name):
        path = os.path.join(source_dir, name)
        return _read_json(path) if os.path.exists(path) else None

    old_req = read_or_default("requirements.json")
    req = copy.deepcopy(old_req) if isinstance(old_req, dict) else _default_document("requirements.json")
    req["schema_version"] = SCHEMA_VERSIONS["requirements.json"]
    req["revision"] = 1
    req.setdefault("mandatory", [])
    req.setdefault("scoring", [])
    req.setdefault("deliverables", [])
    for collection in ("mandatory", "scoring", "deliverables"):
        normalized = []
        for index, raw_item in enumerate(_as_list(req.get(collection))):
            item = raw_item if isinstance(raw_item, dict) else {
                "item": str(raw_item), "provenance": {"adapter": "legacy-v2.1"},
            }
            old_id = item.get("id")
            if not old_id:
                item["id"] = _stable_id("REQ", "%s|%s|%s" % (collection, index, item.get("item", "")), used)
            else:
                if old_id in used:
                    item["id"] = _stable_id("REQ", "%s|%s|%s" % (collection, index, old_id), used)
                else:
                    used.add(old_id)
            mapping["entities"].append({"legacy": old_id or "%s[%s]" % (collection, index), "v3": item["id"]})
            normalized.append(item)
        req[collection] = normalized

    old_strategy = read_or_default("strategy.json")
    strategy = copy.deepcopy(old_strategy) if isinstance(old_strategy, dict) else _default_document("strategy.json")
    strategy["schema_version"] = SCHEMA_VERSIONS["strategy.json"]
    strategy["revision"] = 1
    strategy.setdefault("decision_jobs", [])
    strategy.setdefault("sections", [])
    strategy.setdefault("decision_map", {"destination": "", "not_yet_specified": [], "out_of_scope": []})
    strategy.setdefault("open_questions", [])
    strategy.setdefault("change_log", [])
    for index, decision in enumerate(_as_list(strategy.get("open_questions"))):
        if not isinstance(decision, dict):
            continue
        gate_ref = decision.get("id") or decision.get("ref")
        if not gate_ref:
            gate_ref = _stable_id(
                "GATE", "legacy-gate|%s|%s" % (
                    index, decision.get("title") or decision.get("q") or "decision"), used)
            decision["id"] = gate_ref
            mapping["entities"].append({
                "legacy": "strategy.open_questions[%s]" % index,
                "v3": gate_ref,
            })
        elif gate_ref in used:
            decision["id"] = _stable_id(
                "GATE", "legacy-gate|%s|%s" % (index, gate_ref), used)
        else:
            used.add(gate_ref)
        decision.setdefault("affected_refs", [])
    for index, section in enumerate(_as_list(strategy.get("sections"))):
        if not isinstance(section, dict):
            continue
        section.setdefault("id", "CH-%02d" % (section.get("n") or index + 1))
        section.setdefault("execution_model", "legacy_text")
        used.add(section["id"])

    cv = _default_document("customer-value.json")
    buyer_insight = strategy.get("buyer_insight")
    legacy_role_ref = None
    legacy_need_ref = None
    if _nonempty(buyer_insight):
        legacy_role_ref = _stable_id("ROLE", "legacy-buyer-role", used)
        legacy_need_ref = _stable_id("NEED", "legacy|" + buyer_insight, used)
        cv["roles"].append({
            "id": legacy_role_ref,
            "name": "采购人业务角色（旧数据推断）",
            "archetypes": ["business_owner"],
            "presence": "inferred", "confidence": "low",
            "formal_power": "unknown", "practical_influence": "unknown",
            "delivery_impact": "unknown", "scrutiny_level": "unknown",
            "evidence_refs": [], "provenance": {"adapter": "strategy.buyer_insight"},
        })
        cv["needs"].append({
            "id": legacy_need_ref, "name": "旧甲方洞察待核验", "statement": buyer_insight,
            "assertion_mode": "inferred", "source_visibility": "internal",
            "status": "candidate", "evidence_quality": "unknown",
            "inference_confidence": "low", "publication_status": "internal_only",
            "provenance": {"adapter": "strategy.buyer_insight"},
        })
        cv["role_need_links"].append({
            "id": _stable_id("RN", legacy_role_ref + legacy_need_ref, used),
            "role_ref": legacy_role_ref, "need_ref": legacy_need_ref,
            "priority_band": "unknown", "confidence": "low",
            "requiredness": "exploratory", "criterion_refs": [],
        })

    for index, diff in enumerate(_as_list(strategy.get("differentiators"))):
        if isinstance(diff, str):
            point = diff
            raw = {"point": diff}
        elif isinstance(diff, dict):
            point = diff.get("point") or diff.get("value") or "旧差异化候选"
            raw = diff
        else:
            continue
        vp_id = _stable_id("VP", "legacy-diff|%s|%s" % (index, point), used)
        cv["value_propositions"].append({
            "id": vp_id, "name": point, "value_mechanism": raw.get("how") or raw.get("why_wow") or "",
            "expected_change": raw.get("value") or raw.get("why_wow") or "",
            "value_lens": "outcome", "status": "candidate", "portfolio_role": None,
            "role_refs": [legacy_role_ref] if legacy_role_ref else [],
            "need_refs": [legacy_need_ref] if legacy_need_ref else [],
            "criterion_refs": [], "evidence_link_refs": [], "action_refs": [],
            "assessment": {"evidence": "unknown", "feasibility": "unknown", "risk": "unknown"},
            "provenance": {"adapter": "strategy.differentiators[%s]" % index},
        })
        mapping["entities"].append({"legacy": "strategy.differentiators[%s]" % index, "v3": vp_id})

    old_intel = read_or_default("intel-pool.json")
    if old_intel is None:
        old_intel = read_or_default("intel.json")
    intel = _default_document("intel-pool.json")
    intel["evidence"] = _legacy_evidence(old_intel or [], used)
    if old_intel is not None:
        intel["extensions"] = {"legacy_topics": old_intel}

    delivery = _default_document("delivery-plan.json")
    delivery["extensions"] = {"execution_model": "legacy_text", "migration_confidence": "inferred"}
    return {
        "requirements.json": req,
        "customer-value.json": cv,
        "delivery-plan.json": delivery,
        "strategy.json": strategy,
        "intel-pool.json": intel,
    }, mapping


def migrate_state(source_dir, output_dir, mode="standard", lang="zh"):
    """Non-destructively adapt a legacy run into a new v3 state directory."""
    source_dir = os.path.abspath(source_dir)
    output_dir = os.path.abspath(output_dir)
    if source_dir == output_dir:
        return {"passed": False, "issues": ["migration output must differ from the legacy source"]}
    existing_authorities = [
        filename for filename in CANONICAL_FILES + (
            "source-manifest.json", "run-manifest.json", "legacy-to-v3-map.json")
        if os.path.exists(os.path.join(output_dir, filename))
    ]
    if existing_authorities:
        return {"passed": False, "issues": [
            "migration output already contains state: " + ", ".join(existing_authorities)
        ]}

    parent = os.path.dirname(output_dir)
    os.makedirs(parent, exist_ok=True)
    staging = tempfile.mkdtemp(prefix=".proposal-v3-migrate-", dir=parent)
    try:
        documents, mapping = _migrate_legacy_documents(source_dir)
        _ensure_layout(staging)
        for filename, document in documents.items():
            _write_json_atomic(os.path.join(staging, filename), document)
        source_manifest = {
            "schema_version": SCHEMA_VERSIONS["source-manifest.json"],
            "revision": 1,
            "sources": [],
            "migration": {"from": "legacy-v2.1", "source_dir": source_dir, "non_destructive": True},
        }
        for filename in ("requirements.json", "strategy.json", "intel-pool.json", "intel.json"):
            path = os.path.join(source_dir, filename)
            if os.path.isfile(path):
                source_manifest["sources"].append({
                    "id": "SRC-LEGACY-" + re.sub(r"[^A-Za-z0-9]", "-", filename).upper(),
                    "path": path, "kind": "legacy_state", "visibility": "internal", "hash": file_hash(path),
                })
        _write_json_atomic(os.path.join(staging, "source-manifest.json"), source_manifest)
        run = {
            "schema_version": SCHEMA_VERSIONS["run-manifest.json"], "revision": 1,
            "engine": ENGINE, "engine_version": ENGINE_VERSION,
            "fallback_policy": "explicit", "mode": mode, "lang": lang,
            "capabilities": [
                "customer_value", "delivery_plan", "task2_5", "compiled_context",
                "realization", "requirement_realization", "safe_projection",
                "scoped_authority", "customer_fit", "legacy_adapter"],
            "policy_version": POLICY_VERSION,
            "migration_status": "needs_v3_selection",
        }
        _write_json_atomic(os.path.join(staging, "run-manifest.json"), run)
        _write_json_atomic(os.path.join(staging, "legacy-to-v3-map.json"), mapping)
        checked = check_canonical(staging, stage="draft")
        if not checked["passed"]:
            return {"passed": False, "issues": checked["issues"], "diagnostics": checked.get("diagnostics", [])}
        _ensure_layout(output_dir)
        installed = []
        try:
            for filename in CANONICAL_FILES + (
                    "source-manifest.json", "run-manifest.json", "legacy-to-v3-map.json"):
                os.replace(os.path.join(staging, filename), os.path.join(output_dir, filename))
                installed.append(filename)
        except Exception:
            for filename in installed:
                try:
                    os.unlink(os.path.join(output_dir, filename))
                except OSError:
                    pass
            raise
        return {
            "passed": True, "issues": [], "state_dir": output_dir,
            "mapping": os.path.join(output_dir, "legacy-to-v3-map.json"),
            "source_unchanged": True, "next_stage": "task2.5",
        }
    finally:
        if staging and os.path.exists(staging):
            shutil.rmtree(staging, ignore_errors=True)


def bootstrap_state(state_dir, proposal_path, mode="standard", lang="zh"):
    """Atomically create canonical state from a Task 1 bootstrap proposal."""
    existing_authorities = [
        filename for filename in CANONICAL_FILES + ("source-manifest.json", "run-manifest.json")
        if os.path.exists(os.path.join(state_dir, filename))
    ]
    if existing_authorities:
        return {"passed": False, "issues": [
            "bootstrap target already contains state: " + ", ".join(existing_authorities)
        ]}
    proposal = _read_json(proposal_path)
    documents = proposal.get("canonical") if isinstance(proposal, dict) else None
    if not isinstance(documents, dict):
        return {"passed": False, "issues": ["bootstrap proposal must contain canonical object"]}
    missing = [name for name in CANONICAL_FILES if name not in documents]
    if missing:
        return {"passed": False, "issues": ["bootstrap missing: " + ", ".join(missing)]}

    parent = os.path.dirname(os.path.abspath(state_dir))
    os.makedirs(parent, exist_ok=True)
    staging = tempfile.mkdtemp(prefix=".proposal-v3-bootstrap-", dir=parent)
    try:
        _ensure_layout(staging)
        for filename in CANONICAL_FILES:
            document = copy.deepcopy(documents[filename])
            document.setdefault("schema_version", SCHEMA_VERSIONS[filename])
            document.setdefault("revision", 1)
            _write_json_atomic(os.path.join(staging, filename), document)
        source_manifest = proposal.get("source_manifest") or {
            "schema_version": SCHEMA_VERSIONS["source-manifest.json"], "revision": 1, "sources": []
        }
        try:
            source_manifest = _seal_source_manifest(source_manifest, state_dir)
        except ValueError as exc:
            return {"passed": False, "issues": [str(exc)]}
        source_manifest.setdefault("schema_version", SCHEMA_VERSIONS["source-manifest.json"])
        source_manifest.setdefault("revision", 1)
        _write_json_atomic(os.path.join(staging, "source-manifest.json"), source_manifest)
        run = proposal.get("run_manifest") or {}
        run.update({
            "schema_version": SCHEMA_VERSIONS["run-manifest.json"],
            "engine": ENGINE, "engine_version": ENGINE_VERSION,
            "fallback_policy": "explicit", "mode": mode, "lang": lang,
            "policy_version": POLICY_VERSION,
        })
        run.setdefault("revision", 1)
        run.setdefault("capabilities", [
            "customer_value", "delivery_plan", "task2_5", "compiled_context",
            "realization", "requirement_realization", "safe_projection",
            "scoped_authority", "customer_fit"])
        _write_json_atomic(os.path.join(staging, "run-manifest.json"), run)
        checked = check_canonical(staging, stage="draft")
        if not checked["passed"]:
            return {"passed": False, "issues": checked["issues"], "diagnostics": checked.get("diagnostics", [])}
        _ensure_layout(state_dir)
        installed = []
        try:
            for filename in CANONICAL_FILES + ("source-manifest.json", "run-manifest.json"):
                os.replace(os.path.join(staging, filename), os.path.join(state_dir, filename))
                installed.append(filename)
        except Exception:
            for filename in installed:
                try:
                    os.unlink(os.path.join(state_dir, filename))
                except OSError:
                    pass
            raise
        return {"passed": True, "issues": [], "state_dir": os.path.abspath(state_dir)}
    finally:
        if staging and os.path.exists(staging):
            shutil.rmtree(staging, ignore_errors=True)


def load_state(state_dir):
    documents = {}
    issues = []
    for filename in CANONICAL_FILES:
        path = os.path.join(state_dir, filename)
        if not os.path.exists(path):
            issues.append("missing canonical file: %s" % filename)
            continue
        try:
            documents[filename] = _read_json(path)
        except Exception as exc:
            issues.append("invalid %s: %s" % (filename, exc))
    return documents, issues


def _diagnostic(rule_id, kind, severity, observed, expected, refs=None,
                blocks=None, owner=None, repair=None, confidence="high",
                tags=None):
    refs = [str(ref) for ref in (refs or []) if ref not in (None, "")]
    return {
        "rule_id": rule_id,
        "kind": kind,
        "severity": severity,
        "blocks": blocks or [],
        "subject_refs": refs,
        "root_cause_key": "%s:%s" % (rule_id, ",".join(sorted(refs))),
        "observed": observed,
        "expected": expected,
        "confidence": confidence,
        "owner": owner,
        "repair_options": [repair] if repair else [],
        "secondary_tags": tags or [],
    }


def _build_registry(documents, diagnostics):
    registry = {}
    locations = {}
    for filename, collections in ENTITY_COLLECTIONS.items():
        document = documents.get(filename) or {}
        for collection in collections:
            raw = document.get(collection, [])
            if not isinstance(raw, list):
                diagnostics.append(_diagnostic(
                    "schema.collection", "schema", "fatal",
                    "%s.%s is %s" % (filename, collection, type(raw).__name__),
                    "array", blocks=["compile"], owner=filename,
                ))
                continue
            for index, entity in enumerate(raw):
                if not isinstance(entity, dict):
                    diagnostics.append(_diagnostic(
                        "schema.entity", "schema", "fatal",
                        "%s.%s[%s] is not an object" % (filename, collection, index),
                        "object with immutable id", blocks=["compile"], owner=filename,
                    ))
                    continue
                ref = _entity_id(entity)
                if not _nonempty(ref):
                    diagnostics.append(_diagnostic(
                        "schema.id", "orphan", "fatal",
                        "%s.%s[%s] has no id" % (filename, collection, index),
                        "non-empty stable id", blocks=["compile"], owner=filename,
                    ))
                    continue
                if ref in registry:
                    diagnostics.append(_diagnostic(
                        "schema.duplicate_id", "contradictory", "fatal",
                        "duplicate id %s at %s and %s" % (ref, locations[ref], "%s.%s[%s]" % (filename, collection, index)),
                        "globally unique entity id", refs=[ref], blocks=["compile"], owner=filename,
                    ))
                    continue
                registry[ref] = {
                    "type": COLLECTION_TYPES[collection], "collection": collection,
                    "file": filename, "entity": entity,
                }
                locations[ref] = "%s.%s[%s]" % (filename, collection, index)
    return registry


def _expect_ref(registry, source_ref, target_ref, allowed_types, diagnostics,
                field, stage="draft"):
    if not _nonempty(target_ref):
        diagnostics.append(_diagnostic(
            "ref.empty", "orphan", "fatal", "%s.%s has empty ref" % (source_ref, field),
            "existing typed reference", refs=[source_ref], blocks=["compile"],
        ))
        return False
    target = registry.get(target_ref)
    if not target:
        diagnostics.append(_diagnostic(
            "ref.dangling", "orphan", "fatal", "%s.%s -> %s is missing" % (source_ref, field, target_ref),
            "existing typed reference", refs=[source_ref, target_ref], blocks=["compile"],
        ))
        return False
    if target["type"] not in allowed_types:
        diagnostics.append(_diagnostic(
            "ref.type", "contradictory", "fatal",
            "%s.%s -> %s has type %s" % (source_ref, field, target_ref, target["type"]),
            "one of %s" % sorted(allowed_types), refs=[source_ref, target_ref], blocks=["compile"],
        ))
        return False
    return True


def _validate_schema(documents, diagnostics):
    for filename in CANONICAL_FILES:
        document = documents.get(filename)
        if not isinstance(document, dict):
            continue
        if document.get("schema_version") != SCHEMA_VERSIONS[filename]:
            diagnostics.append(_diagnostic(
                "schema.version", "schema", "fatal",
                "%s schema_version=%r" % (filename, document.get("schema_version")),
                SCHEMA_VERSIONS[filename], blocks=["compile"], owner=filename,
            ))
        revision = document.get("revision")
        if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
            diagnostics.append(_diagnostic(
                "schema.revision", "schema", "fatal",
                "%s revision=%r" % (filename, revision),
                "positive integer", blocks=["compile"], owner=filename,
            ))


def _validate_manifests(state_dir, documents, diagnostics):
    source_path = os.path.join(state_dir, "source-manifest.json")
    run_path = os.path.join(state_dir, "run-manifest.json")
    if not os.path.isfile(source_path):
        diagnostics.append(_diagnostic(
            "manifest.source_missing", "schema", "fatal",
            "source-manifest.json is missing", "source-manifest/v1",
            blocks=["compile"], owner="main",
        ))
        source = {}
    else:
        try:
            source = _read_json(source_path)
        except Exception as exc:
            diagnostics.append(_diagnostic(
                "manifest.source_parse", "schema", "fatal", str(exc),
                "valid source-manifest/v1", blocks=["compile"], owner="main",
            ))
            source = {}
    if source and source.get("schema_version") != SCHEMA_VERSIONS["source-manifest.json"]:
        diagnostics.append(_diagnostic(
            "manifest.source_version", "schema", "fatal",
            "source manifest version=%r" % source.get("schema_version"),
            SCHEMA_VERSIONS["source-manifest.json"], blocks=["compile"], owner="main",
        ))
    if source and (not isinstance(source.get("revision"), int)
                   or isinstance(source.get("revision"), bool)
                   or source.get("revision") < 1):
        diagnostics.append(_diagnostic(
            "manifest.source_revision", "schema", "fatal",
            "source manifest revision=%r" % source.get("revision"),
            "positive integer", blocks=["compile"], owner="main"))
    source_ids = set()
    for index, item in enumerate(_as_list(source.get("sources"))):
        if not isinstance(item, dict):
            diagnostics.append(_diagnostic(
                "manifest.source_entity", "schema", "fatal",
                "sources[%s] is not object" % index, "source object",
                blocks=["compile"], owner="main",
            ))
            continue
        ref = item.get("id")
        if not _nonempty(ref):
            diagnostics.append(_diagnostic(
                "manifest.source_id", "orphan", "fatal",
                "sources[%s] has no stable id" % index, "unique source id",
                blocks=["compile"], owner="main",
            ))
            continue
        if ref in source_ids:
            diagnostics.append(_diagnostic(
                "manifest.source_duplicate", "contradictory", "fatal",
                "duplicate source id %s" % ref, "unique source id", [ref],
                ["compile"], "main",
            ))
        source_ids.add(ref)
        if not re.match(r"^sha256:[0-9a-f]{64}$", str(item.get("hash") or "")):
            diagnostics.append(_diagnostic(
                "manifest.source_hash", "unsupported", "fatal",
                "%s has no sealed sha256 hash" % ref,
                "source identity hash computed by the tool", [ref],
                ["compile"], "main",
            ))
        source_item_path = item.get("path")
        if source_item_path:
            resolved = (source_item_path if os.path.isabs(source_item_path)
                        else os.path.join(state_dir, source_item_path))
            if os.path.exists(resolved):
                try:
                    actual_hash = path_hash(resolved)
                except OSError as exc:
                    actual_hash = None
                    diagnostics.append(_diagnostic(
                        "manifest.source_unreadable", "unsupported", "fatal",
                        "%s cannot be read: %s" % (ref, exc),
                        "readable sealed source", [ref], ["compile"], "main"))
                if actual_hash and item.get("hash") != actual_hash:
                    diagnostics.append(_diagnostic(
                        "manifest.source_changed", "contradictory", "fatal",
                        "%s content no longer matches its sealed hash" % ref,
                        "immutable source identity or an explicit new source revision",
                        [ref], ["compile"], "main",
                        "re-bootstrap/revise the source manifest; never silently accept drift"))
        if not item.get("visibility"):
            diagnostics.append(_diagnostic(
                "manifest.source_visibility", "schema", "fatal",
                "%s has no visibility" % ref, "explicit source visibility",
                [ref], ["compile"], "task1",
            ))

    if not os.path.isfile(run_path):
        diagnostics.append(_diagnostic(
            "manifest.run_missing", "schema", "fatal", "run-manifest.json is missing",
            "run-manifest/v1 with engine=v3", blocks=["compile"], owner="main",
        ))
    else:
        try:
            run = _read_json(run_path)
        except Exception as exc:
            diagnostics.append(_diagnostic(
                "manifest.run_parse", "schema", "fatal", str(exc),
                "valid run-manifest/v1", blocks=["compile"], owner="main",
            ))
            run = {}
        if run and run.get("schema_version") != SCHEMA_VERSIONS["run-manifest.json"]:
            diagnostics.append(_diagnostic(
                "manifest.run_version", "schema", "fatal",
                "run manifest version=%r" % run.get("schema_version"),
                SCHEMA_VERSIONS["run-manifest.json"], blocks=["compile"], owner="main",
            ))
        if run and (not isinstance(run.get("revision"), int)
                    or isinstance(run.get("revision"), bool)
                    or run.get("revision") < 1):
            diagnostics.append(_diagnostic(
                "manifest.run_revision", "schema", "fatal",
                "run manifest revision=%r" % run.get("revision"),
                "positive integer", blocks=["compile"], owner="main"))
        if run and run.get("engine") != ENGINE:
            diagnostics.append(_diagnostic(
                "manifest.engine", "contradictory", "fatal",
                "run engine=%r" % run.get("engine"), "frozen v3 engine",
                blocks=["compile"], owner="main",
            ))
        if run and run.get("engine_version") != ENGINE_VERSION:
            diagnostics.append(_diagnostic(
                "manifest.engine_version", "contradictory", "fatal",
                "run engine_version=%r" % run.get("engine_version"), ENGINE_VERSION,
                blocks=["compile"], owner="main"))
        if run and run.get("policy_version") != POLICY_VERSION:
            diagnostics.append(_diagnostic(
                "manifest.policy_version", "contradictory", "fatal",
                "run policy_version=%r" % run.get("policy_version"), POLICY_VERSION,
                blocks=["compile"], owner="main",
                repair="migrate the run explicitly; do not mix policy snapshots"))
        if run and run.get("fallback_policy") != "explicit":
            diagnostics.append(_diagnostic(
                "manifest.fallback", "overcommitted", "fatal",
                "fallback_policy=%r" % run.get("fallback_policy"),
                "explicit", blocks=["compile"], owner="main",
            ))

    for evidence in _as_list((documents.get("intel-pool.json") or {}).get("evidence")):
        if not isinstance(evidence, dict) or not evidence.get("source_ref"):
            continue
        if evidence.get("source_ref") not in source_ids:
            diagnostics.append(_diagnostic(
                "manifest.evidence_source", "orphan", "fatal",
                "%s source_ref=%s is missing" % (evidence.get("id"), evidence.get("source_ref")),
                "source-manifest entry", [evidence.get("id"), evidence.get("source_ref")],
                ["compile"], "task1",
            ))


def _validate_relations(documents, registry, diagnostics):
    cv = documents.get("customer-value.json") or {}
    strategy = documents.get("strategy.json") or {}
    delivery = documents.get("delivery-plan.json") or {}

    relation_specs = (
        ("role_need_links", "role_ref", {"customer_role"}, "need_ref", {"customer_need"}),
        ("need_criterion_links", "need_ref", {"customer_need"}, "criterion_ref", {"decision_criterion"}),
        ("role_criterion_links", "role_ref", {"customer_role"}, "criterion_ref", {"decision_criterion"}),
    )
    all_entity_types = set(COLLECTION_TYPES.values())
    for collection in ("mandatory", "scoring", "deliverables"):
        for requirement in _as_list((documents.get("requirements.json") or {}).get(collection)):
            if not isinstance(requirement, dict) or not _entity_id(requirement):
                continue
            ref = _entity_id(requirement)
            if requirement.get("source_ref"):
                _expect_ref(registry, ref, requirement.get("source_ref"), {"evidence"}, diagnostics, "source_ref")
            for target_ref in _ref_list(requirement, "authorizes_refs"):
                _expect_ref(registry, ref, target_ref, all_entity_types, diagnostics, "authorizes_refs")
    for collection, left, left_types, right, right_types in relation_specs:
        for index, link in enumerate(_as_list(cv.get(collection))):
            if not isinstance(link, dict):
                diagnostics.append(_diagnostic(
                    "schema.relation", "schema", "fatal", "%s[%s] is not object" % (collection, index),
                    "typed relation object", blocks=["compile"], owner="customer-value.json",
                ))
                continue
            source = link.get("id") or "%s[%s]" % (collection, index)
            _expect_ref(registry, source, link.get(left), left_types, diagnostics, left)
            _expect_ref(registry, source, link.get(right), right_types, diagnostics, right)
            for criterion_ref in _ref_list(link, "criterion_refs"):
                _expect_ref(registry, source, criterion_ref, {"decision_criterion"}, diagnostics, "criterion_refs")

    for collection in ENTITY_COLLECTIONS["customer-value.json"]:
        for entity in _as_list(cv.get(collection)):
            if not isinstance(entity, dict) or not _entity_id(entity):
                continue
            ref = _entity_id(entity)
            specs = {
                "role_refs": {"customer_role"}, "need_refs": {"customer_need"},
                "criterion_refs": {"decision_criterion"}, "value_proposition_refs": {"value_proposition"},
                "claim_refs": {"claim"}, "metric_refs": {"metric"},
                "evidence_link_refs": {"evidence_link"}, "action_refs": {"delivery_action"},
                "evidence_refs": {"evidence"}, "capability_evidence_refs": {"evidence"},
                "owner_ref": {"delivery_role"},
                "acceptance_ref": {"acceptance_contract"},
                "superseded_by": {"customer_need", "value_proposition", "claim"},
            }
            for field, allowed in specs.items():
                for target_ref in _ref_list(entity, field):
                    _expect_ref(registry, ref, target_ref, allowed, diagnostics, field)
            if collection == "evidence_links":
                _expect_ref(registry, ref, entity.get("evidence_ref"), {"evidence"}, diagnostics, "evidence_ref")
                _expect_ref(registry, ref, entity.get("target_ref"), {
                    "customer_need", "decision_criterion", "value_proposition", "claim",
                }, diagnostics, "target_ref")

    for collection in ENTITY_COLLECTIONS["delivery-plan.json"]:
        for entity in _as_list(delivery.get(collection)):
            if not isinstance(entity, dict) or not _entity_id(entity):
                continue
            ref = _entity_id(entity)
            specs = {
                "accountable_role_ref": {"delivery_role"},
                "responsible_role_refs": {"delivery_role"},
                "supporting_role_refs": {"delivery_role"},
                "requirement_refs": {"requirement"},
                "value_proposition_refs": {"value_proposition"},
                "claim_refs": {"claim"}, "resource_refs": {"resource_envelope"},
                "dependency_refs": {"customer_dependency"},
                "acceptance_refs": {"acceptance_contract"},
                "metric_refs": {"metric"}, "customer_role_refs": {"customer_role"},
                "approver_role_refs": {"customer_role"},
                "predecessor_refs": {"delivery_action"},
            }
            for field, allowed in specs.items():
                for target_ref in _ref_list(entity, field):
                    _expect_ref(registry, ref, target_ref, allowed, diagnostics, field)
            for demand in _as_list(entity.get("resource_demands")):
                if isinstance(demand, dict):
                    _expect_ref(registry, ref, demand.get("resource_ref"), {"resource_envelope"}, diagnostics, "resource_demands.resource_ref")

    for job in _as_list(strategy.get("decision_jobs")):
        if not isinstance(job, dict) or not _entity_id(job):
            continue
        ref = _entity_id(job)
        specs = {
            "section_ref": {"section"}, "role_refs": {"customer_role"},
            "criterion_refs": {"decision_criterion"}, "value_proposition_refs": {"value_proposition"},
            "claim_refs": {"claim"}, "action_refs": {"delivery_action"},
            "predecessor_refs": {"decision_job"},
        }
        for field, allowed in specs.items():
            for target_ref in _ref_list(job, field):
                _expect_ref(registry, ref, target_ref, allowed, diagnostics, field)

    for section in _as_list(strategy.get("sections")):
        if not isinstance(section, dict) or not _entity_id(section):
            continue
        ref = _entity_id(section)
        for target_ref in _ref_list(section, "addresses"):
            _expect_ref(registry, ref, target_ref, {"requirement"}, diagnostics, "addresses")
        for field in ("primary_decision_job_ref", "secondary_decision_job_ref"):
            for target_ref in _ref_list(section, field):
                _expect_ref(registry, ref, target_ref, {"decision_job"}, diagnostics, field)

    for evidence in _as_list((documents.get("intel-pool.json") or {}).get("evidence")):
        if not isinstance(evidence, dict) or not _entity_id(evidence):
            continue
        ref = _entity_id(evidence)
        for target_ref in _ref_list(evidence, "authorizes_refs"):
            _expect_ref(registry, ref, target_ref, all_entity_types, diagnostics, "authorizes_refs")

    for decision in _as_list(strategy.get("open_questions")):
        if not isinstance(decision, dict):
            continue
        ref = decision.get("id") or decision.get("ref") or decision.get("title") or "Gate"
        for target_ref in _ref_list(decision, "affected_refs"):
            _expect_ref(registry, ref, target_ref, all_entity_types, diagnostics, "affected_refs")


def _metric_complete(metric):
    required = ("name", "definition", "unit", "window", "data_source", "frequency", "owner_ref")
    missing = [key for key in required if not metric.get(key)]
    baseline = metric.get("baseline")
    target = metric.get("target")
    if not isinstance(baseline, dict) or baseline.get("value") is None or not baseline.get("source_ref"):
        missing.append("baseline.value/source_ref")
    if target is None or target == "":
        missing.append("target")
    return missing


def _acceptance_complete(contract):
    required = ("subject", "criteria", "method", "records", "correction_window", "authority_ref")
    return [key for key in required if not contract.get(key)]


def _authority_valid(authority_ref, subject_ref, documents, registry,
                     purpose="commitment_authority"):
    """Resolve a commitment authority to a real, appropriately scoped object."""
    if not _nonempty(authority_ref):
        return False, "authority_ref is empty"
    target = registry.get(authority_ref)
    if target and target.get("type") == "requirement":
        requirement = target.get("entity") or {}
        subject = registry.get(subject_ref, {}).get("entity") or {}
        subject_type = registry.get(subject_ref, {}).get("type")
        explicitly_authorized = subject_ref in set(_ref_list(requirement, "authorizes_refs"))
        use_allowed = purpose in _as_list(requirement.get("authority_uses"))
        direct_action_basis = (subject_type == "delivery_action"
                               and authority_ref in _ref_list(subject, "requirement_refs"))
        acceptance_basis = False
        if subject_type == "acceptance_contract":
            for action in _as_list((documents.get("delivery-plan.json") or {}).get("actions")):
                if (isinstance(action, dict)
                        and subject_ref in _ref_list(action, "acceptance_refs")
                        and authority_ref in _ref_list(action, "requirement_refs")):
                    acceptance_basis = True
                    break
        if explicitly_authorized or (use_allowed and (direct_action_basis or acceptance_basis)):
            return True, "scoped tender requirement"
        return False, "Requirement does not explicitly authorize this subject/use"
    if target and target.get("type") == "evidence":
        evidence = target.get("entity") or {}
        if not _evidence_is_current(evidence):
            return False, "authority Evidence is not active/current"
        if evidence.get("quality") not in ("high", "verified"):
            return False, "authority Evidence is not high/verified"
        if not _evidence_allowed_for(evidence, purpose):
            return False, "authority Evidence is not allowed for %s" % purpose
        if purpose == "bidder_capability" and (
                evidence.get("third_party") is True
                or evidence.get("kind") in ("third_party_case", "buyer_case", "industry_case")):
            return False, "third-party Evidence cannot authorize bidder capability"
        linked = any(
            isinstance(link, dict) and link.get("evidence_ref") == authority_ref
            and link.get("target_ref") == subject_ref
            and link.get("relation", "supports") == "supports"
            for link in _as_list((documents.get("customer-value.json") or {}).get("evidence_links"))
        )
        explicitly_authorized = subject_ref in set(_ref_list(evidence, "authorizes_refs"))
        if not (linked or explicitly_authorized):
            return False, "authority Evidence is not linked/scoped to %s" % subject_ref
        return True, "verified Evidence authority"

    strategy = documents.get("strategy.json") or {}
    for decision in _as_list(strategy.get("open_questions")):
        if not isinstance(decision, dict):
            continue
        decision_ref = decision.get("id") or decision.get("ref")
        if decision_ref != authority_ref:
            continue
        if decision.get("status") != "resolved" or decision.get("assumption_risk"):
            return False, "Gate authority is not human-resolved"
        affected = set(_ref_list(decision, "affected_refs"))
        if subject_ref not in affected:
            return False, "Gate authority does not cover %s" % subject_ref
        return True, "resolved Gate authority"
    return False, "authority_ref does not resolve to Requirement, verified Evidence, or resolved Gate"


def _validate_lifecycle(documents, registry, diagnostics, stage):
    cv = documents.get("customer-value.json") or {}
    strategy = documents.get("strategy.json") or {}
    delivery = documents.get("delivery-plan.json") or {}
    needs_by_id = {
        item.get("id"): item for item in _as_list(cv.get("needs"))
        if isinstance(item, dict) and item.get("id")
    }
    criteria_by_id = {
        item.get("id"): item for item in _as_list(cv.get("criteria"))
        if isinstance(item, dict) and item.get("id")
    }
    role_need_links = [
        item for item in _as_list(cv.get("role_need_links"))
        if isinstance(item, dict)
    ]

    gate_ids = set()
    for index, decision in enumerate(_as_list(strategy.get("open_questions"))):
        if not isinstance(decision, dict):
            diagnostics.append(_diagnostic(
                "decision.schema", "schema", "fatal",
                "open_questions[%s] is not an object" % index,
                "typed Gate decision", blocks=["compile"], owner="task1"))
            continue
        gate_ref = decision.get("id") or decision.get("ref")
        if not _nonempty(gate_ref):
            diagnostics.append(_diagnostic(
                "decision.id", "orphan", "blocker",
                "open_questions[%s] has no stable GATE-* id" % index,
                "stable Gate id usable as scoped authority", blocks=["task3", "submission"],
                owner="task1", repair="assign an immutable GATE-* id before resolution"))
        elif gate_ref in gate_ids:
            diagnostics.append(_diagnostic(
                "decision.duplicate_id", "contradictory", "fatal",
                "duplicate Gate id %s" % gate_ref, "globally unique Gate ids",
                [gate_ref], ["compile"], "task1"))
        else:
            gate_ids.add(gate_ref)
        if decision.get("status", "open") not in ("open", "resolved", "assumed"):
            diagnostics.append(_diagnostic(
                "decision.status", "schema", "fatal",
                "%s has invalid status %r" % (gate_ref or index, decision.get("status")),
                "open|resolved|assumed", [gate_ref] if gate_ref else [], ["compile"], "task1"))

    if stage in ("generation", "submission"):
        decision_map = strategy.get("decision_map") or {}
        fog = _as_list(decision_map.get("not_yet_specified"))
        open_decisions = [
            item for item in _as_list(strategy.get("open_questions"))
            if isinstance(item, dict) and item.get("status") == "open"
        ]
        assumed_decisions = [
            item for item in _as_list(strategy.get("open_questions"))
            if isinstance(item, dict) and item.get("status") == "assumed"
        ]
        if open_decisions:
            diagnostics.append(_diagnostic(
                "decision.open", "uncovered", "blocker",
                "%s Gate 1 decisions remain open" % len(open_decisions),
                "decision frontier settled before generation",
                [item.get("title") for item in open_decisions if item.get("title")],
                ["task3", "submission"], "gate1",
                "resolve each human-only decision or use explicit auto assumptions",
            ))
        if fog:
            diagnostics.append(_diagnostic(
                "decision.fog", "uncovered", "blocker",
                "%s not_yet_specified decisions remain" % len(fog),
                "fog promoted to a decision, research gap, or out_of_scope",
                [], ["task3", "submission"], "task1",
                "route every unresolved area before generation",
            ))
        if assumed_decisions:
            diagnostics.append(_diagnostic(
                "decision.assumed", "overcommitted", "blocker",
                "%s decisions use auto assumptions" % len(assumed_decisions),
                "human confirmation before direct submission",
                [item.get("title") for item in assumed_decisions if item.get("title")],
                ["submission"], "gate1",
                "confirm assumptions or keep the output marked draft-only",
            ))

    for need in _as_list(cv.get("needs")):
        if not isinstance(need, dict) or not _entity_id(need):
            continue
        ref = _entity_id(need)
        if need.get("status") not in NEED_STATES:
            diagnostics.append(_diagnostic("need.status", "schema", "fatal", "%s status=%r" % (ref, need.get("status")), sorted(NEED_STATES), [ref], ["compile"], "task1"))
        if need.get("status") == "active" and not _nonempty(need.get("statement")):
            diagnostics.append(_diagnostic("need.statement", "orphan", "blocker", "%s active without statement" % ref, "scoped customer outcome or avoided risk", [ref], ["task3", "submission"], "task1"))

    for vp in _as_list(cv.get("value_propositions")):
        if not isinstance(vp, dict) or not _entity_id(vp):
            continue
        ref = _entity_id(vp)
        status = vp.get("status")
        if status not in VP_STATES:
            diagnostics.append(_diagnostic("vp.status", "schema", "fatal", "%s status=%r" % (ref, status), sorted(VP_STATES), [ref], ["compile"], "task2.5"))
            continue
        if status in ("selected", "publishable"):
            missing = []
            for field in ("role_refs", "need_refs", "criterion_refs"):
                if not _ref_list(vp, field):
                    missing.append(field)
            valid_capability_actions = [
                target_ref for target_ref in _ref_list(vp, "action_refs")
                if registry.get(target_ref, {}).get("entity", {}).get("selection_status") == "selected"
                and registry.get(target_ref, {}).get("entity", {}).get("readiness_status")
                in ("planned", "confirmed")
            ]
            valid_capability_evidence = []
            for evidence_ref in _ref_list(vp, "capability_evidence_refs"):
                evidence = registry.get(evidence_ref, {}).get("entity") or {}
                if (_evidence_is_current(evidence)
                        and evidence.get("quality") in ("high", "verified")
                        and _evidence_allowed_for(evidence, "bidder_capability")
                        and evidence.get("third_party") is not True
                        and evidence.get("kind") not in (
                            "third_party_case", "buyer_case", "industry_case")):
                    valid_capability_evidence.append(evidence_ref)
            valid_capability_authorities = []
            for authority_ref in _ref_list(vp, "authority_refs"):
                authority_ok, _ = _authority_valid(
                    authority_ref, ref, documents, registry, "bidder_capability")
                if authority_ok:
                    valid_capability_authorities.append(authority_ref)
            if not (valid_capability_actions or valid_capability_evidence
                    or valid_capability_authorities):
                missing.append("capability_evidence_refs|action_refs|authority_refs")
            if missing:
                diagnostics.append(_diagnostic(
                    "vp.selected_path", "orphan", "blocker",
                    "%s selected with missing %s" % (ref, ", ".join(missing)),
                    "Role + Need + Criterion + capability boundary", [ref], ["task3", "submission"],
                    "task2.5", "complete or demote this value proposition",
                ))
            for need_ref in _ref_list(vp, "need_refs"):
                need = needs_by_id.get(need_ref) or {}
                publication = need.get("publication_status")
                if publication not in ("public_explicit", "publicly_supportable"):
                    diagnostics.append(_diagnostic(
                        "vp.private_need", "unsupported", "blocker",
                        "%s selects non-public Need %s" % (ref, need_ref),
                        "publicly supportable Need before writing",
                        [ref, need_ref], ["task3", "submission"], "task2",
                        "add independent public support and an approved projection, or demote the VP",
                    ))
                elif publication == "publicly_supportable" and not _nonempty(need.get("approved_projection")):
                    diagnostics.append(_diagnostic(
                        "need.public_projection", "unsupported", "blocker",
                        "%s is publicly supportable but has no approved_projection" % need_ref,
                        "safe wording derived only from public Evidence",
                        [ref, need_ref], ["task3", "submission"], "task1",
                        "compile an approved public projection without private wording",
                    ))
            for criterion_ref in _ref_list(vp, "criterion_refs"):
                criterion = criteria_by_id.get(criterion_ref) or {}
                publication = criterion.get("publication_status")
                if publication not in ("public_explicit", "publicly_supportable"):
                    diagnostics.append(_diagnostic(
                        "vp.private_criterion", "unsupported", "blocker",
                        "%s selects non-public Criterion %s" % (ref, criterion_ref),
                        "publicly supportable decision criterion",
                        [ref, criterion_ref], ["task3", "submission"], "task2",
                        "add a safe public basis or keep the criterion internal",
                    ))
                elif publication == "publicly_supportable" and not _nonempty(criterion.get("approved_projection")):
                    diagnostics.append(_diagnostic(
                        "criterion.public_projection", "unsupported", "blocker",
                        "%s is publicly supportable but has no approved_projection" % criterion_ref,
                        "safe wording derived only from public Evidence",
                        [ref, criterion_ref], ["task3", "submission"], "task2",
                        "compile an approved public projection without private wording",
                    ))

    if stage in ("generation", "submission"):
        selected_vps = [
            item for item in _as_list(cv.get("value_propositions"))
            if isinstance(item, dict) and item.get("status") in ("selected", "publishable")
        ]
        leads = [item for item in selected_vps if item.get("portfolio_role") == "lead"]
        if not leads:
            diagnostics.append(_diagnostic(
                "portfolio.lead_missing", "uncovered", "blocker",
                "selected portfolio has no lead ValueProposition",
                "at least one lead serving a high-priority customer path",
                [item.get("id") for item in selected_vps],
                ["task3", "submission"], "task2.5",
                "select a qualified lead or explicitly stop with competitiveness insufficient",
            ))
        for lead in leads:
            matching_priority = False
            for relation in role_need_links:
                if (relation.get("role_ref") in _ref_list(lead, "role_refs")
                        and relation.get("need_ref") in _ref_list(lead, "need_refs")
                        and (relation.get("requiredness") == "required"
                             or relation.get("priority_band") in ("critical", "high"))):
                    relation_criteria = set(_ref_list(relation, "criterion_refs"))
                    if not relation_criteria or relation_criteria.intersection(_ref_list(lead, "criterion_refs")):
                        matching_priority = True
                        break
            if not matching_priority:
                diagnostics.append(_diagnostic(
                    "portfolio.lead_priority", "orphan", "blocker",
                    "%s lead does not serve a required/high-priority Role×Need×Criterion path" % lead.get("id"),
                    "lead anchored in a high-priority customer decision path",
                    [lead.get("id")], ["task3", "submission"], "task2.5",
                    "choose a meaningful lead or correct the evidence-based priority relation",
                ))

    evidence_by_id = {item.get("id"): item for item in _as_list((documents.get("intel-pool.json") or {}).get("evidence")) if isinstance(item, dict)}
    link_by_id = {item.get("id"): item for item in _as_list(cv.get("evidence_links")) if isinstance(item, dict)}
    metrics = {item.get("id"): item for item in _as_list(cv.get("metrics")) if isinstance(item, dict)}
    actions = {item.get("id"): item for item in _as_list(delivery.get("actions")) if isinstance(item, dict)}
    acceptances = {item.get("id"): item for item in _as_list(delivery.get("acceptance_contracts")) if isinstance(item, dict)}

    for evidence_ref, evidence in evidence_by_id.items():
        allowed_uses = evidence.get("allowed_uses")
        if not isinstance(allowed_uses, list):
            diagnostics.append(_diagnostic(
                "evidence.allowed_uses", "schema", "fatal",
                "%s allowed_uses is not an array" % evidence_ref,
                "explicit evidence-use array", [evidence_ref], ["compile"], "task1"))
        else:
            unknown_uses = sorted(set(
                str(use) for use in allowed_uses
                if not isinstance(use, str) or use not in ALLOWED_EVIDENCE_USES))
            if unknown_uses:
                diagnostics.append(_diagnostic(
                    "evidence.allowed_use_unknown", "schema", "fatal",
                    "%s has unknown allowed_uses %s" % (evidence_ref, unknown_uses),
                    sorted(ALLOWED_EVIDENCE_USES), [evidence_ref], ["compile"], "task1"))
        if ((evidence.get("third_party") is True
             or evidence.get("kind") in ("third_party_case", "buyer_case", "industry_case"))
                and "bidder_capability" in _as_list(allowed_uses)):
            diagnostics.append(_diagnostic(
                "evidence.third_party_capability", "unsupported", "blocker",
                "%s third-party Evidence is authorized for bidder_capability" % evidence_ref,
                "third-party Evidence limited to benchmark/feasibility",
                [evidence_ref], ["task3", "submission"], "task2",
                "remove the invalid use and demote any dependent Claim"))
        if evidence.get("visibility") == "approved_anonymized" and (
                not _nonempty(evidence.get("approved_projection"))
                or not _nonempty(evidence.get("safe_title"))):
            diagnostics.append(_diagnostic(
                "evidence.anonymized_projection", "unsupported", "blocker",
                "%s approved_anonymized Evidence lacks safe_title/approved_projection" % evidence_ref,
                "explicit anonymized title and wording; never raw-content fallback",
                [evidence_ref], ["task3", "submission"], "gate1",
                "approve a genuinely anonymized projection or keep the Evidence internal",
                tags=["private_only"],
            ))
        if evidence.get("visibility") == "approved_anonymized":
            authority_ok, authority_reason = _authority_valid(
                evidence.get("publication_authority_ref"), evidence_ref,
                documents, registry, "anonymized_publication")
            if not authority_ok:
                diagnostics.append(_diagnostic(
                    "evidence.anonymized_authority", "unsupported", "blocker",
                    "%s anonymized publication has invalid authority: %s" % (
                        evidence_ref, authority_reason),
                    "real permission Evidence or resolved Gate scoped to this Evidence",
                    [evidence_ref, evidence.get("publication_authority_ref")],
                    ["task3", "submission"], "gate1",
                    "obtain publication permission or keep the Evidence internal"))
        if evidence.get("visibility") == "named":
            authority_ok, authority_reason = _authority_valid(
                evidence.get("publication_authority_ref"), evidence_ref,
                documents, registry, "named_publication")
            if (not _evidence_allowed_for(evidence, "client_name")
                    or not authority_ok):
                diagnostics.append(_diagnostic(
                    "evidence.named_authority", "unsupported", "blocker",
                    "%s named publication is not authorized: %s" % (
                        evidence_ref, authority_reason),
                    "client_name use plus scoped named-publication authority",
                    [evidence_ref, evidence.get("publication_authority_ref")],
                    ["task3", "submission"], "gate1",
                    "obtain naming permission or use an approved anonymized projection"))

    for link in link_by_id.values():
        if link.get("relation") != "refutes":
            continue
        evidence = evidence_by_id.get(link.get("evidence_ref")) or {}
        if not _evidence_is_current(evidence):
            continue
        target_ref = link.get("target_ref")
        target = registry.get(target_ref, {}).get("entity") or {}
        target_live = (target.get("status") in (
            "active", "qualified", "selected", "publishable", "draft_ready")
            or target.get("selection_status") == "selected")
        if not target_live:
            continue
        strong = (link.get("strength") in ("direct", "strong")
                  and evidence.get("quality") in ("high", "verified")
                  and link.get("confidence", "high") in ("high", "medium"))
        severity = "blocker" if strong else "major"
        diagnostics.append(_diagnostic(
            "evidence.counter", "contradictory", severity,
            "%s has active counter-Evidence %s (%s)" % (
                target_ref, evidence.get("id"), link.get("reason") or "no reason"),
            "counter-Evidence resolved, target contested/demoted, or scoped reconciliation",
            [target_ref, link.get("id"), evidence.get("id")],
            ["task3", "submission"] if severity == "blocker" else [],
            "task2.5", "reconcile the contradiction; do not let supports silently override it"))

    for claim in _as_list(cv.get("claims")):
        if not isinstance(claim, dict) or not _entity_id(claim):
            continue
        ref = _entity_id(claim)
        status = claim.get("status")
        if status not in CLAIM_STATES:
            diagnostics.append(_diagnostic("claim.status", "schema", "fatal", "%s status=%r" % (ref, status), sorted(CLAIM_STATES), [ref], ["compile"], "task2.5"))
        if claim.get("content_kind") not in CONTENT_KINDS:
            diagnostics.append(_diagnostic("claim.content_kind", "schema", "fatal", "%s content_kind=%r" % (ref, claim.get("content_kind")), sorted(CONTENT_KINDS), [ref], ["compile"], "task2.5"))
        if claim.get("epistemic_status") not in EPISTEMIC_STATES:
            diagnostics.append(_diagnostic("claim.epistemic", "schema", "fatal", "%s epistemic_status=%r" % (ref, claim.get("epistemic_status")), sorted(EPISTEMIC_STATES), [ref], ["compile"], "task2.5"))
        if claim.get("commitment_level") not in COMMITMENT_LEVELS:
            diagnostics.append(_diagnostic("claim.commitment", "schema", "fatal", "%s commitment_level=%r" % (ref, claim.get("commitment_level")), sorted(COMMITMENT_LEVELS), [ref], ["compile"], "task2.5"))
        if status != "publishable":
            continue

        vp_refs = _ref_list(claim, "value_proposition_refs")
        selected = [target for target in vp_refs if registry.get(target, {}).get("entity", {}).get("status") in ("selected", "publishable")]
        if not selected:
            diagnostics.append(_diagnostic("claim.vp", "orphan", "blocker", "%s publishable without selected ValueProposition" % ref, "at least one selected ValueProposition", [ref], ["task3", "submission"], "task2.5", "link to a selected VP or withdraw the claim"))

        evidence_link_ids = set(_ref_list(claim, "evidence_link_refs"))
        evidence_link_ids.update(
            link_id for link_id, link in link_by_id.items()
            if link.get("target_ref") == ref
        )
        evidence_links = [link_by_id.get(item) for item in evidence_link_ids]
        evidence_links = [item for item in evidence_links if item and item.get("relation", "supports") == "supports"]
        needs_evidence = claim.get("content_kind") in ("fact", "insight", "target") or claim.get("risk_level") in ("high", "critical")
        if needs_evidence and not evidence_links:
            diagnostics.append(_diagnostic("claim.evidence", "unsupported", "blocker", "%s publishable without supporting EvidenceLink" % ref, "risk-appropriate Evidence", [ref], ["task3", "submission"], "task2", "add relevant, valid Evidence or demote the claim"))
        if needs_evidence and evidence_links:
            safe_support = [
                (link, evidence_by_id.get(link.get("evidence_ref")) or {})
                for link in evidence_links
                if (evidence_by_id.get(link.get("evidence_ref")) or {}).get("visibility")
                in SAFE_PUBLICATION_VISIBILITIES
            ]
            proof_task = _claim_proof_task(claim)
            usable_support = [
                (link, evidence) for link, evidence in safe_support
                if _evidence_support_usable(
                    link, evidence, claim.get("risk_level") or "medium",
                    proof_task)
            ]
            if not safe_support:
                diagnostics.append(_diagnostic("claim.private_only", "unsupported", "blocker", "%s only has private/unknown support" % ref, "public or approved anonymized support", [ref], ["task3", "submission"], "task2", "add a safe public projection or keep the claim internal", tags=["private_only"]))
            elif not usable_support:
                diagnostics.append(_diagnostic(
                    "claim.evidence_quality", "unsupported", "blocker",
                    "%s has no active, sufficiently strong public support" % ref,
                    "current, authorized Evidence with relevant scope, risk-appropriate quality and link strength",
                    [ref] + [link.get("id") for link, _ in safe_support],
                    ["task3", "submission"], "task2",
                    "replace stale/weak Evidence or demote the Claim",
                ))

        if claim.get("epistemic_status") == "assumed":
            diagnostics.append(_diagnostic("claim.assumed", "overcommitted", "blocker", "%s assumed but publishable" % ref, "assumptions remain internal", [ref], ["task3", "submission"], "gate1", "confirm, evidence, or withdraw the claim"))

        measurement_required = bool(claim.get("measurement_required")) or claim.get("content_kind") == "target" or bool(claim.get("quantitative"))
        if measurement_required:
            metric_refs = _ref_list(claim, "metric_refs")
            if not metric_refs:
                diagnostics.append(_diagnostic("claim.metric", "unmeasured", "blocker", "%s requires measurement but has no MetricContract" % ref, "complete MetricContract", [ref], ["task3", "submission"], "task2.5", "add a valid MetricContract or make the claim directional"))
            for metric_ref in metric_refs:
                metric = metrics.get(metric_ref) or {}
                missing = _metric_complete(metric)
                if missing:
                    diagnostics.append(_diagnostic("metric.complete", "unmeasured", "blocker", "%s missing %s" % (metric_ref, ", ".join(missing)), "complete MetricContract", [ref, metric_ref], ["task3", "submission"], "gate1", "complete the measurement and acceptance basis"))
                authority_ok, authority_reason = _authority_valid(
                    metric.get("authority_ref"), metric_ref, documents, registry,
                    "commitment_authority")
                if not authority_ok:
                    diagnostics.append(_diagnostic(
                        "metric.authority", "overcommitted", "blocker",
                        "%s has invalid target authority: %s" % (metric_ref, authority_reason),
                        "tender/verified/resolved authority scoped to the MetricContract",
                        [ref, metric_ref, metric.get("authority_ref")],
                        ["task3", "submission"], "gate1",
                        "confirm the metric basis or make the Claim non-quantitative"))

        if claim.get("commitment_level") == "committed":
            authority_ok, authority_reason = _authority_valid(
                claim.get("authority_ref"), ref, documents, registry,
                "bidder_capability" if _claim_proof_task(claim) == "bidder_capability"
                else "commitment_authority")
            if not authority_ok:
                diagnostics.append(_diagnostic(
                    "claim.authority", "overcommitted", "blocker",
                    "%s committed with invalid authority: %s" % (ref, authority_reason),
                    "real tender, verified capability, or resolved Gate authority scoped to this Claim",
                    [ref, claim.get("authority_ref")], ["task3", "submission"],
                    "gate1", "confirm a real authority or demote to intended"))
            action_refs = _ref_list(claim, "action_refs")
            if claim.get("content_kind") in ("proposal", "target") and not action_refs:
                diagnostics.append(_diagnostic("claim.action", "unowned", "blocker", "%s committed without DeliveryAction" % ref, "owned executable action", [ref], ["task3", "submission"], "task2.5", "link an owned Action or demote the claim"))
            for action_ref in action_refs:
                action = actions.get(action_ref) or {}
                if action.get("commitment_level") != "committed":
                    diagnostics.append(_diagnostic("claim.action_strength", "overcommitted", "blocker", "%s is committed but %s is not" % (ref, action_ref), "Claim commitment no stronger than Action", [ref, action_ref], ["task3", "submission"], "gate1", "confirm the Action or demote the Claim"))

    for action in _as_list(delivery.get("actions")):
        if not isinstance(action, dict) or not _entity_id(action):
            continue
        ref = _entity_id(action)
        if action.get("selection_status") not in ("candidate", "selected", "superseded", "rejected"):
            diagnostics.append(_diagnostic("action.selection", "schema", "fatal", "%s selection_status=%r" % (ref, action.get("selection_status")), "candidate|selected|superseded|rejected", [ref], ["compile"], "task2.5"))
        if action.get("readiness_status") not in ("unassessed", "planned", "confirmed", "blocked"):
            diagnostics.append(_diagnostic("action.readiness", "schema", "fatal", "%s readiness_status=%r" % (ref, action.get("readiness_status")), "unassessed|planned|confirmed|blocked", [ref], ["compile"], "task2.5"))
        if action.get("commitment_level") not in ("intended", "committed"):
            diagnostics.append(_diagnostic("action.commitment", "schema", "fatal", "%s commitment_level=%r" % (ref, action.get("commitment_level")), "intended|committed", [ref], ["compile"], "task2.5"))
        if action.get("selection_status") != "selected":
            continue
        listed_resource_refs = set(_ref_list(action, "resource_refs"))
        demand_resource_refs = {
            item.get("resource_ref") for item in _as_list(action.get("resource_demands"))
            if isinstance(item, dict) and item.get("resource_ref")
        }
        if not demand_resource_refs.issubset(listed_resource_refs):
            diagnostics.append(_diagnostic(
                "action.resource_ref_mismatch", "contradictory", "blocker",
                "%s demands unlisted resources %s" % (
                    ref, sorted(demand_resource_refs - listed_resource_refs)),
                "resource_refs exactly include every demand envelope",
                [ref] + sorted(demand_resource_refs - listed_resource_refs),
                ["task3", "submission"], "task2.5",
                "synchronize resource_refs and resource_demands"))
        if ((action.get("required") or action.get("commitment_level") == "committed")
                and listed_resource_refs - demand_resource_refs):
            diagnostics.append(_diagnostic(
                "action.resource_demand_missing", "unmeasured", "blocker",
                "%s references resources without bounded demand: %s" % (
                    ref, sorted(listed_resource_refs - demand_resource_refs)),
                "bounded demand for every required/committed resource",
                [ref] + sorted(listed_resource_refs - demand_resource_refs),
                ["task3", "submission"], "task2.5",
                "add low/high demand or remove the unused resource reference"))
        accountable = _ref_list(action, "accountable_role_ref")
        if len(accountable) != 1:
            severity = "blocker" if action.get("required") or action.get("commitment_level") == "committed" else "major"
            diagnostics.append(_diagnostic("action.owner", "unowned", severity, "%s has %s accountable roles" % (ref, len(accountable)), "exactly one bidder accountable DeliveryRole", [ref], ["submission"] if severity == "blocker" else [], "task2.5", "assign one accountable bidder role"))
        if (action.get("required") or action.get("commitment_level") == "committed") and not _ref_list(action, "responsible_role_refs", "accountable_role_ref"):
            diagnostics.append(_diagnostic("action.responsible", "unowned", "blocker", "%s has no responsible bidder role" % ref, "at least one responsible DeliveryRole", [ref], ["submission"], "task2.5"))
        if action.get("commitment_level") == "committed":
            authority_ok, authority_reason = _authority_valid(
                action.get("authority_ref"), ref, documents, registry,
                "bidder_capability")
            if not authority_ok:
                diagnostics.append(_diagnostic(
                    "action.authority", "overcommitted", "blocker",
                    "%s committed with invalid authority: %s" % (ref, authority_reason),
                    "real resolved authority scoped to this Action", [ref, action.get("authority_ref")],
                    ["task3", "submission"], "gate1", "confirm or demote the Action"))
            acceptance_refs = _ref_list(action, "acceptance_refs")
            if not acceptance_refs:
                diagnostics.append(_diagnostic("action.acceptance", "unsupported", "blocker", "%s committed without AcceptanceContract" % ref, "bounded acceptance contract", [ref], ["task3", "submission"], "task2.5", "add acceptance criteria or demote the Action", tags=["acceptance_missing"]))
            for acceptance_ref in acceptance_refs:
                missing = _acceptance_complete(acceptances.get(acceptance_ref) or {})
                if missing:
                    diagnostics.append(_diagnostic("acceptance.complete", "unsupported", "blocker", "%s missing %s" % (acceptance_ref, ", ".join(missing)), "complete AcceptanceContract", [ref, acceptance_ref], ["task3", "submission"], "gate1", "complete acceptance and correction boundaries"))
            if action.get("readiness_status") != "confirmed":
                diagnostics.append(_diagnostic("action.readiness_committed", "overcommitted", "blocker", "%s committed but readiness=%s" % (ref, action.get("readiness_status")), "confirmed readiness", [ref], ["task3", "submission"], "gate1", "confirm capacity or demote the Action"))

        if action.get("required") or action.get("commitment_level") == "committed":
            if not _nonempty(action.get("time_window")):
                diagnostics.append(_diagnostic(
                    "action.time_window", "unmeasured", "blocker",
                    "%s required/committed without a bounded time_window" % ref,
                    "explicit delivery window", [ref], ["task3", "submission"],
                    "task2.5", "add a tender/Gate-authorized delivery window"))
            demands = [item for item in _as_list(action.get("resource_demands")) if isinstance(item, dict)]
            if not demands and not (action.get("resource_treatment") or {}).get("cost_not_applicable"):
                diagnostics.append(_diagnostic(
                    "action.resource_treatment", "unmeasured", "blocker",
                    "%s required/committed without resource demand or authorized not-applicable treatment" % ref,
                    "bounded resource_demands or cost_not_applicable with authority/reason",
                    [ref], ["task3", "submission"], "task2.5",
                    "map owned resources/cost or document an authorized not-applicable treatment"))
            treatment = action.get("resource_treatment") or {}
            if treatment.get("cost_not_applicable") and (
                    not _nonempty(treatment.get("reason"))
                    or not _nonempty(treatment.get("authority_ref"))):
                diagnostics.append(_diagnostic(
                    "action.resource_treatment_authority", "unsupported", "blocker",
                    "%s cost_not_applicable treatment lacks reason/authority" % ref,
                    "explicit reason and real authority", [ref], ["task3", "submission"],
                    "gate1", "confirm the no-cost boundary or map a budget demand"))

        budget_cap = (documents.get("requirements.json") or {}).get("budget_cap") or {}
        if (action.get("selection_status") == "selected"
                and isinstance(budget_cap.get("value"), (int, float))
                and not isinstance(budget_cap.get("value"), bool)):
            budget_refs = {
                item.get("id") for item in _as_list(delivery.get("resource_envelopes"))
                if isinstance(item, dict) and item.get("kind") == "budget"
                and item.get("portfolio_budget") is True and item.get("id")
            }
            budget_demands = [
                item for item in _as_list(action.get("resource_demands"))
                if isinstance(item, dict) and item.get("resource_ref") in budget_refs
            ]
            treatment = action.get("resource_treatment") or {}
            if not budget_demands and not treatment.get("cost_not_applicable"):
                diagnostics.append(_diagnostic(
                    "budget.action_unmapped", "unmeasured", "blocker",
                    "%s selected without explicit portfolio budget treatment" % ref,
                    "bounded budget demand or authorized cost_not_applicable",
                    [ref] + sorted(budget_refs), ["task3", "submission"],
                    "task2.5", "map this Action cost so portfolio totals cannot omit it"))
            for demand in budget_demands:
                if not isinstance(demand.get("low"), (int, float)) or not isinstance(demand.get("high"), (int, float)):
                    diagnostics.append(_diagnostic(
                        "budget.action_unbounded", "unmeasured", "blocker",
                        "%s has unbounded portfolio budget demand" % ref,
                        "numeric low/high budget demand", [ref, demand.get("resource_ref")],
                        ["task3", "submission"], "gate1",
                        "confirm bounded cost or remove the Action from the selected portfolio"))
            if treatment.get("cost_not_applicable"):
                if not _nonempty(treatment.get("reason")):
                    diagnostics.append(_diagnostic(
                        "budget.no_cost_reason", "unmeasured", "blocker",
                        "%s no-cost treatment has no reason" % ref,
                        "explicit reason for cost_not_applicable", [ref],
                        ["task3", "submission"], "task2.5",
                        "document why this Action adds no portfolio cost"))
                treatment_ok, treatment_reason = _authority_valid(
                    treatment.get("authority_ref"), ref, documents, registry,
                    "commitment_authority")
                if not treatment_ok:
                    diagnostics.append(_diagnostic(
                        "budget.no_cost_authority", "unsupported", "blocker",
                        "%s no-cost treatment has invalid authority: %s" % (ref, treatment_reason),
                        "real authority scoped to this Action", [ref, treatment.get("authority_ref")],
                        ["task3", "submission"], "gate1",
                        "confirm the no-cost treatment or map budget demand"))

    selected_resource_refs = set()
    for action in actions.values():
        if action.get("selection_status") == "selected":
            selected_resource_refs.update(_ref_list(action, "resource_refs"))
            selected_resource_refs.update(
                item.get("resource_ref") for item in _as_list(action.get("resource_demands"))
                if isinstance(item, dict) and item.get("resource_ref"))
    for resource in _as_list(delivery.get("resource_envelopes")):
        if not isinstance(resource, dict) or resource.get("id") not in selected_resource_refs:
            continue
        resource_ref = resource.get("id")
        if resource.get("status") == "confirmed":
            authority_ok, authority_reason = _authority_valid(
                resource.get("authority_ref"), resource_ref, documents, registry,
                "bidder_capability")
            if not authority_ok:
                diagnostics.append(_diagnostic(
                    "resource.authority", "overcommitted", "blocker",
                    "%s confirmed with invalid authority: %s" % (resource_ref, authority_reason),
                    "real capability/Gate authority scoped to this ResourceEnvelope",
                    [resource_ref, resource.get("authority_ref")], ["task3", "submission"],
                    "gate1", "confirm capacity or demote the resource status"))

    for acceptance_ref, acceptance in acceptances.items():
        if not any(acceptance_ref in _ref_list(action, "acceptance_refs")
                   for action in actions.values() if action.get("selection_status") == "selected"):
            continue
        authority_ok, authority_reason = _authority_valid(
            acceptance.get("authority_ref"), acceptance_ref, documents, registry,
            "commitment_authority")
        if not authority_ok:
            diagnostics.append(_diagnostic(
                "acceptance.authority", "overcommitted", "blocker",
                "%s has invalid authority: %s" % (acceptance_ref, authority_reason),
                "tender Requirement, verified material, or resolved Gate authority",
                [acceptance_ref, acceptance.get("authority_ref")], ["task3", "submission"],
                "gate1", "bind acceptance to a real authority or narrow it"))

    if stage in ("generation", "submission"):
        sections = [item for item in _as_list(strategy.get("sections")) if isinstance(item, dict)]
        jobs = {item.get("id"): item for item in _as_list(strategy.get("decision_jobs")) if isinstance(item, dict)}
        for section in sections:
            ref = _entity_id(section) or "section-%s" % section.get("n")
            primary = _ref_list(section, "primary_decision_job_ref")
            secondary = _ref_list(section, "secondary_decision_job_ref")
            if len(primary) != 1:
                diagnostics.append(_diagnostic("section.primary_job", "orphan", "blocker", "%s has %s primary DecisionJobs" % (ref, len(primary)), "exactly one primary DecisionJob", [ref], ["task3", "submission"], "task2.5", "compile one primary customer decision job"))
            if len(secondary) > 1:
                diagnostics.append(_diagnostic("section.secondary_job", "redundant", "blocker", "%s has %s secondary DecisionJobs" % (ref, len(secondary)), "zero or one secondary DecisionJob", [ref], ["task3"], "task2.5"))
            for job_ref in primary + secondary:
                job = jobs.get(job_ref) or {}
                if job.get("section_ref") != ref:
                    diagnostics.append(_diagnostic("section.job_backref", "contradictory", "blocker", "%s points to %s but job.section_ref=%r" % (ref, job_ref, job.get("section_ref")), "bidirectional section/job binding", [ref, job_ref], ["task3"], "task2.5"))
        for job in jobs.values():
            ref = _entity_id(job)
            if job.get("job_kind") not in JOB_KINDS:
                diagnostics.append(_diagnostic("job.kind", "schema", "fatal", "%s job_kind=%r" % (ref, job.get("job_kind")), sorted(JOB_KINDS), [ref], ["compile"], "task2.5"))
            missing = []
            if not _ref_list(job, "role_refs"): missing.append("role_refs")
            if not _ref_list(job, "criterion_refs"): missing.append("criterion_refs")
            if not (_ref_list(job, "value_proposition_refs") or _ref_list(job, "claim_refs")): missing.append("value_proposition_refs|claim_refs")
            if not _nonempty(job.get("expected_judgment")): missing.append("expected_judgment")
            if missing:
                diagnostics.append(_diagnostic("job.path", "orphan", "blocker", "%s missing %s" % (ref, ", ".join(missing)), "role + criterion + expected judgment + VP/Claim", [ref], ["task3", "submission"], "task2.5"))


def _resource_diagnostics(documents):
    diagnostics = []
    delivery = documents.get("delivery-plan.json") or {}
    resources = {item.get("id"): item for item in _as_list(delivery.get("resource_envelopes")) if isinstance(item, dict)}
    totals = {}
    contributing = {}
    for action in _as_list(delivery.get("actions")):
        if not isinstance(action, dict) or action.get("selection_status") != "selected":
            continue
        for demand in _as_list(action.get("resource_demands")):
            if not isinstance(demand, dict) or not demand.get("resource_ref"):
                continue
            resource_ref = demand.get("resource_ref")
            resource = resources.get(resource_ref) or {}
            window = demand.get("time_window") or action.get("time_window")
            if not _nonempty(window):
                diagnostics.append(_diagnostic(
                    "resource.window_missing", "unmeasured", "blocker",
                    "%s demand for %s has no time window" % (_entity_id(action), resource_ref),
                    "demand window aligned to the ResourceEnvelope",
                    [_entity_id(action), resource_ref], ["task3", "submission"],
                    "task2.5", "add a bounded demand window"))
                window = "unspecified"
            resource_window = resource.get("time_window")
            if _nonempty(resource_window) and window != resource_window:
                diagnostics.append(_diagnostic(
                    "resource.window_mismatch", "contradictory", "blocker",
                    "%s demand window %s does not match %s window %s" % (
                        _entity_id(action), window, resource_ref, resource_window),
                    "matching comparable windows", [_entity_id(action), resource_ref],
                    ["task3", "submission"], "task2.5",
                    "normalize or split the ResourceEnvelope by time window"))
            demand_unit = demand.get("unit")
            if _nonempty(demand_unit) and _nonempty(resource.get("unit")) \
                    and demand_unit != resource.get("unit"):
                diagnostics.append(_diagnostic(
                    "resource.unit_mismatch", "contradictory", "blocker",
                    "%s demand unit %s does not match %s unit %s" % (
                        _entity_id(action), demand_unit, resource_ref, resource.get("unit")),
                    "matching resource units", [_entity_id(action), resource_ref],
                    ["task3", "submission"], "task2.5",
                    "normalize the demand without changing its real quantity"))
            key = (resource_ref, window)
            low = demand.get("low")
            high = demand.get("high")
            if not isinstance(low, (int, float)) or not isinstance(high, (int, float)):
                if action.get("commitment_level") == "committed":
                    diagnostics.append(_diagnostic("resource.unknown_demand", "overcommitted", "blocker", "%s has unknown demand for %s" % (_entity_id(action), demand.get("resource_ref")), "numeric low/high demand", [_entity_id(action), demand.get("resource_ref")], ["task3", "submission"], "gate1", "confirm a bounded resource demand"))
                continue
            if low < 0 or high < low:
                diagnostics.append(_diagnostic(
                    "resource.invalid_range", "contradictory", "blocker",
                    "%s has invalid demand %.2f–%.2f for %s" % (
                        _entity_id(action), low, high, resource_ref),
                    "0 <= low <= high", [_entity_id(action), resource_ref],
                    ["task3", "submission"], "task2.5",
                    "correct the bounded demand range"))
                continue
            totals.setdefault(key, [0.0, 0.0])
            totals[key][0] += low
            totals[key][1] += high
            contributing.setdefault(key, []).append(_entity_id(action))

    for (resource_ref, window), (demand_low, demand_high) in totals.items():
        resource = resources.get(resource_ref) or {}
        capacity = resource.get("capacity") or {}
        cap_low, cap_high = capacity.get("low"), capacity.get("high")
        refs = [resource_ref] + contributing.get((resource_ref, window), [])
        if not isinstance(cap_low, (int, float)) or not isinstance(cap_high, (int, float)):
            diagnostics.append(_diagnostic("resource.unknown_capacity", "overcommitted", "blocker", "%s has no bounded capacity for %s" % (resource_ref, window), "capacity low/high in matching unit", refs, ["task3", "submission"], "gate1", "confirm the portfolio capacity envelope"))
            continue
        if demand_low > cap_high:
            diagnostics.append(_diagnostic("resource.overload", "overcommitted", "blocker", "demand %.2f–%.2f exceeds capacity %.2f–%.2f in %s" % (demand_low, demand_high, cap_low, cap_high, window), "portfolio demand within confirmed capacity", refs, ["task3", "submission"], "gate1", "reduce, sequence, or add confirmed capacity"))
        elif demand_high > cap_low:
            diagnostics.append(_diagnostic("resource.possible_overload", "overcommitted", "major", "demand %.2f–%.2f overlaps capacity %.2f–%.2f in %s" % (demand_low, demand_high, cap_low, cap_high, window), "confirm peak demand or capacity", refs, [], "gate1", "tighten the range before committing"))

    requirements = documents.get("requirements.json") or {}
    budget_cap = requirements.get("budget_cap") or {}
    cap_value = budget_cap.get("value")
    if isinstance(cap_value, (int, float)) and not isinstance(cap_value, bool):
        budget_resources = [
            item for item in resources.values()
            if item.get("kind") == "budget" and item.get("portfolio_budget") is True
        ]
        if len(budget_resources) != 1:
            diagnostics.append(_diagnostic(
                "budget.envelope", "unmeasured", "blocker",
                "%s portfolio budget envelopes found for cap %s %s" % (
                    len(budget_resources), cap_value, budget_cap.get("unit") or ""),
                "exactly one portfolio_budget ResourceEnvelope",
                [item.get("id") for item in budget_resources],
                ["task3", "submission"], "task2.5",
                "create one confirmed budget envelope and map selected Action demand",
            ))
        else:
            budget = budget_resources[0]
            budget_ref = budget.get("id")
            cap_unit = str(budget_cap.get("unit") or "").strip()
            resource_unit = str(budget.get("unit") or "").strip()
            if cap_unit and resource_unit and cap_unit != resource_unit:
                diagnostics.append(_diagnostic(
                    "budget.unit", "contradictory", "blocker",
                    "%s uses %s but tender cap uses %s" % (
                        budget_ref, resource_unit, cap_unit),
                    "matching budget units", [budget_ref],
                    ["task3", "submission"], "task2.5",
                    "normalize the budget unit without changing the tender amount",
                ))
            capacity = budget.get("capacity") or {}
            capacity_low = capacity.get("low")
            capacity_high = capacity.get("high")
            if (not isinstance(capacity_low, (int, float))
                    or not isinstance(capacity_high, (int, float))
                    or capacity_low < 0 or capacity_high < capacity_low):
                diagnostics.append(_diagnostic(
                    "budget.capacity", "unmeasured", "blocker",
                    "%s has no valid numeric low/high bound" % budget_ref,
                    "0 <= portfolio budget low <= high <= tender cap", [budget_ref],
                    ["task3", "submission"], "gate1",
                    "confirm a bounded single recommended budget",
                ))
            elif capacity_high > cap_value:
                diagnostics.append(_diagnostic(
                    "budget.cap", "overcommitted", "blocker",
                    "%s high %.2f exceeds tender cap %.2f %s" % (
                        budget_ref, capacity_high, cap_value, cap_unit),
                    "budget envelope within tender cap", [budget_ref],
                    ["task3", "submission"], "gate1",
                    "reduce the plan or confirm a lawful cap interpretation",
                ))
            budget_demands = [
                (key, value) for key, value in totals.items()
                if key[0] == budget_ref
            ]
            if not budget_demands:
                diagnostics.append(_diagnostic(
                    "budget.demand_missing", "unmeasured", "blocker",
                    "%s is not linked to selected Action demand" % budget_ref,
                    "selected portfolio cost mapped to the budget envelope",
                    [budget_ref], ["task3", "submission"], "task2.5",
                    "add bounded budget demand to the selected Action portfolio",
                ))
            else:
                demand_low = sum(value[0] for _, value in budget_demands)
                demand_high = sum(value[1] for _, value in budget_demands)
                if demand_high > cap_value:
                    diagnostics.append(_diagnostic(
                        "budget.portfolio_cap", "overcommitted", "blocker",
                        "selected Action budget %.2f–%.2f exceeds cap %.2f %s" % (
                            demand_low, demand_high, cap_value, cap_unit),
                        "single recommended portfolio within tender cap",
                        [budget_ref] + [ref for key in budget_demands for ref in contributing.get(key, [])],
                        ["task3", "submission"], "gate1",
                        "reduce or reallocate selected Action demand",
                    ))
    return diagnostics


def _delivery_structure_diagnostics(documents):
    diagnostics = []
    delivery = documents.get("delivery-plan.json") or {}
    actions = {
        item.get("id"): item for item in _as_list(delivery.get("actions"))
        if isinstance(item, dict) and item.get("id")
        and item.get("selection_status") == "selected"
    }
    dependencies = {
        item.get("id"): item
        for item in _as_list(delivery.get("customer_dependencies"))
        if isinstance(item, dict) and item.get("id")
    }

    graph = {
        ref: [target for target in _ref_list(action, "predecessor_refs") if target in actions]
        for ref, action in actions.items()
    }
    visiting = set()
    visited = set()
    reported = set()

    def visit(ref, path):
        if ref in visited:
            return
        if ref in visiting:
            start = path.index(ref) if ref in path else 0
            cycle = tuple(path[start:] + [ref])
            key = tuple(sorted(set(cycle)))
            if key not in reported:
                reported.add(key)
                diagnostics.append(_diagnostic(
                    "delivery.precedence_cycle", "contradictory", "blocker",
                    "Action precedence cycle: %s" % " -> ".join(cycle),
                    "acyclic delivery precedence", list(key),
                    ["task3", "submission"], "task2.5",
                    "remove the circular dependency or split phases",
                ))
            return
        visiting.add(ref)
        for predecessor in graph.get(ref, []):
            visit(predecessor, path + [predecessor])
        visiting.remove(ref)
        visited.add(ref)

    for action_ref in graph:
        visit(action_ref, [action_ref])

    for action_ref, action in actions.items():
        for dependency_ref in _ref_list(action, "dependency_refs"):
            dependency = dependencies.get(dependency_ref) or {}
            required_fields = ("input", "needed_by", "delay_impact", "fallback", "escalation_path")
            missing = [field for field in required_fields if not dependency.get(field)]
            if missing:
                severity = "blocker" if action.get("commitment_level") == "committed" else "major"
                diagnostics.append(_diagnostic(
                    "dependency.incomplete", "unsupported", severity,
                    "%s for %s missing %s" % (
                        dependency_ref, action_ref, ", ".join(missing)),
                    "bounded customer input with safe fallback and escalation",
                    [action_ref, dependency_ref],
                    ["task3", "submission"] if severity == "blocker" else [],
                    "task2.5", "complete the dependency or narrow the Claim/Action",
                ))
            transferred = _ref_list(dependency, "transferred_requirement_refs")
            if transferred:
                diagnostics.append(_diagnostic(
                    "dependency.responsibility_transfer", "overcommitted", "blocker",
                    "%s attempts to transfer Requirement responsibility: %s" % (
                        dependency_ref, ", ".join(transferred)),
                    "customer input must not transfer bidder mandatory responsibility",
                    [action_ref, dependency_ref] + transferred,
                    ["task3", "submission"], "task2.5",
                    "retain bidder accountability and add a safe fallback",
                ))

    for index, excluded in enumerate(_as_list(delivery.get("excluded_scope"))):
        if isinstance(excluded, dict):
            requirement_refs = _ref_list(excluded, "requirement_refs")
            if requirement_refs:
                diagnostics.append(_diagnostic(
                    "delivery.excluded_requirement", "contradictory", "blocker",
                    "excluded_scope[%s] intersects Requirement %s" % (
                        index, ", ".join(requirement_refs)),
                    "no excluded scope may create a negative deviation",
                    requirement_refs, ["task3", "submission"], "task1",
                    "remove the exclusion or formally resolve the Requirement conflict",
                ))
    return diagnostics


def _coverage_obligations(documents):
    cv = documents.get("customer-value.json") or {}
    links = []
    need_criteria = {}
    for item in _as_list(cv.get("need_criterion_links")):
        if isinstance(item, dict) and item.get("need_ref") and item.get("criterion_ref"):
            need_criteria.setdefault(item["need_ref"], []).append(item["criterion_ref"])
    for relation in _as_list(cv.get("role_need_links")):
        if not isinstance(relation, dict) or not relation.get("role_ref") or not relation.get("need_ref"):
            continue
        criteria = _ref_list(relation, "criterion_refs") or need_criteria.get(relation.get("need_ref"), [])
        requiredness = relation.get("requiredness")
        if requiredness not in ("required", "expected", "exploratory"):
            requiredness = "required" if relation.get("priority_band") == "critical" else ("expected" if relation.get("priority_band") in ("high", "medium") else "exploratory")
        for criterion_ref in criteria:
            links.append({
                "role_ref": relation["role_ref"], "need_ref": relation["need_ref"],
                "criterion_ref": criterion_ref, "requiredness": requiredness,
                "confidence": relation.get("confidence") or "unknown",
                "source_ref": relation.get("id"),
            })
    return links


def _authoritative_realization_manifests(realization_dir):
    manifests = {}
    diagnostics = []
    if not realization_dir or not os.path.isdir(realization_dir):
        return manifests, diagnostics
    for filename in sorted(os.listdir(realization_dir)):
        if not filename.endswith(".json"):
            continue
        if filename.endswith(".proposed.json") or filename.endswith(".semantic.json"):
            continue
        path = os.path.join(realization_dir, filename)
        try:
            manifest = _read_json(path)
        except Exception as exc:
            diagnostics.append(_diagnostic(
                "realization.parse", "schema", "fatal",
                "%s cannot be parsed: %s" % (filename, exc),
                "valid realization/v1 manifest", blocks=["submission"],
                owner="task3",
            ))
            continue
        if manifest.get("schema_version") != SCHEMA_VERSIONS["realization"]:
            continue
        section_ref = manifest.get("section_ref")
        if not section_ref:
            diagnostics.append(_diagnostic(
                "realization.section_ref", "schema", "fatal",
                "%s has no section_ref" % filename,
                "authoritative realization with section_ref",
                blocks=["submission"], owner="task3",
            ))
            continue
        if section_ref in manifests:
            diagnostics.append(_diagnostic(
                "realization.duplicate", "contradictory", "fatal",
                "multiple authoritative manifests for %s" % section_ref,
                "exactly one realization/v1 manifest per section",
                [section_ref], ["submission"], "task3",
            ))
            continue
        manifest["_authoritative_path"] = os.path.abspath(path)
        manifests[section_ref] = manifest
    return manifests, diagnostics


def coverage_diagnostics(documents, realization_dir=None):
    cv = documents.get("customer-value.json") or {}
    strategy = documents.get("strategy.json") or {}
    requirements = documents.get("requirements.json") or {}
    diagnostics = []
    sections = {item.get("id"): item for item in _as_list(strategy.get("sections")) if isinstance(item, dict)}
    jobs = {item.get("id"): item for item in _as_list(strategy.get("decision_jobs")) if isinstance(item, dict)}
    vps = [item for item in _as_list(cv.get("value_propositions")) if isinstance(item, dict) and item.get("status") in ("selected", "publishable")]
    claims = [item for item in _as_list(cv.get("claims")) if isinstance(item, dict) and item.get("status") == "publishable"]

    requirement_ids = [
        item.get("id")
        for key in ("mandatory", "scoring", "deliverables")
        for item in _as_list(requirements.get(key))
        if isinstance(item, dict) and item.get("id")
    ]
    mapped = set()
    for section in sections.values():
        mapped.update(_ref_list(section, "addresses"))
    missing_requirements = [ref for ref in requirement_ids if ref not in mapped]
    for ref in missing_requirements:
        diagnostics.append(_diagnostic("coverage.requirement", "uncovered", "blocker", "%s has no Section mapping" % ref, "Requirement -> Section", [ref], ["task3", "submission"], "task1", "map the requirement and realize its response"))

    realized_refs = set()
    realized_requirement_refs = set()
    realization_status = {}
    manifests, _ = _authoritative_realization_manifests(realization_dir)
    for manifest in manifests.values():
        for item in _as_list(manifest.get("realizations")):
            if isinstance(item, dict) and item.get("semantic_status") == "entailed" and item.get("canonical_ref"):
                realized_refs.add(item["canonical_ref"])
                realization_status[item["canonical_ref"]] = manifest.get("status")
        if manifest.get("status") == "valid":
            for item in _as_list(manifest.get("requirement_realizations")):
                if (isinstance(item, dict) and item.get("status") == "addressed"
                        and item.get("requirement_ref") and _as_list(item.get("anchors"))):
                    realized_requirement_refs.add(item.get("requirement_ref"))

    obligations = _coverage_obligations(documents)
    paths = []
    for obligation in obligations:
        role_ref, need_ref, criterion_ref = obligation["role_ref"], obligation["need_ref"], obligation["criterion_ref"]
        matching_vps = [vp for vp in vps if role_ref in _ref_list(vp, "role_refs") and need_ref in _ref_list(vp, "need_refs") and criterion_ref in _ref_list(vp, "criterion_refs")]
        matching_claims = [claim for claim in claims if any(vp.get("id") in _ref_list(claim, "value_proposition_refs") for vp in matching_vps)]
        matching_jobs = [job for job in jobs.values() if role_ref in _ref_list(job, "role_refs") and criterion_ref in _ref_list(job, "criterion_refs") and (any(vp.get("id") in _ref_list(job, "value_proposition_refs") for vp in matching_vps) or any(claim.get("id") in _ref_list(job, "claim_refs") for claim in matching_claims))]
        matching_sections = [sections.get(job.get("section_ref")) for job in matching_jobs if sections.get(job.get("section_ref"))]
        maturity = "identified"
        health = "incomplete"
        caused_by = []
        if matching_vps: maturity = "connected"
        if matching_claims: maturity = "publishable"
        if matching_sections: health = "valid"
        if realization_dir:
            realized = [claim for claim in matching_claims if claim.get("id") in realized_refs and realization_status.get(claim.get("id")) == "valid"]
            if realized:
                maturity = "realized"
            else:
                health = "incomplete"
        if not matching_vps:
            caused_by.append("vp_missing")
        elif not matching_claims:
            caused_by.append("claim_missing")
        elif not matching_jobs:
            caused_by.append("decision_job_missing")
        elif not matching_sections:
            caused_by.append("section_missing")
        elif realization_dir and maturity != "realized":
            caused_by.append("realization_missing")
        path_ref = "%s|%s|%s" % (role_ref, need_ref, criterion_ref)
        paths.append(dict(obligation, maturity=maturity, health=health, caused_by=caused_by,
                          value_proposition_refs=[item.get("id") for item in matching_vps],
                          claim_refs=[item.get("id") for item in matching_claims],
                          decision_job_refs=[item.get("id") for item in matching_jobs],
                          section_refs=[item.get("id") for item in matching_sections]))
        if caused_by and obligation["requiredness"] in ("required", "expected"):
            severity = "blocker" if obligation["requiredness"] == "required" else "major"
            blocks = ["submission"] if severity == "blocker" else []
            diagnostics.append(_diagnostic("coverage.customer_path", "uncovered", severity, "%s incomplete: %s" % (path_ref, ", ".join(caused_by)), "Role -> Need -> Criterion -> selected VP -> publishable Claim -> DecisionJob -> Section%s" % (" -> realization" if realization_dir else ""), [role_ref, need_ref, criterion_ref], blocks, "task2.5", "repair the nearest missing canonical owner"))

    return {
        "schema_version": SCHEMA_VERSIONS["coverage"],
        "requirement_track": {
            "total": len(requirement_ids),
            "mapped": len(requirement_ids) - len(missing_requirements),
            "missing": missing_requirements,
            "realized": len(realized_requirement_refs) if realization_dir else None,
            "missing_realization": (
                sorted(set(requirement_ids) - realized_requirement_refs)
                if realization_dir else []),
        },
        "customer_value_track": {
            "obligation_count": len(obligations),
            "required_count": sum(1 for item in obligations if item["requiredness"] == "required"),
            "realized_required": sum(1 for item in paths if item["requiredness"] == "required" and item["maturity"] == "realized" and item["health"] == "valid"),
            "paths": paths,
        },
        "diagnostics": diagnostics,
    }


def _realization_diagnostics(state_dir, documents, realization_dir,
                             include_summary=True):
    """Deterministically reject missing or stale section realization manifests."""
    diagnostics = []
    strategy = documents.get("strategy.json") or {}
    manifests, loader_diagnostics = _authoritative_realization_manifests(realization_dir)
    diagnostics.extend(loader_diagnostics)
    expected_snapshot_id, _, _ = _expected_snapshot_id(documents)

    artifacts_path = os.path.join(state_dir, "derived", "manifests", "artifacts.json")
    artifacts = {}
    if os.path.isfile(artifacts_path):
        try:
            artifact_doc = _read_json(artifacts_path)
            artifacts = {
                item.get("artifact_id"): item
                for item in _as_list(artifact_doc.get("artifacts"))
                if isinstance(item, dict) and item.get("artifact_id")
            }
        except Exception as exc:
            diagnostics.append(_diagnostic(
                "realization.artifact_registry", "schema", "fatal",
                "artifact registry cannot be read: %s" % exc,
                "valid current artifact registry", blocks=["submission"], owner="main"))

    def validate_artifacts(ref, manifest):
        manifest_path = manifest.get("_authoritative_path")
        artifact = artifacts.get("realization:%s" % ref)
        if not manifest_path or not artifact:
            diagnostics.append(_diagnostic(
                "realization.unregistered", "unsupported", "blocker",
                "%s realization is not registered" % ref,
                "authoritative manifest emitted by audit-realization",
                [ref], ["submission"], "task3",
                "re-run audit-realization with the current compiled brief"))
            return
        if (os.path.abspath(artifact.get("path") or "") != os.path.abspath(manifest_path)
                or artifact.get("output_hash") != file_hash(manifest_path)
                or artifact.get("status") != "fresh"):
            diagnostics.append(_diagnostic(
                "realization.artifact_drift", "contradictory", "blocker",
                "%s authoritative manifest differs from its registered audit artifact" % ref,
                "fresh immutable audit output", [ref], ["submission"], "task3",
                "re-audit; do not hand-edit the authoritative manifest"))
        brief_path = manifest.get("brief_path")
        brief_root = os.path.abspath(os.path.join(state_dir, "derived", "briefs"))
        if not _nonempty(brief_path) or not os.path.isfile(brief_path):
            diagnostics.append(_diagnostic(
                "realization.brief_missing", "unsupported", "blocker",
                "%s has no readable compiled brief" % ref,
                "registered current brief", [ref], ["submission"], "task3",
                "recompile and re-audit the section"))
            return
        try:
            inside = os.path.commonpath([brief_root, os.path.abspath(brief_path)]) == brief_root
        except ValueError:
            inside = False
        if not inside:
            diagnostics.append(_diagnostic(
                "realization.brief_path", "unsupported", "blocker",
                "%s brief is outside the run's derived/briefs registry" % ref,
                "run-local compiled brief", [ref], ["submission"], "task3"))
            return
        brief = {}
        try:
            brief = _read_json(brief_path)
            brief_issues, artifact_id = _brief_integrity_issues(
                state_dir, brief_path, brief, ref, documents)
        except Exception as exc:
            brief_issues, artifact_id = [str(exc)], None
        if brief_issues or manifest.get("brief_hash") != brief.get("brief_hash") \
                or manifest.get("brief_artifact_id") != artifact_id:
            diagnostics.append(_diagnostic(
                "realization.brief_drift", "contradictory", "blocker",
                "%s brief lineage is invalid: %s" % (
                    ref, "; ".join(brief_issues[:3]) if brief_issues else "hash/id mismatch"),
                "current registered brief with matching snapshot/hash",
                [ref], ["submission"], "task3",
                "recompile the brief and re-audit the section"))

    addressed_requirements = set()
    for section in _as_list(strategy.get("sections")):
        if not isinstance(section, dict) or not section.get("id"):
            continue
        ref = section["id"]
        manifest = manifests.get(ref)
        if not manifest:
            diagnostics.append(_diagnostic(
                "realization.missing", "uncovered", "blocker",
                "%s has no realization manifest" % ref,
                "valid authoritative realization", [ref], ["submission"],
                "task3", "audit the section against its compiled brief",
            ))
            continue
        if manifest.get("status") != "valid":
            diagnostics.append(_diagnostic(
                "realization.invalid", "uncovered", "blocker",
                "%s realization status=%s" % (ref, manifest.get("status")),
                "status=valid", [ref], ["submission"], "task3",
                "repair missing, drifted, or unreviewed realization",
            ))
        validate_artifacts(ref, manifest)
        if manifest.get("snapshot_id") != expected_snapshot_id:
            diagnostics.append(_diagnostic(
                "realization.stale_snapshot", "contradictory", "blocker",
                "%s realization uses snapshot %r, current is %s" % (
                    ref, manifest.get("snapshot_id"), expected_snapshot_id),
                "current generation snapshot", [ref], ["submission"],
                "task3", "recompile the brief and re-audit the section",
            ))
        number = section.get("n")
        section_path = os.path.join(state_dir, "sections", "section-%s.md" % number)
        if not os.path.isfile(section_path):
            diagnostics.append(_diagnostic(
                "realization.section_text_missing", "uncovered", "blocker",
                "%s has a manifest but section-%s.md is missing" % (ref, number),
                "current section text and matching realization",
                [ref], ["submission"], "task3",
                "restore or regenerate the section and re-audit it",
            ))
        elif manifest.get("section_hash") != content_hash(_read_text(section_path)):
            diagnostics.append(_diagnostic(
                "realization.stale_text", "contradictory", "blocker",
                "%s text changed after realization audit" % ref,
                "matching section fingerprint", [ref], ["submission"],
                "task3", "re-audit the current section text",
            ))

        for item in _as_list(manifest.get("requirement_realizations")):
            if (isinstance(item, dict) and item.get("status") == "addressed"
                    and item.get("requirement_ref") and _as_list(item.get("anchors"))
                    and manifest.get("status") == "valid"):
                addressed_requirements.add(item.get("requirement_ref"))

    requirements = documents.get("requirements.json") or {}
    all_requirement_refs = {
        item.get("id")
        for collection in ("mandatory", "scoring", "deliverables")
        for item in _as_list(requirements.get(collection))
        if isinstance(item, dict) and item.get("id")
    }
    for requirement_ref in sorted(all_requirement_refs - addressed_requirements):
        diagnostics.append(_diagnostic(
            "realization.requirement_missing", "uncovered", "blocker",
            "%s has no valid addressed realization in any formal section" % requirement_ref,
            "semantic addressed realization with reason, quote and confidence",
            [requirement_ref], ["submission"], "task3",
            "repair the mapped section response and re-run the independent audit"))

    if not include_summary:
        return diagnostics

    summary_path = os.path.join(state_dir, "sections", "section-0.md")
    summary_manifest = (manifests.get("CH-00") or manifests.get("section-0")
                        or manifests.get("0"))
    if not os.path.isfile(summary_path):
        diagnostics.append(_diagnostic(
            "realization.summary_text_missing", "uncovered", "blocker",
            "required section-0.md is missing",
            "realized-only executive summary", ["CH-00"], ["submission"],
            "task3.5", "compile and write the summary after all sections are valid",
        ))
    if not summary_manifest or summary_manifest.get("status") != "valid":
        diagnostics.append(_diagnostic(
            "realization.summary", "unsupported", "blocker",
            "section-0 has no valid authoritative realized-only manifest",
            "valid summary realization using the section whitelist",
            ["CH-00"], ["submission"], "task3.5",
            "audit the summary against realized claims only",
        ))
    elif summary_manifest.get("snapshot_id") != expected_snapshot_id:
        diagnostics.append(_diagnostic(
            "realization.summary_snapshot", "contradictory", "blocker",
            "section-0 realization uses a stale snapshot",
            "current generation snapshot", ["CH-00"], ["submission"],
            "task3.5", "recompile and re-audit the summary",
        ))
    else:
        validate_artifacts(summary_manifest.get("section_ref") or "CH-00", summary_manifest)
    if (summary_manifest and os.path.isfile(summary_path)
            and summary_manifest.get("section_hash") != content_hash(_read_text(summary_path))):
        diagnostics.append(_diagnostic(
            "realization.summary_stale", "contradictory", "blocker",
            "section-0 changed after realization audit",
            "matching summary fingerprint", ["CH-00"], ["submission"],
            "task3.5", "re-audit the current summary text",
        ))
    return diagnostics


def check_canonical(state_dir, stage="draft", realization_dir=None, write_derived=False):
    if stage not in ("draft", "generation", "submission"):
        return {"passed": False, "issues": ["stage must be draft, generation, or submission"]}
    documents, load_issues = load_state(state_dir)
    diagnostics = []
    for issue in load_issues:
        diagnostics.append(_diagnostic("state.missing", "schema", "fatal", issue, "all five canonical files", blocks=["compile"], owner="main"))
    _validate_schema(documents, diagnostics)
    _validate_manifests(state_dir, documents, diagnostics)
    registry = _build_registry(documents, diagnostics)
    _validate_relations(documents, registry, diagnostics)
    _validate_lifecycle(documents, registry, diagnostics, stage)
    diagnostics.extend(_resource_diagnostics(documents))
    diagnostics.extend(_delivery_structure_diagnostics(documents))
    coverage = coverage_diagnostics(documents, realization_dir if stage == "submission" else None)
    diagnostics.extend(coverage["diagnostics"])
    if stage == "submission" and not load_issues:
        diagnostics.extend(_realization_diagnostics(
            state_dir, documents,
            realization_dir or os.path.join(state_dir, "derived", "realization"),
        ))

    if stage == "draft":
        failing = [item for item in diagnostics if item["severity"] == "fatal"]
    elif stage == "generation":
        failing = [item for item in diagnostics if item["severity"] == "fatal" or "task3" in item.get("blocks", []) or "compile" in item.get("blocks", [])]
    else:
        failing = [item for item in diagnostics if item["severity"] in ("fatal", "blocker")]

    result = {
        "passed": not failing,
        "stage": stage,
        "engine": ENGINE,
        "issues": [item["observed"] for item in failing],
        "diagnostics": diagnostics,
        "counts": {
            "fatal": sum(1 for item in diagnostics if item["severity"] == "fatal"),
            "blocker": sum(1 for item in diagnostics if item["severity"] == "blocker"),
            "major": sum(1 for item in diagnostics if item["severity"] == "major"),
            "minor": sum(1 for item in diagnostics if item["severity"] == "minor"),
        },
        "submission_ready": stage == "submission" and not failing,
        "coverage": coverage,
    }
    if write_derived:
        derived = os.path.join(state_dir, "derived")
        os.makedirs(derived, exist_ok=True)
        _write_json_atomic(os.path.join(derived, "coverage.json"), coverage)
        _write_json_atomic(os.path.join(derived, "diagnostics.json"), {
            "schema_version": "diagnostics/v1", "stage": stage, "diagnostics": diagnostics,
        })
    return result


def _decode_pointer(pointer):
    if pointer in ("", "/"):
        return []
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ValueError("JSON pointer must start with /")
    return [part.replace("~1", "/").replace("~0", "~") for part in pointer[1:].split("/")]


def _pointer_parent(document, pointer):
    parts = _decode_pointer(pointer)
    if not parts:
        return None, None
    node = document
    for part in parts[:-1]:
        if isinstance(node, list):
            node = node[int(part)]
        else:
            node = node[part]
    return node, parts[-1]


def _find_entity(document, target_ref):
    for collection, raw in document.items():
        if not isinstance(raw, list):
            continue
        for index, entity in enumerate(raw):
            if isinstance(entity, dict) and _entity_id(entity) == target_ref:
                return collection, index, entity
    return None, None, None


def _apply_operation(document, operation):
    op = operation.get("op")
    if op in ("add", "replace", "remove", "test"):
        pointer = operation.get("path")
        parent, key = _pointer_parent(document, pointer)
        if parent is None:
            if op in ("add", "replace"):
                return copy.deepcopy(operation.get("value"))
            raise ValueError("cannot %s document root" % op)
        if isinstance(parent, list):
            if key == "-":
                if op != "add": raise ValueError("- is only valid for add")
                parent.append(copy.deepcopy(operation.get("value")))
            else:
                index = int(key)
                if op == "add": parent.insert(index, copy.deepcopy(operation.get("value")))
                elif op == "replace": parent[index] = copy.deepcopy(operation.get("value"))
                elif op == "remove": parent.pop(index)
                elif parent[index] != operation.get("value"): raise ValueError("test failed at %s" % pointer)
        else:
            if op == "add": parent[key] = copy.deepcopy(operation.get("value"))
            elif op == "replace":
                if key not in parent: raise ValueError("replace target missing: %s" % pointer)
                parent[key] = copy.deepcopy(operation.get("value"))
            elif op == "remove":
                if key not in parent: raise ValueError("remove target missing: %s" % pointer)
                del parent[key]
            elif parent.get(key) != operation.get("value"): raise ValueError("test failed at %s" % pointer)
        return document
    if op == "transition":
        collection, index, entity = _find_entity(document, operation.get("target_ref"))
        if entity is None:
            raise ValueError("transition target missing: %s" % operation.get("target_ref"))
        field = operation.get("field") or "status"
        if entity.get(field) != operation.get("from"):
            raise ValueError("transition base mismatch for %s.%s" % (operation.get("target_ref"), field))
        document[collection][index][field] = operation.get("to")
        return document
    if op == "upsert":
        collection = operation.get("collection")
        value = operation.get("value")
        if collection not in document or not isinstance(document[collection], list):
            raise ValueError("upsert collection missing: %s" % collection)
        ref = _entity_id(value)
        if not ref: raise ValueError("upsert value requires id")
        for index, item in enumerate(document[collection]):
            if isinstance(item, dict) and _entity_id(item) == ref:
                document[collection][index] = copy.deepcopy(value)
                break
        else:
            document[collection].append(copy.deepcopy(value))
        return document
    raise ValueError("unsupported operation: %s" % op)


def _producer_allowed(producer, filename, operation):
    if producer in ("main", "gate1", "gate2", "human", "migration"):
        return True
    if producer == "task2":
        if filename == "intel-pool.json": return True
        if filename == "customer-value.json":
            path = operation.get("path") or ""
            return path.startswith("/evidence_links") or operation.get("collection") == "evidence_links"
        return False
    if producer == "task2.5":
        return filename in ("customer-value.json", "delivery-plan.json", "strategy.json")
    if producer in ("task3", "task3.5", "redteam"):
        return False
    return False


def _entities_by_id(document, collection):
    return {
        _entity_id(item): item for item in _as_list((document or {}).get(collection))
        if isinstance(item, dict) and _entity_id(item)
    }


def _task25_transition_issues(before, after):
    """Keep selection authority separate from human commitment authority."""
    issues = []

    for filename in ("customer-value.json", "delivery-plan.json", "strategy.json"):
        for collection in ENTITY_COLLECTIONS[filename]:
            old_refs = set(_entities_by_id(before.get(filename), collection))
            new_refs = set(_entities_by_id(after.get(filename), collection))
            for ref in sorted(old_refs - new_refs):
                issues.append("task2.5 cannot delete canonical history %s" % ref)

    for collection in (
            "roles", "needs", "criteria", "role_need_links",
            "need_criterion_links", "role_criterion_links", "evidence_links",
            "role_conflicts"):
        if ((before.get("customer-value.json") or {}).get(collection)
                != (after.get("customer-value.json") or {}).get(collection)):
            issues.append("task2.5 cannot mutate customer semantics collection %s" % collection)

    before_strategy = before.get("strategy.json") or {}
    after_strategy = after.get("strategy.json") or {}
    for field in (
            "title", "bid_type", "depth_mode", "language", "buyer_insight",
            "win_themes", "big_idea", "narrative", "budget_strategy",
            "decision_map"):
        if before_strategy.get(field) != after_strategy.get(field):
            issues.append("task2.5 cannot mutate strategy authority field %s" % field)

    def compare(filename, collection, protected):
        old_items = _entities_by_id(before.get(filename), collection)
        new_items = _entities_by_id(after.get(filename), collection)
        for ref, new in new_items.items():
            old = old_items.get(ref) or {}
            for field, forbidden_new in protected.items():
                old_value = old.get(field)
                new_value = new.get(field)
                if field == "authority_ref":
                    if new_value != old_value and _nonempty(new_value):
                        issues.append("task2.5 cannot add/change authority_ref on %s" % ref)
                elif new_value in forbidden_new and old_value != new_value:
                    issues.append("task2.5 cannot elevate %s.%s to %s" % (ref, field, new_value))

    compare("customer-value.json", "claims", {
        "commitment_level": {"committed"}, "authority_ref": set(),
    })
    compare("customer-value.json", "metrics", {
        "authority_ref": set(),
    })
    compare("delivery-plan.json", "actions", {
        "readiness_status": {"confirmed"}, "commitment_level": {"committed"},
        "authority_ref": set(),
    })
    compare("delivery-plan.json", "resource_envelopes", {
        "status": {"confirmed"}, "authority_ref": set(),
    })
    compare("delivery-plan.json", "acceptance_contracts", {
        "authority_ref": set(),
    })

    old_vps = _entities_by_id(before.get("customer-value.json"), "value_propositions")
    new_vps = _entities_by_id(after.get("customer-value.json"), "value_propositions")
    vp_semantic_fields = (
        "name", "approved_wording", "expected_change", "value_mechanism",
        "relative_advantage", "scope", "value_lens", "role_refs", "need_refs",
        "criterion_refs", "evidence_link_refs", "action_refs",
        "capability_evidence_refs", "authority_refs",
    )
    for ref, new in new_vps.items():
        old = old_vps.get(ref)
        if old is None:
            issues.append("task2.5 cannot create new ValueProposition %s" % ref)
            continue
        changed = [field for field in vp_semantic_fields if old.get(field) != new.get(field)]
        if changed:
            issues.append(
                "task2.5 cannot rewrite ValueProposition semantics on %s: %s"
                % (ref, ", ".join(changed)))

    def freeze_elevated(filename, collection, predicate, fields):
        old_items = _entities_by_id(before.get(filename), collection)
        new_items = _entities_by_id(after.get(filename), collection)
        for ref, old in old_items.items():
            new = new_items.get(ref)
            if not new or not predicate(old):
                continue
            changed = [field for field in fields if old.get(field) != new.get(field)]
            if changed:
                issues.append(
                    "task2.5 cannot alter authorized %s fields on %s: %s"
                    % (collection, ref, ", ".join(changed)))

    freeze_elevated(
        "customer-value.json", "claims",
        lambda item: item.get("commitment_level") == "committed",
        ("proposition", "approved_wording", "content_kind", "epistemic_status",
         "scope", "risk_level", "quantitative", "measurement_required", "metric_refs",
         "action_refs", "value_proposition_refs", "evidence_link_refs", "authority_ref"))
    freeze_elevated(
        "delivery-plan.json", "actions",
        lambda item: (item.get("commitment_level") == "committed"
                      or item.get("readiness_status") == "confirmed"),
        ("name", "approved_wording", "description", "customer_outcome", "phase",
         "time_window", "milestones", "commitment_level", "readiness_status",
         "accountable_role_ref", "responsible_role_refs", "supporting_role_refs",
         "requirement_refs", "value_proposition_refs", "claim_refs", "resource_refs",
         "resource_demands", "resource_treatment", "dependency_refs", "acceptance_refs",
         "authority_ref"))
    freeze_elevated(
        "delivery-plan.json", "resource_envelopes",
        lambda item: item.get("status") == "confirmed",
        ("kind", "name", "unit", "capacity", "time_window", "portfolio_budget",
         "approved_projection", "approved_allocation", "authority_ref"))
    freeze_elevated(
        "delivery-plan.json", "acceptance_contracts",
        lambda item: _nonempty(item.get("authority_ref")),
        ("subject", "criteria", "method", "records", "correction_window",
         "metric_refs", "approver_role_refs", "approved_wording", "authority_ref"))
    freeze_elevated(
        "customer-value.json", "metrics",
        lambda item: _nonempty(item.get("authority_ref")),
        ("name", "definition", "unit", "window", "baseline", "target", "data_source",
         "frequency", "owner_ref", "approved_baseline", "approved_wording", "authority_ref"))

    old_decisions = {
        item.get("id") or item.get("ref") or item.get("title"): item
        for item in _as_list((before.get("strategy.json") or {}).get("open_questions"))
        if isinstance(item, dict) and (item.get("id") or item.get("ref") or item.get("title"))
    }
    for decision in _as_list((after.get("strategy.json") or {}).get("open_questions")):
        if not isinstance(decision, dict):
            continue
        key = decision.get("id") or decision.get("ref") or decision.get("title")
        old = old_decisions.get(key) or {}
        if decision.get("status") in ("resolved", "assumed") and old.get("status") != decision.get("status"):
            issues.append("task2.5 cannot resolve/assume Gate %s" % key)
        if decision.get("resolved") != old.get("resolved") and _nonempty(decision.get("resolved")):
            issues.append("task2.5 cannot write Gate resolution for %s" % key)
        if old.get("status") == "resolved" and decision != old:
            issues.append("task2.5 cannot alter resolved Gate %s" % key)
    return sorted(set(issues))


def apply_changeset(state_dir, changeset_path):
    changeset = _read_json(changeset_path)
    if changeset.get("schema_version") != SCHEMA_VERSIONS["changeset"]:
        return {"passed": False, "issues": ["unsupported changeset schema"]}
    producer = changeset.get("producer")
    if not producer:
        return {"passed": False, "issues": ["changeset producer is required"]}
    documents, issues = load_state(state_dir)
    if issues:
        return {"passed": False, "issues": issues}
    base = changeset.get("base_revisions") or {}
    operations = _as_list(changeset.get("operations"))
    preflight_touched = []
    for operation in operations:
        if not isinstance(operation, dict):
            return {"passed": False, "issues": ["operation must be object"]}
        filename = operation.get("file")
        if filename not in CANONICAL_FILES:
            return {"passed": False, "issues": [
                "operation file is not canonical: %s" % filename
            ]}
        if filename not in preflight_touched:
            preflight_touched.append(filename)
    if not preflight_touched:
        return {"passed": False, "issues": ["changeset has no operations"]}
    for filename in preflight_touched:
        if filename not in base:
            return {"passed": False, "issues": [
                "changeset missing base revision for touched file: %s" % filename
            ], "stale": True}
        if base[filename] != documents[filename].get("revision"):
            return {"passed": False, "issues": ["stale changeset: %s base=%r current=%r" % (filename, base[filename], documents[filename].get("revision"))], "stale": True}

    candidates = copy.deepcopy(documents)
    touched = []
    try:
        for operation in operations:
            if not isinstance(operation, dict): raise ValueError("operation must be object")
            filename = operation.get("file")
            if filename not in CANONICAL_FILES: raise ValueError("operation file is not canonical: %s" % filename)
            if not _producer_allowed(producer, filename, operation):
                raise ValueError("producer %s cannot mutate %s" % (producer, filename))
            candidates[filename] = _apply_operation(candidates[filename], operation)
            if filename not in touched: touched.append(filename)
    except Exception as exc:
        return {"passed": False, "issues": [str(exc)]}

    if producer == "task2.5":
        transition_issues = _task25_transition_issues(documents, candidates)
        if transition_issues:
            return {"passed": False, "issues": transition_issues, "rolled_back": True}

    for filename in touched:
        candidates[filename]["revision"] = documents[filename]["revision"] + 1
        if isinstance(candidates[filename].get("change_log"), list):
            candidates[filename]["change_log"].append({
                "changeset_id": changeset.get("changeset_id"), "producer": producer,
                "rationale": changeset.get("rationale") or "",
                "base_revision": documents[filename]["revision"],
            })

    # Validate the complete candidate state before touching a single live file.
    temp_parent = os.path.dirname(os.path.abspath(state_dir))
    validation_dir = tempfile.mkdtemp(prefix=".proposal-v3-validate-", dir=temp_parent)
    try:
        for filename in CANONICAL_FILES:
            _write_json_atomic(os.path.join(validation_dir, filename), candidates[filename])
        for filename in ("source-manifest.json", "run-manifest.json"):
            source_path = os.path.join(state_dir, filename)
            if os.path.isfile(source_path):
                shutil.copy2(source_path, os.path.join(validation_dir, filename))
        stage = changeset.get("validate_stage") or "draft"
        checked = check_canonical(validation_dir, stage=stage)
    finally:
        shutil.rmtree(validation_dir, ignore_errors=True)
    if not checked["passed"]:
        return {"passed": False, "issues": checked["issues"], "diagnostics": checked["diagnostics"], "rolled_back": True}

    transaction = tempfile.mkdtemp(prefix=".proposal-v3-txn-", dir=state_dir)
    backups = {}
    replaced = []
    try:
        for filename in touched:
            _write_json_atomic(os.path.join(transaction, filename), candidates[filename])
        backup_dir = os.path.join(transaction, "backups")
        os.makedirs(backup_dir)
        for filename in touched:
            live = os.path.join(state_dir, filename)
            backup = os.path.join(backup_dir, filename)
            shutil.copy2(live, backup)
            backups[filename] = backup
        for filename in touched:
            os.replace(os.path.join(transaction, filename), os.path.join(state_dir, filename))
            replaced.append(filename)
    except Exception as exc:
        for filename in reversed(replaced):
            try:
                os.replace(backups[filename], os.path.join(state_dir, filename))
            except Exception:
                pass
        return {"passed": False, "issues": ["transaction failed and was rolled back: %s" % exc], "rolled_back": True}
    finally:
        shutil.rmtree(transaction, ignore_errors=True)

    _invalidate_derived(state_dir, changeset.get("affected_refs") or [], touched)
    receipt = {
        "schema_version": "change-receipt/v1", "changeset_id": changeset.get("changeset_id"),
        "producer": producer, "touched": touched,
        "new_revisions": {name: candidates[name]["revision"] for name in touched},
        "affected_refs": changeset.get("affected_refs") or [],
    }
    receipt_dir = os.path.join(state_dir, "proposals", "changes")
    os.makedirs(receipt_dir, exist_ok=True)
    receipt_name = re.sub(r"[^A-Za-z0-9_.-]", "-", str(changeset.get("changeset_id") or uuid.uuid4().hex)) + ".receipt.json"
    _write_json_atomic(os.path.join(receipt_dir, receipt_name), receipt)
    return {"passed": True, "issues": [], "receipt": receipt, "rolled_back": False}


def promote_research(state_dir, intel_proposal_path, links_proposal_path):
    """Validate Task 2 candidates and promote them through the ChangeSet path."""
    intel_proposal = _read_json(intel_proposal_path)
    links_proposal = _read_json(links_proposal_path)
    if intel_proposal.get("schema_version") != "research-evidence/v1":
        return {"passed": False, "issues": ["intel proposal must be research-evidence/v1"]}
    if links_proposal.get("schema_version") != "research-links/v1":
        return {"passed": False, "issues": ["links proposal must be research-links/v1"]}
    documents, issues = load_state(state_dir)
    if issues:
        return {"passed": False, "issues": issues}
    diagnostics = []
    registry = _build_registry(documents, diagnostics)
    existing_ids = set(registry)
    evidence_candidates = _as_list(intel_proposal.get("evidence_candidates"))
    link_candidates = _as_list(links_proposal.get("link_candidates"))
    new_evidence_ids = set()
    proposal_issues = []
    allowed_visibility = SAFE_PUBLICATION_VISIBILITIES | {"internal", "private", "unknown"}
    for index, evidence in enumerate(evidence_candidates):
        if not isinstance(evidence, dict):
            proposal_issues.append("evidence_candidates[%s] is not object" % index)
            continue
        ref = evidence.get("id")
        if not _nonempty(ref):
            proposal_issues.append("evidence_candidates[%s] missing id" % index)
            continue
        if ref in existing_ids or ref in new_evidence_ids:
            proposal_issues.append("duplicate Evidence id: %s" % ref)
        new_evidence_ids.add(ref)
        if not _nonempty(evidence.get("content")) or not _nonempty(evidence.get("source")):
            proposal_issues.append("%s requires content and source" % ref)
        visibility = evidence.get("visibility")
        if visibility not in allowed_visibility:
            proposal_issues.append("%s invalid visibility=%r" % (ref, visibility))
        if visibility == "public" and not _nonempty(evidence.get("url")):
            proposal_issues.append("%s public Evidence requires a fetched source URL" % ref)
        if ((evidence.get("third_party") is True
             or evidence.get("kind") in ("third_party_case", "buyer_case", "industry_case"))
                and "bidder_capability" in _as_list(evidence.get("allowed_uses"))):
            proposal_issues.append("%s third-party case cannot prove bidder capability" % ref)
        if evidence.get("visibility") == "approved_anonymized" and (
                not _nonempty(evidence.get("safe_title"))
                or not _nonempty(evidence.get("approved_projection"))
                or not _nonempty(evidence.get("publication_authority_ref"))):
            proposal_issues.append(
                "%s approved_anonymized requires safe_title, approved_projection and publication_authority_ref" % ref)
    new_link_ids = set()
    for index, link in enumerate(link_candidates):
        if not isinstance(link, dict):
            proposal_issues.append("link_candidates[%s] is not object" % index)
            continue
        ref = link.get("id")
        if not _nonempty(ref) or ref in existing_ids or ref in new_link_ids:
            proposal_issues.append("invalid or duplicate EvidenceLink id: %r" % ref)
        new_link_ids.add(ref)
        evidence_ref = link.get("evidence_ref")
        if evidence_ref not in existing_ids and evidence_ref not in new_evidence_ids:
            proposal_issues.append("%s references missing Evidence %s" % (ref, evidence_ref))
        target_ref = link.get("target_ref")
        if target_ref not in registry or registry[target_ref]["type"] not in {
                "customer_need", "decision_criterion", "value_proposition", "claim"}:
            proposal_issues.append("%s has invalid target_ref %s" % (ref, target_ref))
        if link.get("relation") not in ("supports", "refutes"):
            proposal_issues.append("%s relation must be supports or refutes" % ref)
        if not link.get("reason"):
            proposal_issues.append("%s requires semantic relevance reason" % ref)
    if proposal_issues:
        return {"passed": False, "issues": proposal_issues}

    base_revisions = {}
    base_revisions.update(intel_proposal.get("base_revisions") or {})
    base_revisions.update(links_proposal.get("base_revisions") or {})
    operations = []
    for evidence in evidence_candidates:
        operations.append({"file": "intel-pool.json", "op": "add", "path": "/evidence/-", "value": evidence})
    promoted_gaps = list(_as_list(intel_proposal.get("gaps")))
    for contradiction in _as_list(links_proposal.get("contradictions")):
        if isinstance(contradiction, dict):
            normalized = copy.deepcopy(contradiction)
            normalized.setdefault("kind", "contradiction")
            normalized.setdefault("next_action", "task2.5")
            promoted_gaps.append(normalized)
    for gap in promoted_gaps:
        operations.append({"file": "intel-pool.json", "op": "add", "path": "/gaps/-", "value": gap})
    for link in link_candidates:
        operations.append({"file": "customer-value.json", "op": "add", "path": "/evidence_links/-", "value": link})
    if not operations:
        return {"passed": False, "issues": ["research proposal has no promotable candidates or gaps"]}
    changeset = {
        "schema_version": SCHEMA_VERSIONS["changeset"],
        "changeset_id": links_proposal.get("changeset_id") or intel_proposal.get("proposal_id") or "CS-T2-RESEARCH",
        "producer": "task2", "base_revisions": base_revisions,
        "rationale": intel_proposal.get("rationale") or "Promote validated Task 2 Evidence and semantic links",
        "validate_stage": "draft", "operations": operations,
        "affected_refs": sorted(new_evidence_ids | set(item.get("target_ref") for item in link_candidates)),
    }
    temp_path = os.path.join(state_dir, "proposals", "changes", ".task2-promote-%s.json" % uuid.uuid4().hex)
    _write_json_atomic(temp_path, changeset)
    try:
        result = apply_changeset(state_dir, temp_path)
    finally:
        try: os.unlink(temp_path)
        except OSError: pass
    if result.get("passed"):
        result["promoted_evidence"] = len(evidence_candidates)
        result["promoted_links"] = len(link_candidates)
    return result


def apply_auto_state(state_dir):
    """Convert open v3 decisions to traceable assumptions through a ChangeSet."""
    documents, issues = load_state(state_dir)
    if issues:
        return {"passed": False, "issues": issues}
    strategy = documents["strategy.json"]
    fog = _as_list((strategy.get("decision_map") or {}).get("not_yet_specified"))
    if fog:
        return {"passed": False, "issues": [
            "not_yet_specified must first be routed to a decision, research gap, or out_of_scope"
        ]}
    decision_operations = []
    pending_updates = {}
    converted = 0
    diagnostics = []
    registry = _build_registry(documents, diagnostics)

    def demote_affected(ref, gate_ref):
        target = registry.get(ref)
        if not target:
            return
        filename = target.get("file")
        collection, index, entity = _find_entity(documents[filename], ref)
        if entity is None:
            return
        key = (filename, collection, index)
        updated = copy.deepcopy(pending_updates.get(key) or entity)
        changed = False
        target_type = target.get("type")
        if target_type == "claim" and updated.get("authority_ref") == gate_ref:
            if updated.get("commitment_level") == "committed":
                updated["commitment_level"] = "intended"; changed = True
            updated["authority_ref"] = None; changed = True
        elif target_type == "delivery_action" and updated.get("authority_ref") == gate_ref:
            if updated.get("commitment_level") == "committed":
                updated["commitment_level"] = "intended"; changed = True
            if updated.get("readiness_status") == "confirmed":
                updated["readiness_status"] = "planned"; changed = True
            updated["authority_ref"] = None; changed = True
        elif target_type == "resource_envelope" and updated.get("authority_ref") == gate_ref:
            if updated.get("status") == "confirmed":
                updated["status"] = "provisional"; changed = True
            updated["authority_ref"] = None; changed = True
        elif target_type in ("acceptance_contract", "metric") \
                and updated.get("authority_ref") == gate_ref:
            updated["authority_ref"] = None; changed = True
        elif target_type == "evidence" \
                and updated.get("publication_authority_ref") == gate_ref:
            updated["visibility"] = "internal"
            updated["publication_authority_ref"] = None
            updated["allowed_uses"] = [
                use for use in _as_list(updated.get("allowed_uses"))
                if use not in ("proposal_narrative", "bidder_capability")
            ]
            changed = True
        if changed:
            pending_updates[key] = updated

    for index, decision in enumerate(_as_list(strategy.get("open_questions"))):
        if not isinstance(decision, dict):
            return {"passed": False, "issues": ["open_questions[%s] is not object" % index]}
        if decision.get("status") != "open":
            continue
        assumption = decision.get("ai_assumption")
        if not _nonempty(assumption):
            return {"passed": False, "issues": [
                "open decision %r has no conservative ai_assumption" % decision.get("title")
            ]}
        updated = copy.deepcopy(decision)
        updated.update(status="assumed", resolved=assumption, assumption_risk=True)
        decision_operations.append({
            "file": "strategy.json", "op": "replace",
            "path": "/open_questions/%s" % index, "value": updated,
        })
        gate_ref = decision.get("id") or decision.get("ref")
        for affected_ref in _ref_list(decision, "affected_refs"):
            demote_affected(affected_ref, gate_ref)
        converted += 1
    if not decision_operations:
        return {"passed": True, "issues": [], "converted": 0}
    operations = list(decision_operations)
    for (filename, collection, index), updated in sorted(pending_updates.items()):
        operations.append({
            "file": filename, "op": "replace",
            "path": "/%s/%s" % (collection, index), "value": updated,
        })
    touched = sorted(set(operation["file"] for operation in operations))
    changeset = {
        "schema_version": SCHEMA_VERSIONS["changeset"],
        "changeset_id": "CS-AUTO-DECISIONS-%s" % (strategy.get("revision") + 1),
        "producer": "main",
        "base_revisions": {filename: documents[filename].get("revision") for filename in touched},
        "rationale": "Apply explicit -auto conservative assumptions without presenting them as confirmed",
        "validate_stage": "draft", "operations": operations,
        "affected_refs": sorted(set(
            [item.get("id") or item.get("ref") or item.get("title")
             for item in strategy.get("open_questions") or []
             if isinstance(item, dict) and item.get("status") == "open"
             and (item.get("id") or item.get("ref") or item.get("title"))]
            + [_entity_id(value) for value in pending_updates.values() if _entity_id(value)]
        )),
    }
    path = os.path.join(state_dir, "proposals", "changes", ".auto-decisions.json")
    _write_json_atomic(path, changeset)
    try:
        result = apply_changeset(state_dir, path)
    finally:
        try: os.unlink(path)
        except OSError: pass
    result["converted"] = converted if result.get("passed") else 0
    result["auto_demoted_refs"] = sorted(
        _entity_id(value) for value in pending_updates.values() if _entity_id(value))
    return result


def _invalidate_derived(state_dir, affected_refs, touched_files):
    manifests_dir = os.path.join(state_dir, "derived", "manifests")
    artifacts_path = os.path.join(manifests_dir, "artifacts.json")
    if not os.path.exists(artifacts_path):
        return
    try:
        artifacts = _read_json(artifacts_path)
    except Exception:
        return
    changed = False
    for item in _as_list(artifacts.get("artifacts")):
        if not isinstance(item, dict): continue
        refs = set(item.get("dependency_refs") or [])
        files = set(item.get("dependency_files") or [])
        if refs.intersection(affected_refs) or files.intersection(touched_files):
            if item.get("status") == "fresh":
                item["status"] = "stale"
                item["stale_reason"] = "canonical dependency changed"
                changed = True
    if changed:
        _write_json_atomic(artifacts_path, artifacts)


def _state_fingerprint(documents):
    revisions = {}
    hashes = {}
    for filename in CANONICAL_FILES:
        key = filename[:-5].replace("-", "_")
        revisions[key] = documents[filename].get("revision")
        hashes[key] = content_hash(documents[filename])
    return revisions, hashes


def freeze_snapshot(state_dir, force=False):
    checked = check_canonical(state_dir, stage="generation", write_derived=True)
    if not checked["passed"]:
        return {"passed": False, "issues": checked["issues"], "diagnostics": checked["diagnostics"]}
    documents, _ = load_state(state_dir)
    revisions, hashes = _state_fingerprint(documents)
    seed = content_hash({"revisions": revisions, "hashes": hashes, "policy": POLICY_VERSION})
    snapshot = {
        "schema_version": SCHEMA_VERSIONS["snapshot"],
        "snapshot_id": "GS-" + seed.split(":", 1)[1][:12].upper(),
        "canonical_revisions": revisions, "canonical_hashes": hashes,
        "gate_state": "generation_ready", "created_for": "task3",
        "policy_version": POLICY_VERSION,
    }
    path = os.path.join(state_dir, "derived", "manifests", "generation-snapshot.json")
    if os.path.exists(path) and not force:
        existing = _read_json(path)
        if existing.get("canonical_hashes") == hashes:
            return {"passed": True, "issues": [], "snapshot": existing, "path": path, "reused": True}
    _write_json_atomic(path, snapshot)
    return {"passed": True, "issues": [], "snapshot": snapshot, "path": path, "reused": False}


def _public_projection(evidence, use="proposal_narrative"):
    if not _evidence_projection_ready(evidence, use):
        return None
    visibility = evidence.get("visibility")
    anonymized = visibility == "approved_anonymized"
    projection = {
        "source_ref": evidence.get("id"), "kind": evidence.get("kind"),
        "title": (evidence.get("safe_title") if anonymized
                  else evidence.get("safe_title") or evidence.get("title")),
        "content": (evidence.get("approved_projection") if anonymized
                    else evidence.get("approved_projection") or evidence.get("content")),
        "source": None if anonymized else evidence.get("source"),
        "observed_at": evidence.get("observed_at"),
        "quality": evidence.get("quality"), "visibility": visibility,
    }
    return {key: value for key, value in projection.items() if value not in (None, "", [])}


def _project(entity, fields):
    if not isinstance(entity, dict):
        return None
    result = {}
    for field in fields:
        value = entity.get(field)
        if value not in (None, "", []):
            result[field] = copy.deepcopy(value)
    return result


def _safe_role(role):
    return _project(role, (
        "id", "name", "customer_label", "approved_projection", "archetypes",
        "decision_concern", "veto_condition_projection",
    ))


def _safe_need(need):
    result = _project(need, ("id", "name", "status"))
    publication = need.get("publication_status")
    if publication == "public_explicit":
        wording = need.get("statement")
    elif publication == "publicly_supportable":
        wording = need.get("approved_projection")
    else:
        wording = None
    if _nonempty(wording):
        result["statement"] = wording
    result["publication_status"] = publication or "internal_only"
    return result


def _safe_criterion(criterion):
    result = _project(criterion, ("id", "name", "status"))
    publication = criterion.get("publication_status")
    if publication == "public_explicit":
        wording = criterion.get("statement")
    elif publication == "publicly_supportable":
        wording = criterion.get("approved_projection")
    else:
        wording = None
    if _nonempty(wording):
        result["statement"] = wording
    result["publication_status"] = publication or "internal_only"
    return result


def _safe_vp(vp):
    return _project(vp, (
        "id", "name", "approved_wording", "value_mechanism", "expected_change",
        "relative_advantage", "value_lens", "scope", "portfolio_role", "status",
        "role_refs", "need_refs", "criterion_refs", "action_refs",
    ))


def _safe_claim(claim):
    result = _project(claim, (
        "id", "content_kind", "epistemic_status", "commitment_level", "status",
        "risk_level", "scope", "measurement_required", "quantitative",
        "value_proposition_refs", "metric_refs", "action_refs",
    ))
    wording = claim.get("approved_wording") or claim.get("proposition")
    if _nonempty(wording):
        result["proposition"] = wording
    return result


def _safe_action(action):
    return _project(action, (
        "id", "name", "approved_wording", "customer_outcome", "description",
        "phase", "time_window", "milestones", "sequence", "commitment_level",
        "readiness_status", "required", "requirement_refs", "value_proposition_refs",
        "claim_refs", "accountable_role_ref", "responsible_role_refs",
        "supporting_role_refs", "resource_refs", "dependency_refs", "acceptance_refs",
    ))


def _safe_delivery_role(role):
    return _project(role, ("id", "name", "customer_label", "scope", "approved_projection"))


def _safe_resource(resource):
    result = _project(resource, (
        "id", "kind", "name", "customer_label", "unit", "time_window",
        "approved_projection", "approved_allocation", "portfolio_budget",
    ))
    # Raw internal capacity/cost is deliberately never sent to a writer.
    return result


def _safe_dependency(dependency):
    return _project(dependency, (
        "id", "input", "needed_by", "delay_impact", "fallback", "escalation_path",
        "approved_wording",
    ))


def _safe_acceptance(acceptance):
    return _project(acceptance, (
        "id", "subject", "criteria", "method", "records", "correction_window",
        "approved_wording",
    ))


def _safe_metric(metric):
    return _project(metric, (
        "id", "name", "definition", "unit", "window", "frequency", "target",
        "approved_baseline", "approved_wording",
    ))


def _safe_requirement(requirement):
    return _project(requirement, (
        "id", "item", "clause", "type", "must", "dimension", "weight", "basis",
        "acceptance_text", "response_constraint",
    ))


def _safe_section(section):
    return _project(section, (
        "id", "n", "title", "sub", "addresses", "narrative_role",
    ))


def _safe_job(job):
    return _project(job, (
        "id", "job_kind", "entry_judgment", "expected_judgment",
        "evidence_burden", "transition", "role_refs", "criterion_refs",
        "value_proposition_refs", "claim_refs", "action_refs",
    ))


def _collect_by_refs(items, refs):
    refs = set(refs)
    return [copy.deepcopy(item) for item in items if isinstance(item, dict) and item.get("id") in refs]


def _brief_common(documents):
    strategy = documents["strategy.json"]
    decisions = []
    for decision in _as_list(strategy.get("open_questions")):
        if not isinstance(decision, dict) or decision.get("status") not in ("resolved", "assumed"):
            continue
        safe_constraint = decision.get("safe_constraint")
        if not _nonempty(safe_constraint):
            safe_constraint = (
                "Treat as an unconfirmed internal boundary; do not state it as fact or commitment."
                if decision.get("status") == "assumed"
                else "Use only the approved canonical projections affected by this decision; never reveal the raw answer."
            )
        decisions.append({
            "source_ref": decision.get("id") or decision.get("ref"),
            "status": decision.get("status"),
            "boundary": safe_constraint,
            "assumption_risk": bool(decision.get("assumption_risk")),
        })
    safe_out_of_scope = []
    for item in _as_list((strategy.get("decision_map") or {}).get("out_of_scope")):
        if isinstance(item, str):
            safe_out_of_scope.append({"boundary": item})
            continue
        if not isinstance(item, dict):
            continue
        if item.get("visibility") in ("private", "internal"):
            boundary = (item.get("safe_constraint") or item.get("approved_projection")
                        or "Respect an internal scope boundary; do not infer or disclose its reason.")
        else:
            boundary = item.get("approved_projection") or item.get("item")
        safe_out_of_scope.append({
            key: value for key, value in {
                "boundary": boundary,
                "forbidden_terms": copy.deepcopy(item.get("forbidden_terms") or []),
            }.items() if value not in (None, "", [])
        })
    return {
        "destination": (strategy.get("decision_map") or {}).get("destination"),
        "narrative": copy.deepcopy(strategy.get("narrative") or {}),
        "big_idea": strategy.get("big_idea"),
        "decision_boundaries": decisions,
        "out_of_scope": safe_out_of_scope,
        "global_forbidden": [
            "canonical IDs in customer-visible text", "raw URLs", "private source wording",
            "assumptions presented as facts", "commitment stronger than canonical",
            "internal scoring or narrative labels", "sales CTA",
        ],
    }


def _compile_research(documents):
    cv = documents["customer-value.json"]
    intel = documents["intel-pool.json"]
    linked_targets = set(item.get("target_ref") for item in _as_list(cv.get("evidence_links")) if isinstance(item, dict) and item.get("relation", "supports") == "supports")
    gaps = []
    for collection in ("needs", "criteria", "value_propositions", "claims"):
        for item in _as_list(cv.get(collection)):
            if not isinstance(item, dict) or not item.get("id"): continue
            relevant = item.get("status") in ("active", "candidate", "investigating", "qualified", "selected", "draft_ready", "publishable")
            if relevant and item["id"] not in linked_targets:
                gaps.append({"source_ref": item["id"], "kind": collection, "evidence_burden": item.get("evidence_burden") or "establish relevance, authority, scope, freshness and counter-evidence"})
    existing = []
    for evidence in _as_list(intel.get("evidence")):
        if not isinstance(evidence, dict): continue
        projection = _public_projection(evidence)
        if projection: existing.append(projection)
    return {
        "must_use": {"evidence_gaps": gaps, "public_existing_evidence": existing},
        "may_use": {"candidate_value_propositions": [copy.deepcopy(item) for item in _as_list(cv.get("value_propositions")) if isinstance(item, dict) and item.get("status") in ("candidate", "investigating", "qualified")]},
        "forbidden": {"private_query_content": [item.get("id") for item in _as_list(intel.get("evidence")) if isinstance(item, dict) and item.get("visibility") not in SAFE_PUBLICATION_VISIBILITIES]},
        "expected_outputs": ["proposals/task2.intel.json", "proposals/task2.links.json"],
    }


def _compile_value_selection(documents):
    cv = documents["customer-value.json"]
    delivery = documents["delivery-plan.json"]
    intel = documents["intel-pool.json"]
    evidence = []
    for item in _as_list(intel.get("evidence")):
        if not isinstance(item, dict): continue
        evidence.append({
            "source_ref": item.get("id"), "kind": item.get("kind"),
            "content": item.get("approved_projection") or item.get("content"),
            "visibility": item.get("visibility"), "quality": item.get("quality"),
            "status": item.get("status"),
        })
    return {
        "must_use": {
            "roles": copy.deepcopy(_as_list(cv.get("roles"))),
            "needs": copy.deepcopy(_as_list(cv.get("needs"))),
            "criteria": copy.deepcopy(_as_list(cv.get("criteria"))),
            "role_need_links": copy.deepcopy(_as_list(cv.get("role_need_links"))),
            "need_criterion_links": copy.deepcopy(_as_list(cv.get("need_criterion_links"))),
            "value_propositions": [copy.deepcopy(item) for item in _as_list(cv.get("value_propositions")) if isinstance(item, dict) and item.get("status") in ("candidate", "investigating", "qualified", "selected")],
            "evidence_links": copy.deepcopy(_as_list(cv.get("evidence_links"))),
            "evidence": evidence,
            "capability_and_resources": copy.deepcopy(_as_list(delivery.get("resource_envelopes"))),
            "candidate_actions": [copy.deepcopy(item) for item in _as_list(delivery.get("actions")) if isinstance(item, dict) and item.get("selection_status") in ("candidate", "selected")],
        },
        "may_use": {"role_conflicts": copy.deepcopy(_as_list(cv.get("role_conflicts")))},
        "forbidden": {"selection_rules": ["do not reward idea count", "do not publish private raw wording", "do not upgrade unknown capability or authority"]},
        "expected_outputs": ["one changeset/v1 produced by task2.5"],
    }


def _compile_section(documents, section_id):
    req = documents["requirements.json"]
    cv = documents["customer-value.json"]
    delivery = documents["delivery-plan.json"]
    strategy = documents["strategy.json"]
    intel = documents["intel-pool.json"]
    sections = [item for item in _as_list(strategy.get("sections")) if isinstance(item, dict)]
    section = next((item for item in sections if item.get("id") == section_id or str(item.get("n")) == str(section_id)), None)
    if not section:
        raise ValueError("section not found: %s" % section_id)
    section_ref = section.get("id")
    job_refs = _ref_list(section, "primary_decision_job_ref", "secondary_decision_job_ref")
    jobs = _collect_by_refs(_as_list(strategy.get("decision_jobs")), job_refs)
    role_refs, criterion_refs, vp_refs, claim_refs, action_refs = set(), set(), set(), set(), set()
    for job in jobs:
        role_refs.update(_ref_list(job, "role_refs")); criterion_refs.update(_ref_list(job, "criterion_refs"))
        vp_refs.update(_ref_list(job, "value_proposition_refs")); claim_refs.update(_ref_list(job, "claim_refs")); action_refs.update(_ref_list(job, "action_refs"))
    claims = _collect_by_refs(_as_list(cv.get("claims")), claim_refs)
    for claim in claims:
        vp_refs.update(_ref_list(claim, "value_proposition_refs")); action_refs.update(_ref_list(claim, "action_refs"))
    vps = _collect_by_refs(_as_list(cv.get("value_propositions")), vp_refs)
    need_refs = set()
    for vp in vps:
        role_refs.update(_ref_list(vp, "role_refs")); criterion_refs.update(_ref_list(vp, "criterion_refs")); need_refs.update(_ref_list(vp, "need_refs")); action_refs.update(_ref_list(vp, "action_refs"))
    actions = _collect_by_refs(_as_list(delivery.get("actions")), action_refs)
    delivery_role_refs, resource_refs, dependency_refs, acceptance_refs, metric_refs = set(), set(), set(), set(), set()
    for claim in claims: metric_refs.update(_ref_list(claim, "metric_refs"))
    for action in actions:
        delivery_role_refs.update(_ref_list(action, "accountable_role_ref", "responsible_role_refs", "supporting_role_refs"))
        resource_refs.update(_ref_list(action, "resource_refs")); dependency_refs.update(_ref_list(action, "dependency_refs")); acceptance_refs.update(_ref_list(action, "acceptance_refs"))
        for demand in _as_list(action.get("resource_demands")):
            if isinstance(demand, dict) and demand.get("resource_ref"): resource_refs.add(demand["resource_ref"])
    for acceptance in _collect_by_refs(_as_list(delivery.get("acceptance_contracts")), acceptance_refs): metric_refs.update(_ref_list(acceptance, "metric_refs"))

    evidence_targets = set()
    for item in claims + vps + _collect_by_refs(_as_list(cv.get("needs")), need_refs) + _collect_by_refs(_as_list(cv.get("criteria")), criterion_refs):
        if item.get("id"): evidence_targets.add(item["id"])
    links = [
        item for item in _as_list(cv.get("evidence_links"))
        if isinstance(item, dict) and item.get("target_ref") in evidence_targets
    ]
    evidence_by_ref = {
        item.get("id"): item for item in _as_list(intel.get("evidence"))
        if isinstance(item, dict) and item.get("id")
    }
    target_by_ref = {
        item.get("id"): item
        for item in claims + vps
        + _collect_by_refs(_as_list(cv.get("needs")), need_refs)
        + _collect_by_refs(_as_list(cv.get("criteria")), criterion_refs)
        if isinstance(item, dict) and item.get("id")
    }
    public_evidence = []
    counter_evidence = []
    private_refs = []
    for link in links:
        evidence = evidence_by_ref.get(link.get("evidence_ref")) or {}
        projection = _public_projection(evidence)
        if not projection:
            private_refs.append(evidence.get("id") or link.get("evidence_ref"))
            continue
        link_projection = dict(projection)
        link_projection.update({
            "link_ref": link.get("id"), "target_ref": link.get("target_ref"),
            "relation": link.get("relation"), "strength": link.get("strength"),
            "support_scope": link.get("scope"), "relevance_reason": link.get("reason"),
        })
        if link.get("relation", "supports") == "supports":
            target = target_by_ref.get(link.get("target_ref")) or {}
            if _evidence_support_usable(
                    link, evidence, target.get("risk_level") or "medium"):
                public_evidence.append(link_projection)
        elif link.get("relation") == "refutes" and _evidence_is_current(evidence):
            counter_evidence.append(link_projection)
    requirement_refs = _ref_list(section, "addresses")
    requirements = []
    for collection in ("mandatory", "scoring", "deliverables"):
        requirements.extend(
            _safe_requirement(item)
            for item in _collect_by_refs(_as_list(req.get(collection)), requirement_refs)
        )
    publishable_claims = [item for item in claims if item.get("status") == "publishable"]
    selected_vps = [item for item in vps if item.get("status") in ("selected", "publishable")]
    selected_actions = [item for item in actions if item.get("selection_status") == "selected"]
    safe_needs = [_safe_need(item) for item in _collect_by_refs(_as_list(cv.get("needs")), need_refs)]
    safe_criteria = [_safe_criterion(item) for item in _collect_by_refs(_as_list(cv.get("criteria")), criterion_refs)]
    private_refs.extend(
        item.get("id") for item in safe_needs + safe_criteria
        if item and item.get("publication_status") == "internal_only")
    return {
        "section_ref": section_ref,
        "must_use": {
            "section": _safe_section(section), "requirements": requirements,
            "decision_jobs": [_safe_job(item) for item in jobs],
            "customer_roles": [_safe_role(item) for item in _collect_by_refs(_as_list(cv.get("roles")), role_refs)],
            "customer_needs": safe_needs,
            "decision_criteria": safe_criteria,
            "value_propositions": [_safe_vp(item) for item in selected_vps],
            "claims": [_safe_claim(item) for item in publishable_claims],
            "actions": [_safe_action(item) for item in selected_actions],
            "delivery_roles": [_safe_delivery_role(item) for item in _collect_by_refs(_as_list(delivery.get("delivery_roles")), delivery_role_refs)],
            "resources": [_safe_resource(item) for item in _collect_by_refs(_as_list(delivery.get("resource_envelopes")), resource_refs)],
            "customer_dependencies": [_safe_dependency(item) for item in _collect_by_refs(_as_list(delivery.get("customer_dependencies")), dependency_refs)],
            "acceptance_contracts": [_safe_acceptance(item) for item in _collect_by_refs(_as_list(delivery.get("acceptance_contracts")), acceptance_refs)],
            "metrics": [_safe_metric(item) for item in _collect_by_refs(_as_list(cv.get("metrics")), metric_refs)],
            "public_evidence": public_evidence,
            "counter_evidence_constraints": counter_evidence,
        },
        "may_use": {},
        "forbidden": {"private_evidence_refs": private_refs, "canonical_mutation": True},
        "expected_outputs": ["sections/section-%s.md" % section.get("n"), "proposed realization hints with canonical_ref/contribution/quote"],
        "expected_realization_refs": [item.get("id") for item in publishable_claims + selected_actions if item.get("id")],
        "expected_requirement_refs": sorted(requirement_refs),
    }


def _compile_exec_summary(documents, state_dir):
    cv = documents["customer-value.json"]
    delivery = documents["delivery-plan.json"]
    intel = documents["intel-pool.json"]
    formal_diagnostics = _realization_diagnostics(
        state_dir, documents, os.path.join(state_dir, "derived", "realization"),
        include_summary=False)
    blocking = [
        item for item in formal_diagnostics
        if item.get("severity") in ("fatal", "blocker")
    ]
    if blocking:
        raise ValueError(
            "exec-summary requires all formal sections and Requirement responses to be valid: %s"
            % "; ".join(item.get("observed", "") for item in blocking[:5]))
    realized = set()
    anchors = []
    realization_dir = os.path.join(state_dir, "derived", "realization")
    manifests, _ = _authoritative_realization_manifests(realization_dir)
    for manifest in manifests.values():
        if manifest.get("section_ref") in ("CH-00", "section-0", "0"):
            continue
        if manifest.get("status") != "valid":
            continue
        for item in _as_list(manifest.get("realizations")):
            if isinstance(item, dict) and item.get("semantic_status") == "entailed" and item.get("canonical_ref"):
                realized.add(item["canonical_ref"])
                anchors.append({"source_ref": item["canonical_ref"], "section_ref": manifest.get("section_ref"), "anchors": item.get("anchors") or []})
    claims = _collect_by_refs(_as_list(cv.get("claims")), realized)
    actions = _collect_by_refs(_as_list(delivery.get("actions")), realized)
    vp_refs = set()
    for claim in claims: vp_refs.update(_ref_list(claim, "value_proposition_refs"))
    vps = _collect_by_refs(_as_list(cv.get("value_propositions")), vp_refs)
    evidence_by_ref = {
        item.get("id"): item for item in _as_list(intel.get("evidence"))
        if isinstance(item, dict) and item.get("id")
    }
    claims_by_ref = {item.get("id"): item for item in claims if item.get("id")}
    evidence = []
    counter_constraints = []
    for link in _as_list(cv.get("evidence_links")):
        if not isinstance(link, dict) or link.get("target_ref") not in claims_by_ref:
            continue
        source = evidence_by_ref.get(link.get("evidence_ref")) or {}
        projection = _public_projection(source)
        if link.get("relation", "supports") == "supports":
            claim = claims_by_ref[link.get("target_ref")]
            if projection and _evidence_support_usable(
                    link, source, claim.get("risk_level") or "medium",
                    _claim_proof_task(claim)):
                item = dict(projection)
                item.update({
                    "link_ref": link.get("id"), "target_ref": link.get("target_ref"),
                    "scope": link.get("scope"), "reason": link.get("reason"),
                    "strength": link.get("strength"),
                })
                evidence.append(item)
        elif link.get("relation") == "refutes" and _evidence_is_current(source):
            counter_constraints.append({
                "target_ref": link.get("target_ref"),
                "constraint": link.get("safe_constraint") or link.get("reason")
                or "Do not state this Claim beyond its approved scope.",
            })
    return {
        "must_use": {
            "realized_claims": [_safe_claim(item) for item in claims],
            "realized_actions": [_safe_action(item) for item in actions],
            "realized_value_propositions": [_safe_vp(item) for item in vps],
            "public_evidence": evidence,
            "counter_evidence_constraints": counter_constraints,
            "source_anchors": anchors,
        },
        "may_use": {},
        "forbidden": {"not_realized_refs": "all canonical refs outside this whitelist", "new_or_stronger_claims": True},
        "expected_outputs": ["sections/section-0.md", "summary realization hints using whitelist only"],
        "allowed_realization_refs": sorted(realized),
    }


def _compile_redteam(documents, role, state_dir):
    checked = check_canonical(state_dir, stage="submission", realization_dir=os.path.join(state_dir, "derived", "realization"))
    return {
        "must_use": {
            "audit_role": role,
            "requirements": copy.deepcopy(documents["requirements.json"]),
            "canonical_gate_summary": checked["counts"],
            "root_diagnostics": checked["diagnostics"],
        },
        "may_use": {},
        "forbidden": {"private_raw_graph": True, "direct_canonical_mutation": True, "automatic_waiver": True},
        "expected_outputs": ["root diagnostic proposals with observed/reason/confidence/source anchors"],
    }


def _register_artifact(state_dir, artifact):
    path = os.path.join(state_dir, "derived", "manifests", "artifacts.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        try: manifest = _read_json(path)
        except Exception: manifest = {"schema_version": "artifact-manifest/v1", "artifacts": []}
    else:
        manifest = {"schema_version": "artifact-manifest/v1", "artifacts": []}
    items = [item for item in _as_list(manifest.get("artifacts")) if not (isinstance(item, dict) and item.get("artifact_id") == artifact.get("artifact_id"))]
    items.append(artifact)
    manifest["artifacts"] = items
    _write_json_atomic(path, manifest)


def compile_context(state_dir, target, target_id=None, role=None, output_path=None,
                    token_budget=24000):
    if target not in ("research", "value-selection", "section", "exec-summary", "redteam"):
        return {"passed": False, "issues": ["unsupported context target"]}
    required_stage = "generation" if target in ("section", "exec-summary", "redteam") else "draft"
    checked = check_canonical(state_dir, stage=required_stage, write_derived=True)
    if not checked["passed"]:
        return {"passed": False, "issues": checked["issues"], "diagnostics": checked["diagnostics"]}
    documents, _ = load_state(state_dir)
    snapshot = None
    if target in ("section", "exec-summary", "redteam"):
        frozen = freeze_snapshot(state_dir)
        if not frozen["passed"]: return frozen
        snapshot = frozen["snapshot"]
    try:
        if target == "research": payload = _compile_research(documents)
        elif target == "value-selection": payload = _compile_value_selection(documents)
        elif target == "section":
            if target_id is None: raise ValueError("section target requires --id")
            payload = _compile_section(documents, target_id)
        elif target == "exec-summary": payload = _compile_exec_summary(documents, state_dir)
        else:
            if not role: raise ValueError("redteam target requires --role")
            payload = _compile_redteam(documents, role, state_dir)
    except ValueError as exc:
        return {"passed": False, "issues": [str(exc)]}

    revisions, hashes = _state_fingerprint(documents)
    brief = {
        "brief_schema_version": SCHEMA_VERSIONS["brief"],
        "target": target, "target_id": target_id or role,
        "generation_snapshot_id": snapshot.get("snapshot_id") if snapshot else None,
        "input_revisions": revisions, "input_hashes": hashes,
        "compiler_version": ENGINE_VERSION, "context_policy_version": CONTEXT_POLICY_VERSION,
        "common": _brief_common(documents),
        "must_use": payload.get("must_use") or {}, "may_use": payload.get("may_use") or {},
        "forbidden": payload.get("forbidden") or {},
        "expected_outputs": payload.get("expected_outputs") or [],
        "expected_realization_refs": payload.get("expected_realization_refs") or [],
        "expected_requirement_refs": payload.get("expected_requirement_refs") or [],
        "allowed_realization_refs": payload.get("allowed_realization_refs") or [],
        "token_budget": token_budget, "pruning_log": [], "status": "fresh",
    }
    estimated = max(1, len(_canonical_json(brief)) // 4)
    brief["estimated_tokens"] = estimated
    if estimated > token_budget:
        # Required context is never silently removed. Only may_use can be pruned.
        if brief["may_use"]:
            brief["pruning_log"].append({"removed": "may_use", "reason": "token_budget"})
            brief["may_use"] = {}
            estimated = max(1, len(_canonical_json(brief)) // 4)
            brief["estimated_tokens"] = estimated
        if estimated > token_budget:
            brief["status"] = "blocked"
            brief["overflow"] = {"estimated_tokens": estimated, "token_budget": token_budget, "action": "split the task or raise an explicit budget"}
    brief["brief_hash"] = content_hash({key: value for key, value in brief.items() if key != "brief_hash"})

    if output_path is None:
        if target == "section":
            safe_target = re.sub(r"[^A-Za-z0-9_.-]", "-", str(payload.get("section_ref", target_id)))
            output_path = os.path.join(state_dir, "derived", "briefs", "sections", "%s.json" % safe_target)
        elif target == "redteam":
            safe_role = re.sub(r"[^A-Za-z0-9_.-]", "-", str(role))
            output_path = os.path.join(state_dir, "derived", "briefs", "redteam", "%s.json" % safe_role)
        else: output_path = os.path.join(state_dir, "derived", "briefs", "%s.json" % target)
    _write_json_atomic(output_path, brief)
    dependency_refs = []
    for ref in re.findall(r'"(?:[A-Z][A-Z0-9_]*-[A-Z0-9_.-]+)"', _canonical_json(brief.get("must_use"))):
        dependency_refs.append(ref.strip('"'))
    _register_artifact(state_dir, {
        "artifact_id": "brief:%s:%s" % (target, target_id or role or "default"),
        "kind": "context_brief", "path": os.path.abspath(output_path),
        "output_hash": file_hash(output_path), "status": brief["status"],
        "dependency_refs": sorted(set(dependency_refs)),
        "dependency_files": list(CANONICAL_FILES),
        "input_hashes": hashes, "snapshot_id": brief.get("generation_snapshot_id"),
        "policy_version": CONTEXT_POLICY_VERSION,
    })
    return {"passed": brief["status"] == "fresh", "issues": [] if brief["status"] == "fresh" else ["required context exceeds token budget"], "brief": brief, "output_path": os.path.abspath(output_path)}


def _paragraphs(markdown):
    headings = []
    paragraphs = []
    buffer = []

    def flush():
        if buffer:
            text = "\n".join(buffer).strip()
            if text:
                paragraphs.append({"heading_path": list(headings), "text": text})
            del buffer[:]

    for line in markdown.splitlines():
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            flush()
            level = len(match.group(1))
            headings[:] = headings[:level - 1]
            while len(headings) < level - 1: headings.append("")
            headings.append(match.group(2))
        elif not line.strip():
            flush()
        else:
            buffer.append(line)
    flush()
    for index, paragraph in enumerate(paragraphs, 1):
        paragraph["paragraph_id"] = "P-%04d" % index
        paragraph["fingerprint"] = content_hash(re.sub(r"\s+", " ", paragraph["text"]).strip())
    return paragraphs


def _expected_snapshot_id(documents):
    revisions, hashes = _state_fingerprint(documents)
    seed = content_hash({"revisions": revisions, "hashes": hashes, "policy": POLICY_VERSION})
    return "GS-" + seed.split(":", 1)[1][:12].upper(), revisions, hashes


def _brief_integrity_issues(state_dir, brief_path, brief, section_ref, documents):
    issues = []
    is_summary = section_ref in ("CH-00", "section-0", "0")
    expected_target = "exec-summary" if is_summary else "section"
    if brief.get("brief_schema_version") != SCHEMA_VERSIONS["brief"]:
        issues.append("brief schema_version is not context-brief/v1")
    if brief.get("target") != expected_target:
        issues.append("brief target does not match %s" % section_ref)
    if not is_summary and brief.get("target_id") != section_ref:
        issues.append("brief target_id does not match section_ref")
    if brief.get("status") != "fresh":
        issues.append("brief is not fresh")
    expected_hash = content_hash({key: value for key, value in brief.items() if key != "brief_hash"})
    if brief.get("brief_hash") != expected_hash:
        issues.append("brief_hash does not match brief content")
    expected_snapshot, revisions, hashes = _expected_snapshot_id(documents)
    if brief.get("generation_snapshot_id") != expected_snapshot:
        issues.append("brief snapshot does not match current canonical state")
    if brief.get("input_revisions") != revisions or brief.get("input_hashes") != hashes:
        issues.append("brief input fingerprint does not match current canonical state")

    artifacts_path = os.path.join(state_dir, "derived", "manifests", "artifacts.json")
    artifact_id = "brief:%s:%s" % (
        expected_target, "default" if is_summary else section_ref)
    artifact = None
    if os.path.isfile(artifacts_path):
        try:
            artifacts = _read_json(artifacts_path)
            artifact = next((
                item for item in _as_list(artifacts.get("artifacts"))
                if isinstance(item, dict) and item.get("artifact_id") == artifact_id
            ), None)
        except Exception as exc:
            issues.append("artifact registry cannot be read: %s" % exc)
    if not artifact:
        issues.append("compiled brief is not registered as %s" % artifact_id)
    else:
        if os.path.abspath(artifact.get("path") or "") != os.path.abspath(brief_path):
            issues.append("registered brief path does not match supplied brief")
        if artifact.get("status") != "fresh":
            issues.append("registered brief artifact is stale/blocked")
        if artifact.get("output_hash") != file_hash(brief_path):
            issues.append("registered brief hash does not match supplied brief")
        if artifact.get("snapshot_id") != expected_snapshot:
            issues.append("registered brief snapshot is stale")
    return issues, artifact_id


def audit_realization(state_dir, section_ref, section_path, hints_path,
                      brief_path=None, semantic_path=None, output_path=None):
    documents, issues = load_state(state_dir)
    if issues:
        return {"passed": False, "issues": issues}
    if not brief_path or not os.path.isfile(brief_path):
        return {"passed": False, "issues": ["a current compiled --brief is required"]}
    if not os.path.isfile(section_path) or not os.path.isfile(hints_path):
        return {"passed": False, "issues": ["section and realization hints must exist"]}
    markdown = _read_text(section_path)
    hints_doc = _read_json(hints_path)
    if not isinstance(hints_doc, dict):
        return {"passed": False, "issues": ["realization hints must be realization-hints/v1 object"]}
    hints = hints_doc.get("realizations")
    if not isinstance(hints, list):
        return {"passed": False, "issues": ["realization hints must contain realizations array"]}
    brief = _read_json(brief_path)
    semantic = _read_json(semantic_path) if semantic_path else {}
    semantic_items = semantic.get("evaluations") if isinstance(semantic, dict) else []
    semantic_by_ref = {}
    expected = set(brief.get("expected_realization_refs") or [])
    expected_requirements = set(brief.get("expected_requirement_refs") or [])
    allowed = set(brief.get("allowed_realization_refs") or expected)
    public_evidence_by_target = {}
    for item in _as_list((brief.get("must_use") or {}).get("public_evidence")):
        if isinstance(item, dict) and item.get("target_ref") and item.get("source_ref"):
            public_evidence_by_target.setdefault(item.get("target_ref"), set()).add(item.get("source_ref"))
    is_summary = section_ref in ("CH-00", "section-0", "0")
    paragraphs = _paragraphs(markdown)
    registry_diagnostics = []
    registry = _build_registry(documents, registry_diagnostics)
    realizations = []
    requirement_realizations = []
    unexpected_refs = []
    seen = set()
    issues = [item["observed"] for item in registry_diagnostics if item["severity"] == "fatal"]
    brief_issues, brief_artifact_id = _brief_integrity_issues(
        state_dir, brief_path, brief, section_ref, documents)
    issues.extend(brief_issues)

    if hints_doc.get("schema_version") != "realization-hints/v1":
        issues.append("writer hints schema_version is not realization-hints/v1")
    if hints_doc.get("section_ref") != section_ref:
        issues.append("writer hints section_ref does not match")
    if hints_doc.get("snapshot_id") != brief.get("generation_snapshot_id"):
        issues.append("writer hints snapshot does not match brief")
    if hints_doc.get("brief_hash") != brief.get("brief_hash"):
        issues.append("writer hints brief_hash does not match brief")
    for observation in _as_list(hints_doc.get("observations")):
        if isinstance(observation, dict) and observation.get("kind") in (
                "missing_context", "claim_change_proposal", "evidence_gap",
                "resource_gap", "acceptance_gap", "placeholder"):
            issues.append("writer reported unresolved %s: %s" % (
                observation.get("kind"), observation.get("observed") or "no detail"))
    if semantic_path:
        if semantic.get("schema_version") != "semantic-realization/v1":
            issues.append("semantic audit schema_version is not semantic-realization/v1")
        if semantic.get("section_ref") != section_ref:
            issues.append("semantic audit section_ref does not match")
        if semantic.get("snapshot_id") != brief.get("generation_snapshot_id"):
            issues.append("semantic audit snapshot does not match brief")
        if semantic.get("brief_hash") != brief.get("brief_hash"):
            issues.append("semantic audit brief_hash does not match brief")
        if not _nonempty(semantic.get("evaluator")):
            issues.append("semantic audit evaluator is required")
        if semantic.get("overall") not in ("valid", "repair_required", "needs_review"):
            issues.append("semantic audit overall is required")
        elif semantic.get("overall") != "valid":
            issues.append("semantic audit overall=%s" % semantic.get("overall"))
        if not isinstance(semantic_items, list):
            issues.append("semantic audit evaluations must be an array")
            semantic_items = []
        for evaluation in semantic_items:
            if not isinstance(evaluation, dict) or not evaluation.get("canonical_ref"):
                issues.append("semantic evaluation requires canonical_ref")
                continue
            ref = evaluation.get("canonical_ref")
            if ref in semantic_by_ref:
                issues.append("duplicate semantic evaluation for %s" % ref)
            semantic_by_ref[ref] = evaluation

    def locate_quote(ref, quote, label):
        normalized_quote = re.sub(r"\s+", " ", quote or "").strip()
        if not normalized_quote:
            issues.append("%s %s has no quote" % (label, ref))
            return []
        matches = []
        for paragraph in paragraphs:
            normalized_text = re.sub(r"\s+", " ", paragraph["text"]).strip()
            if normalized_quote in normalized_text:
                matches.append(paragraph)
        if len(matches) != 1:
            issues.append("%s %s quote %s" % (
                label, ref, "not found" if not matches else "is not unique"))
            return []
        item = matches[0]
        return [{
            "heading_path": item["heading_path"], "paragraph_id": item["paragraph_id"],
            "quote": quote, "fingerprint": item["fingerprint"],
        }]

    hinted_refs = set()
    for hint in hints:
        if not isinstance(hint, dict):
            issues.append("realization hint is not object")
            continue
        ref = hint.get("canonical_ref")
        contribution = hint.get("contribution")
        if not ref or ref not in registry:
            issues.append("unknown canonical_ref: %s" % ref)
            continue
        if contribution not in CONTRIBUTIONS:
            issues.append("invalid contribution for %s" % ref)
            continue
        if ref in hinted_refs:
            issues.append("duplicate realization hint for %s" % ref)
            continue
        hinted_refs.add(ref)
        if ref not in allowed:
            unexpected_refs.append(ref)
        anchors = locate_quote(ref, hint.get("quote"), "canonical")
        evaluation = semantic_by_ref.get(ref) or {}
        semantic_status = evaluation.get("semantic_status") or "pending_semantic_review"
        if semantic_status not in (
                "entailed", "partial", "contradicted", "overstated", "not_found",
                "needs_review", "pending_semantic_review"):
            issues.append("invalid semantic_status for %s" % ref)
        confidence = evaluation.get("confidence") or "unknown"
        observed_commitment = evaluation.get("observed_commitment_level")
        canonical = registry[ref]["entity"]
        canonical_commitment = canonical.get("commitment_level")
        strength_order = {"none": 0, "intended": 1, "committed": 2}
        if observed_commitment in strength_order and canonical_commitment in strength_order and strength_order[observed_commitment] > strength_order[canonical_commitment]:
            semantic_status = "overstated"
        presented_evidence = set(_ref_list(evaluation, "evidence_refs_presented"))
        unapproved_evidence = presented_evidence - public_evidence_by_target.get(ref, set())
        if unapproved_evidence:
            issues.append("%s presents Evidence outside its public scoped brief: %s" % (
                ref, ", ".join(sorted(unapproved_evidence))))
        if (registry[ref]["type"] == "claim"
                and canonical.get("content_kind") in ("fact", "insight", "target")
                and semantic_status == "entailed"
                and not presented_evidence.intersection(public_evidence_by_target.get(ref, set()))):
            issues.append("%s factual/insight/target realization presents no approved scoped Evidence" % ref)
        realizations.append({
            "canonical_ref": ref, "kind": registry[ref]["type"],
            "contribution": contribution, "anchors": anchors,
            "observed_scope": evaluation.get("observed_scope"),
            "observed_commitment_level": observed_commitment,
            "evidence_refs_presented": sorted(presented_evidence),
            "semantic_status": semantic_status, "reason": evaluation.get("reason"),
            "confidence": confidence,
            "evaluator": semantic.get("evaluator") if isinstance(semantic, dict) else None,
        })
        if anchors and semantic_status == "entailed": seen.add(ref)

    if semantic_path:
        for ref in semantic_by_ref:
            if ref not in hinted_refs:
                issues.append("semantic evaluation %s has no writer hint" % ref)

    requirement_by_ref = {}
    requirement_items = semantic.get("requirement_evaluations") if semantic_path else []
    if semantic_path and not isinstance(requirement_items, list):
        issues.append("semantic requirement_evaluations must be an array")
        requirement_items = []
    for evaluation in _as_list(requirement_items):
        if not isinstance(evaluation, dict) or not evaluation.get("requirement_ref"):
            issues.append("requirement evaluation requires requirement_ref")
            continue
        ref = evaluation.get("requirement_ref")
        if ref in requirement_by_ref:
            issues.append("duplicate requirement evaluation for %s" % ref)
            continue
        requirement_by_ref[ref] = evaluation
        if ref not in expected_requirements:
            issues.append("unexpected requirement evaluation for %s" % ref)
        status_value = evaluation.get("status")
        if status_value not in ("addressed", "partial", "missing", "contradicted"):
            issues.append("invalid requirement realization status for %s" % ref)
        if not _nonempty(evaluation.get("reason")):
            issues.append("requirement evaluation %s has no reason" % ref)
        if evaluation.get("confidence") not in ("high", "medium", "low"):
            issues.append("requirement evaluation %s has invalid confidence" % ref)
        anchors = []
        if status_value != "missing":
            anchors = locate_quote(ref, evaluation.get("quote"), "requirement")
        requirement_realizations.append({
            "requirement_ref": ref, "status": status_value,
            "anchors": anchors, "reason": evaluation.get("reason"),
            "confidence": evaluation.get("confidence"),
        })

    missing = sorted(expected - seen)
    missing_requirement_evaluations = sorted(expected_requirements - set(requirement_by_ref))
    semantic_invalid = [item["canonical_ref"] for item in realizations if item["semantic_status"] != "entailed"]
    unexpected_claims = semantic.get("unexpected_claims") if isinstance(semantic, dict) else []
    unexpected_claims = _as_list(unexpected_claims)
    blocking_unexpected = [
        item for item in unexpected_claims
        if not isinstance(item, dict) or item.get("confidence") in ("high", "medium", None)
    ]
    requirement_invalid = [
        item["requirement_ref"] for item in requirement_realizations
        if item.get("status") != "addressed" or not item.get("anchors")
    ]
    snapshot_id = brief.get("generation_snapshot_id")
    brief_stale = bool(brief_issues)
    if (is_summary and markdown.strip() and not realizations):
        issues.append("non-empty summary has no realized whitelist hints")
    if not semantic_path:
        status = "needs_semantic_review"
    elif (issues or missing or semantic_invalid or unexpected_refs
          or blocking_unexpected or brief_stale or missing_requirement_evaluations
          or requirement_invalid):
        status = "invalid"
    else:
        status = "valid"
    manifest = {
        "schema_version": SCHEMA_VERSIONS["realization"], "section_ref": section_ref,
        "section_hash": content_hash(markdown),
        "brief_hash": brief.get("brief_hash"), "brief_artifact_id": brief_artifact_id,
        "brief_path": os.path.abspath(brief_path),
        "snapshot_id": snapshot_id, "status": status,
        "realizations": realizations, "missing_expected_refs": missing,
        "requirement_realizations": requirement_realizations,
        "missing_requirement_evaluations": missing_requirement_evaluations,
        "unexpected_refs": sorted(set(unexpected_refs)),
        "unexpected_claims": unexpected_claims,
        "blocking_unexpected_claims": blocking_unexpected,
        "brief_stale": brief_stale, "issues": issues,
        "diagnostic_refs": [], "policy_version": REALIZATION_POLICY_VERSION,
    }
    if output_path is None:
        safe = re.sub(r"[^A-Za-z0-9_.-]", "-", str(section_ref))
        output_path = os.path.join(state_dir, "derived", "realization", "%s.json" % safe)
    _write_json_atomic(output_path, manifest)
    _register_artifact(state_dir, {
        "artifact_id": "realization:%s" % section_ref, "kind": "realization",
        "path": os.path.abspath(output_path), "output_hash": file_hash(output_path),
        "status": "fresh" if status == "valid" else "blocked",
        "dependency_refs": [item.get("canonical_ref") for item in realizations],
        "dependency_files": list(CANONICAL_FILES), "snapshot_id": snapshot_id,
        "brief_hash": brief.get("brief_hash"),
        "policy_version": REALIZATION_POLICY_VERSION,
    })
    result_issues = list(issues)
    if missing:
        result_issues.append("missing expected refs: " + ", ".join(missing))
    if semantic_invalid:
        result_issues.append("semantic review incomplete or failed: " + ", ".join(semantic_invalid))
    if missing_requirement_evaluations:
        result_issues.append("missing requirement evaluations: " + ", ".join(missing_requirement_evaluations))
    if requirement_invalid:
        result_issues.append("requirement response missing/contradicted: " + ", ".join(requirement_invalid))
    return {"passed": status == "valid", "issues": result_issues,
            "manifest": manifest, "output_path": os.path.abspath(output_path)}


FIT_DIMENSIONS = (
    "need_alignment", "role_decision_coverage", "insight_credibility",
    "value_strength", "differentiation", "evidence_quality",
    "delivery_readiness", "commitment_safety", "reading_efficiency", "consistency",
)
LEVEL_RANGES = {
    "deficient": (10, 35), "fragile": (35, 55), "adequate": (55, 75),
    "strong": (75, 90), "distinctive": (90, 100), "not_evaluated": (20, 90),
}


def _ratio_level(numerator, denominator, distinctive=False):
    if denominator <= 0: return "not_evaluated"
    ratio = numerator / float(denominator)
    if ratio < 0.4: return "deficient"
    if ratio < 0.7: return "fragile"
    if ratio < 0.9: return "adequate"
    if ratio < 1.0 or not distinctive: return "strong"
    return "distinctive"


def _fit_weights(requirements):
    weights = {dimension: [2.0, 4.0] for dimension in FIT_DIMENSIONS}
    provenance = {dimension: ["systemic floor"] for dimension in FIT_DIMENSIONS}
    keyword_map = {
        "need_alignment": ("理解", "需求", "洞察", "目标", "现状"),
        "role_decision_coverage": ("团队", "服务", "协同", "管理"),
        "insight_credibility": ("分析", "策略", "依据"),
        "value_strength": ("方案", "效果", "创意", "策划"),
        "differentiation": ("创新", "亮点", "特色", "创意"),
        "evidence_quality": ("案例", "业绩", "资质", "数据"),
        "delivery_readiness": ("执行", "进度", "资源", "人员", "保障"),
        "commitment_safety": ("承诺", "应急", "风险", "质量", "售后"),
        "reading_efficiency": ("呈现", "完整", "清晰"),
        "consistency": ("整体", "一致", "响应"),
    }
    for item in _as_list(requirements.get("scoring")):
        if not isinstance(item, dict): continue
        weight = item.get("weight")
        if not isinstance(weight, (int, float)): continue
        mapping = item.get("fit_dimension_map") or {}
        primary = mapping.get("primary")
        secondary = mapping.get("secondary")
        if primary not in FIT_DIMENSIONS:
            text = "%s %s %s" % (item.get("item", ""), item.get("dimension", ""), item.get("basis", ""))
            scores = [(sum(1 for word in words if word in text), dimension) for dimension, words in keyword_map.items()]
            primary = max(scores)[1] if max(scores)[0] else "value_strength"
        if secondary in FIT_DIMENSIONS and secondary != primary:
            primary_share = weight * 0.80
            secondary_share = weight * 0.20
            weights[primary][0] += primary_share
            weights[primary][1] += primary_share
            weights[secondary][0] += secondary_share
            weights[secondary][1] += secondary_share
            provenance[primary].append("%s primary 80%%" % item.get("id"))
            provenance[secondary].append("%s secondary 20%%" % item.get("id"))
        else:
            weights[primary][0] += weight
            weights[primary][1] += weight
            provenance[primary].append("%s primary 100%%" % item.get("id"))
    return weights, provenance


def customer_fit(state_dir, checkpoint="strategy", judgments_path=None,
                 realization_dir=None, output_path=None):
    if checkpoint not in ("strategy", "submission"):
        return {"passed": False, "issues": ["checkpoint must be strategy or submission"]}
    if realization_dir is None:
        realization_dir = os.path.join(state_dir, "derived", "realization")
    stage = "generation" if checkpoint == "strategy" else "submission"
    checked = check_canonical(state_dir, stage=stage, realization_dir=realization_dir if checkpoint == "submission" else None, write_derived=True)
    documents, load_issues = load_state(state_dir)
    if load_issues: return {"passed": False, "issues": load_issues}
    coverage = coverage_diagnostics(documents, realization_dir if checkpoint == "submission" else None)
    cv = documents["customer-value.json"]
    delivery = documents["delivery-plan.json"]
    judgments = _read_json(judgments_path) if judgments_path else {}
    judgment_by_dimension = {item.get("dimension"): item for item in _as_list(judgments.get("dimensions")) if isinstance(item, dict) and item.get("dimension") in FIT_DIMENSIONS}

    paths = coverage["customer_value_track"]["paths"]
    required = [item for item in paths if item["requiredness"] == "required"]
    connected_required = [item for item in required if item["maturity"] in ("publishable", "realized") and item["health"] == "valid"]
    roles = set(item["role_ref"] for item in required)
    covered_roles = set(item["role_ref"] for item in connected_required)
    publishable_claims = [item for item in _as_list(cv.get("claims")) if isinstance(item, dict) and item.get("status") == "publishable"]
    evidence_by_ref = {
        item.get("id"): item
        for item in _as_list(documents["intel-pool.json"].get("evidence"))
        if isinstance(item, dict) and item.get("id")
    }
    links_by_target = {}
    for link in _as_list(cv.get("evidence_links")):
        if isinstance(link, dict) and link.get("target_ref"):
            links_by_target.setdefault(link.get("target_ref"), []).append(link)
    supported_claims = [
        item for item in publishable_claims
        if any(
            _evidence_support_usable(
                link, evidence_by_ref.get(link.get("evidence_ref")) or {},
                item.get("risk_level") or "medium", _claim_proof_task(item))
            for link in links_by_target.get(item.get("id"), [])
        )
    ]
    selected_actions = [item for item in _as_list(delivery.get("actions")) if isinstance(item, dict) and item.get("selection_status") == "selected"]
    ready_actions = [item for item in selected_actions if item.get("readiness_status") in ("planned", "confirmed") and len(_ref_list(item, "accountable_role_ref")) == 1]
    committed = [item for item in publishable_claims if item.get("commitment_level") == "committed"]
    safe_committed = [item for item in committed if item.get("authority_ref") and _ref_list(item, "action_refs")]
    active_needs = [item for item in _as_list(cv.get("needs")) if isinstance(item, dict) and item.get("status") == "active"]
    credible_needs = [item for item in active_needs if item.get("evidence_quality") in ("medium", "high") and item.get("inference_confidence") in ("medium", "high")]
    selected_vps = [item for item in _as_list(cv.get("value_propositions")) if isinstance(item, dict) and item.get("status") in ("selected", "publishable")]

    inferred = {
        "need_alignment": _ratio_level(len(connected_required), len(required)),
        "role_decision_coverage": _ratio_level(len(covered_roles), len(roles)),
        "insight_credibility": _ratio_level(len(credible_needs), len(active_needs)),
        "value_strength": "adequate" if selected_vps and connected_required else ("fragile" if selected_vps else "deficient"),
        "differentiation": "not_evaluated",
        "evidence_quality": _ratio_level(len(supported_claims), len(publishable_claims)),
        "delivery_readiness": _ratio_level(len(ready_actions), len(selected_actions)),
        "commitment_safety": _ratio_level(len(safe_committed), len(committed)) if committed else "adequate",
        "reading_efficiency": "not_evaluated",
        "consistency": "strong" if checkpoint == "submission" and checked["passed"] else ("not_evaluated" if checkpoint == "strategy" else "fragile"),
    }
    weights, provenance = _fit_weights(documents["requirements.json"])
    if required:
        for dimension in ("need_alignment", "role_decision_coverage"):
            weights[dimension][0] += min(6.0, len(required) * 0.5)
            weights[dimension][1] += min(8.0, len(required) * 0.75)
            provenance[dimension].append("required Role×Need×Criterion obligations")
    high_risk_claims = [
        item for item in publishable_claims
        if item.get("risk_level") in ("high", "critical")
    ]
    if high_risk_claims:
        for dimension in ("evidence_quality", "delivery_readiness", "commitment_safety", "consistency"):
            weights[dimension][0] = max(weights[dimension][0], 6.0)
            weights[dimension][1] = max(weights[dimension][1], 10.0)
            provenance[dimension].append("high-risk publishable Claim floor")
    dimensions = []
    for dimension in FIT_DIMENSIONS:
        judgment = judgment_by_dimension.get(dimension)
        if judgment and judgment.get("level") in LEVEL_RANGES and judgment.get("reason") and judgment.get("source_refs"):
            level = judgment["level"]
            reason = judgment["reason"]
            confidence = judgment.get("confidence") or "medium"
            source_refs = judgment.get("source_refs")
            authority = "semantic_judgment"
        else:
            level = inferred[dimension]
            reason = "deterministic v3 anchors; semantic judgment not supplied" if level == "not_evaluated" else "derived from canonical coverage and hard-gate structure"
            confidence = "low" if level == "not_evaluated" else "medium"
            source_refs = []
            authority = "deterministic"
        dimensions.append({
            "dimension": dimension, "level": level,
            "weight_range": [round(weights[dimension][0], 2), round(weights[dimension][1], 2)],
            "weight_provenance": provenance[dimension], "confidence": confidence,
            "reason": reason, "source_refs": source_refs, "authority": authority,
        })

    if checkpoint == "strategy":
        gate_failures = [
            item for item in checked.get("diagnostics", [])
            if item.get("severity") == "fatal"
            or "compile" in item.get("blocks", [])
            or "task3" in item.get("blocks", [])
        ]
    else:
        gate_failures = [
            item for item in checked.get("diagnostics", [])
            if item.get("severity") in ("fatal", "blocker")
        ]
    overall = {"status": "withheld", "fit_range": None, "band": None}
    if not gate_failures:
        total_low = sum(item["weight_range"][0] for item in dimensions)
        total_high = sum(item["weight_range"][1] for item in dimensions)
        low_score = sum(LEVEL_RANGES[item["level"]][0] * item["weight_range"][0] for item in dimensions) / max(total_low, 1)
        high_score = sum(LEVEL_RANGES[item["level"]][1] * item["weight_range"][1] for item in dimensions) / max(total_high, 1)
        low_score = int(low_score // 5 * 5)
        high_score = int((high_score + 4.999) // 5 * 5)
        levels = {item["dimension"]: item["level"] for item in dimensions}
        if any(levels[name] in ("deficient", "fragile") for name in ("need_alignment", "role_decision_coverage", "delivery_readiness", "commitment_safety", "consistency")):
            high_score = min(high_score, 70)
        applicable_levels = [value for value in levels.values() if value != "not_evaluated"]
        all_adequate = all(value in ("adequate", "strong", "distinctive") for value in applicable_levels)
        has_distinctive_value = levels["value_strength"] == "distinctive" or levels["differentiation"] == "distinctive"
        if not (all_adequate and has_distinctive_value and len(applicable_levels) == len(FIT_DIMENSIONS)):
            high_score = min(high_score, 85)
        bands = []
        for name, lower, upper in (("fragile", 0, 55), ("credible", 55, 75), ("competitive", 75, 90), ("strong", 90, 101)):
            if low_score < upper and high_score >= lower: bands.append(name)
        overall = {"status": "partial" if any(item["level"] == "not_evaluated" for item in dimensions) else "evaluated", "fit_range": [low_score, high_score], "band": "/".join(bands)}

    shortboard = []
    for diagnostic in sorted(checked.get("diagnostics", []), key=lambda item: {"fatal": 0, "blocker": 1, "major": 2, "minor": 3, "info": 4}.get(item.get("severity"), 5)):
        if len(shortboard) >= 5: break
        if diagnostic.get("severity") in ("fatal", "blocker", "major"):
            shortboard.append({
                "root_diagnostic": diagnostic.get("root_cause_key"), "kind": diagnostic.get("kind"),
                "owner": diagnostic.get("owner"), "target_refs": diagnostic.get("subject_refs"),
                "recommended_repair": (diagnostic.get("repair_options") or [None])[0],
                "recheck_scope": diagnostic.get("blocks") or ["customer-fit"],
            })
    result = {
        "schema_version": SCHEMA_VERSIONS["fit"], "checkpoint": checkpoint,
        "policy_version": FIT_POLICY_VERSION,
        "gates": {"passed": not gate_failures, "failures": [item.get("root_cause_key") for item in gate_failures]},
        "dimensions": dimensions, "overall": overall, "shortboard": shortboard,
        "uncertainty_drivers": [item["dimension"] for item in dimensions if item["level"] == "not_evaluated" or item["confidence"] == "low"],
        "disclaimer": "This is an internal customer-fit sensitivity range, not an evaluator score or win probability.",
    }
    if output_path is None:
        output_path = os.path.join(state_dir, "derived", "customer-fit.%s.json" % checkpoint)
    _write_json_atomic(output_path, result)
    return {"passed": not gate_failures, "issues": checked.get("issues", []), "scorecard": result, "output_path": os.path.abspath(output_path)}


def archive_state(state_dir, bundle_dir, require_submission_ready=True):
    """Archive safe per-bid state and preserve the previous archive as last-good."""
    realization_dir = os.path.join(state_dir, "derived", "realization")
    draft_checked = check_canonical(state_dir, stage="draft")
    if not draft_checked["passed"]:
        return {
            "passed": False,
            "issues": ["archive refused because canonical state is corrupt"] + draft_checked["issues"],
            "diagnostics": draft_checked["diagnostics"],
        }
    checked = check_canonical(state_dir, stage="submission", realization_dir=realization_dir)
    if require_submission_ready and not checked["passed"]:
        return {"passed": False, "issues": checked["issues"], "diagnostics": checked["diagnostics"]}
    bundle_dir = os.path.abspath(bundle_dir)
    os.makedirs(bundle_dir, exist_ok=True)
    staging = tempfile.mkdtemp(prefix="._state-staging-", dir=bundle_dir)
    target = os.path.join(bundle_dir, "_state")
    last_good = os.path.join(bundle_dir, "_state.last-good")
    try:
        for filename in CANONICAL_FILES + ("source-manifest.json", "run-manifest.json", "legacy-to-v3-map.json"):
            source = os.path.join(state_dir, filename)
            if os.path.isfile(source): shutil.copy2(source, os.path.join(staging, filename))
        for relative in ("derived/manifests", "derived/realization"):
            source = os.path.join(state_dir, relative)
            if os.path.isdir(source): shutil.copytree(source, os.path.join(staging, relative), dirs_exist_ok=True)
        sections_source = os.path.join(state_dir, "sections")
        if os.path.isdir(sections_source):
            shutil.copytree(sections_source, os.path.join(staging, "sections"), dirs_exist_ok=True)
        for filename in ("coverage.json", "diagnostics.json", "customer-fit.strategy.json", "customer-fit.submission.json"):
            source = os.path.join(state_dir, "derived", filename)
            if os.path.isfile(source):
                destination_dir = os.path.join(staging, "derived")
                os.makedirs(destination_dir, exist_ok=True)
                shutil.copy2(source, os.path.join(destination_dir, filename))
        _write_json_atomic(os.path.join(staging, "archive-manifest.json"), {
            "schema_version": "state-archive/v1",
            "canonical_submission_ready": checked["passed"],
            "submission_ready": None if checked["passed"] else False,
            "submission_ready_reason": (
                "report-level compliance, QA, customer-fit and Gate 2 are not attested by archive-state"
            ),
            "engine": ENGINE, "engine_version": ENGINE_VERSION,
            "warning": "INTERNAL STATE — NEVER SUBMIT TO THE CUSTOMER",
        })
        if os.path.exists(last_good): shutil.rmtree(last_good, ignore_errors=True)
        if os.path.exists(target): os.replace(target, last_good)
        os.replace(staging, target)
        staging = None
        return {
            "passed": True, "issues": [], "state_archive": target,
            "last_good": last_good if os.path.exists(last_good) else None,
            "canonical_submission_ready": checked["passed"],
            "submission_ready": None if checked["passed"] else False,
        }
    except Exception as exc:
        if not os.path.exists(target) and os.path.exists(last_good):
            try: os.replace(last_good, target)
            except Exception: pass
        return {"passed": False, "issues": ["archive failed; last-good preserved: %s" % exc]}
    finally:
        if staging and os.path.exists(staging): shutil.rmtree(staging, ignore_errors=True)


def add_cli_parsers(sub):
    p = sub.add_parser("init-state"); p.add_argument("--state-dir", required=True); p.add_argument("--mode", default="standard", choices=["quick", "standard", "deep"]); p.add_argument("--lang", default="zh")
    p = sub.add_parser("bootstrap-state"); p.add_argument("--state-dir", required=True); p.add_argument("--proposal", required=True); p.add_argument("--mode", default="standard", choices=["quick", "standard", "deep"]); p.add_argument("--lang", default="zh")
    p = sub.add_parser("migrate-state"); p.add_argument("--source-dir", required=True); p.add_argument("--output-dir", required=True); p.add_argument("--mode", default="standard", choices=["quick", "standard", "deep"]); p.add_argument("--lang", default="zh")
    p = sub.add_parser("check-canonical"); p.add_argument("--state-dir", required=True); p.add_argument("--stage", default="draft", choices=["draft", "generation", "submission"]); p.add_argument("--realization-dir", default=None); p.add_argument("--write-derived", action="store_true")
    p = sub.add_parser("apply-changeset"); p.add_argument("--state-dir", required=True); p.add_argument("--changeset", required=True)
    p = sub.add_parser("promote-research"); p.add_argument("--state-dir", required=True); p.add_argument("--intel-proposal", required=True); p.add_argument("--links-proposal", required=True)
    p = sub.add_parser("apply-auto-state"); p.add_argument("--state-dir", required=True)
    p = sub.add_parser("freeze-snapshot"); p.add_argument("--state-dir", required=True); p.add_argument("--force", action="store_true")
    p = sub.add_parser("compile-context"); p.add_argument("--state-dir", required=True); p.add_argument("--target", required=True, choices=["research", "value-selection", "section", "exec-summary", "redteam"]); p.add_argument("--id", default=None); p.add_argument("--role", default=None); p.add_argument("--output", default=None); p.add_argument("--token-budget", default=24000, type=int)
    p = sub.add_parser("audit-realization"); p.add_argument("--state-dir", required=True); p.add_argument("--section-ref", required=True); p.add_argument("--section", required=True); p.add_argument("--hints", required=True); p.add_argument("--brief", required=True); p.add_argument("--semantic", default=None); p.add_argument("--output", default=None)
    p = sub.add_parser("customer-fit"); p.add_argument("--state-dir", required=True); p.add_argument("--checkpoint", default="strategy", choices=["strategy", "submission"]); p.add_argument("--judgments", default=None); p.add_argument("--realization-dir", default=None); p.add_argument("--output", default=None)
    p = sub.add_parser("archive-state"); p.add_argument("--state-dir", required=True); p.add_argument("--bundle-dir", required=True); p.add_argument("--allow-draft", action="store_true")


def dispatch_cli(args):
    command = args.command
    if command == "init-state": result = init_state(args.state_dir, args.mode, args.lang)
    elif command == "bootstrap-state": result = bootstrap_state(args.state_dir, args.proposal, args.mode, args.lang)
    elif command == "migrate-state": result = migrate_state(args.source_dir, args.output_dir, args.mode, args.lang)
    elif command == "check-canonical": result = check_canonical(args.state_dir, args.stage, args.realization_dir, args.write_derived)
    elif command == "apply-changeset": result = apply_changeset(args.state_dir, args.changeset)
    elif command == "promote-research": result = promote_research(args.state_dir, args.intel_proposal, args.links_proposal)
    elif command == "apply-auto-state": result = apply_auto_state(args.state_dir)
    elif command == "freeze-snapshot": result = freeze_snapshot(args.state_dir, args.force)
    elif command == "compile-context": result = compile_context(args.state_dir, args.target, args.id, args.role, args.output, args.token_budget)
    elif command == "audit-realization": result = audit_realization(args.state_dir, args.section_ref, args.section, args.hints, args.brief, args.semantic, args.output)
    elif command == "customer-fit": result = customer_fit(args.state_dir, args.checkpoint, args.judgments, args.realization_dir, args.output)
    elif command == "archive-state": result = archive_state(args.state_dir, args.bundle_dir, not args.allow_draft)
    else: return None
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("passed") else 1
