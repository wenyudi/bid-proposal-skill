import copy
import json
import os
import tempfile
import unittest
from unittest import mock


from tools import prop_tools, prop_v3


def _write_json(path, value):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)


def _valid_documents():
    requirements = {
        "schema_version": "requirements/v3",
        "revision": 1,
        "project_name": "客户价值测试项目",
        "buyer": "测试采购人",
        "budget_cap": {"value": 100, "unit": "万元"},
        "mandatory": [{
            "id": "M-01", "item": "提供完整执行方案", "type": "实质性",
            "authority_uses": ["commitment_authority"],
        }],
        "scoring": [{
            "id": "S-01", "item": "执行方案完整、可行", "weight": 30,
            "basis": "人员、进度、验收闭环",
            "fit_dimension_map": {"primary": "delivery_readiness", "secondary": "commitment_safety"},
        }],
        "deliverables": [],
    }
    customer_value = {
        "schema_version": "customer-value/v1",
        "revision": 1,
        "roles": [{
            "id": "ROLE-BUSINESS", "name": "业务负责人",
            "archetypes": ["business_owner"], "presence": "explicit",
            "confidence": "high", "formal_power": "scoring",
            "practical_influence": "high", "delivery_impact": "critical",
            "scrutiny_level": "high", "evidence_refs": ["EV-TENDER"],
        }],
        "needs": [{
            "id": "NEED-CERTAINTY", "name": "降低执行失控风险",
            "statement": "在有限管理投入下获得可验收的稳定交付",
            "assertion_mode": "explicit", "source_visibility": "public",
            "status": "active", "evidence_quality": "high",
            "inference_confidence": "high", "publication_status": "public_explicit",
            "evidence_link_refs": ["EL-NEED"],
        }],
        "criteria": [{
            "id": "CRIT-DELIVERY", "name": "执行闭环",
            "statement": "责任、节奏和验收均可核验",
            "status": "active", "publication_status": "public_explicit",
            "evidence_link_refs": ["EL-CRIT"],
        }],
        "role_need_links": [{
            "id": "RN-01", "role_ref": "ROLE-BUSINESS",
            "need_ref": "NEED-CERTAINTY", "criterion_refs": ["CRIT-DELIVERY"],
            "priority_band": "critical", "requiredness": "required", "confidence": "high",
        }],
        "need_criterion_links": [{
            "id": "NC-01", "need_ref": "NEED-CERTAINTY", "criterion_ref": "CRIT-DELIVERY",
        }],
        "role_criterion_links": [],
        "value_propositions": [{
            "id": "VP-CLOSED-LOOP", "name": "少盯过程也能稳妥验收",
            "value_mechanism": "以单一责任人、阶段检查和验收留痕形成闭环",
            "expected_change": "降低采购人日常管理负担和交付风险",
            "value_lens": "risk", "status": "selected", "portfolio_role": "lead",
            "role_refs": ["ROLE-BUSINESS"], "need_refs": ["NEED-CERTAINTY"],
            "criterion_refs": ["CRIT-DELIVERY"], "action_refs": ["DA-CLOSED-LOOP"],
            "evidence_link_refs": ["EL-VP"],
        }],
        "claims": [{
            "id": "CL-CLOSED-LOOP",
            "proposition": "项目经理对阶段检查与验收闭环承担单一责任",
            "content_kind": "proposal", "epistemic_status": "evidenced",
            "commitment_level": "committed", "status": "publishable",
            "risk_level": "high", "scope": "合同期技术服务",
            "value_proposition_refs": ["VP-CLOSED-LOOP"],
            "evidence_link_refs": ["EL-CLAIM"], "metric_refs": [],
            "action_refs": ["DA-CLOSED-LOOP"], "authority_ref": "GATE-CAPABILITY-RESOLVED",
        }],
        "metrics": [],
        "evidence_links": [
            {"id": "EL-NEED", "evidence_ref": "EV-TENDER", "target_ref": "NEED-CERTAINTY", "relation": "supports", "strength": "direct", "scope": "本项目执行方案", "reason": "标书明确要求完整执行方案"},
            {"id": "EL-CRIT", "evidence_ref": "EV-TENDER", "target_ref": "CRIT-DELIVERY", "relation": "supports", "strength": "direct", "scope": "本项目执行闭环", "reason": "标书要求完整可执行响应"},
            {"id": "EL-VP", "evidence_ref": "EV-CAPABILITY", "target_ref": "VP-CLOSED-LOOP", "relation": "supports", "strength": "strong", "scope": "合同期项目经理配置", "reason": "已核验项目经理可用"},
            {"id": "EL-CLAIM", "evidence_ref": "EV-CAPABILITY", "target_ref": "CL-CLOSED-LOOP", "relation": "supports", "strength": "strong", "scope": "合同期项目经理配置", "reason": "已核验项目经理可承担该职责"},
        ],
        "role_conflicts": [],
        "change_log": [],
    }
    delivery = {
        "schema_version": "delivery-plan/v1",
        "revision": 1,
        "delivery_roles": [{"id": "DR-PM", "name": "项目经理", "scope": "全流程交付"}],
        "actions": [{
            "id": "DA-CLOSED-LOOP", "name": "运行阶段检查与验收闭环",
            "selection_status": "selected", "readiness_status": "confirmed",
            "commitment_level": "committed", "required": True,
            "accountable_role_ref": "DR-PM", "responsible_role_refs": ["DR-PM"],
            "supporting_role_refs": [], "requirement_refs": ["M-01", "S-01"],
            "value_proposition_refs": ["VP-CLOSED-LOOP"], "claim_refs": ["CL-CLOSED-LOOP"],
            "resource_refs": ["RES-PM", "RES-BUDGET"],
            "resource_demands": [
                {"resource_ref": "RES-PM", "time_window": "contract", "low": 1, "high": 1},
                {"resource_ref": "RES-BUDGET", "time_window": "contract", "low": 90, "high": 95}
            ],
            "dependency_refs": [], "acceptance_refs": ["AC-CLOSED-LOOP"],
            "authority_ref": "GATE-CAPABILITY-RESOLVED", "time_window": "contract",
        }],
        "resource_envelopes": [
            {
                "id": "RES-PM", "kind": "person", "name": "项目经理容量",
                "unit": "FTE", "capacity": {"low": 1, "high": 2}, "time_window": "contract",
                "status": "confirmed", "authority_ref": "GATE-CAPABILITY-RESOLVED",
                "approved_projection": "配置一名项目经理承担全流程责任",
            },
            {
                "id": "RES-BUDGET", "kind": "budget", "name": "单一推荐方案预算",
                "unit": "万元", "capacity": {"low": 90, "high": 100},
                "time_window": "contract", "portfolio_budget": True,
                "status": "confirmed", "authority_ref": "GATE-BUDGET-RESOLVED",
                "approved_allocation": {"low": 90, "high": 100, "unit": "万元"},
            }
        ],
        "customer_dependencies": [],
        "acceptance_contracts": [{
            "id": "AC-CLOSED-LOOP", "subject": "阶段交付物",
            "criteria": "满足标书要求与经确认样稿", "method": "阶段审阅",
            "records": "确认单与版本记录", "correction_window": "按标书约定",
            "authority_ref": "M-01", "approver_role_refs": ["ROLE-BUSINESS"],
        }],
        "change_log": [],
    }
    strategy = {
        "schema_version": "strategy/v3",
        "revision": 1,
        "title": "客户价值测试方案", "depth_mode": "standard",
        "narrative": {"mode": "logic", "rationale": "执行分高", "through_line": "从管理负担到稳妥验收"},
        "big_idea": "一条责任链，贯穿每次交付",
        "decision_map": {"destination": "全部强制项和评分项有可兑现响应。", "not_yet_specified": [], "out_of_scope": []},
        "open_questions": [
            {
                "id": "GATE-CAPABILITY-RESOLVED",
                "title": "交付能力边界", "q": "能否配置项目经理？",
                "why_matters": "决定责任承诺", "ai_assumption": "保守配置",
                "depends_on": [], "status": "resolved", "resolved": "确认配置",
                "safe_constraint": "仅在合同期承诺已核验的项目经理配置。",
                "affected_refs": ["CL-CLOSED-LOOP", "DA-CLOSED-LOOP", "RES-PM", "EV-CAPABILITY"],
                "assumption_risk": False,
            },
            {
                "id": "GATE-BUDGET-RESOLVED",
                "title": "预算边界", "q": "推荐方案预算是否确认？",
                "why_matters": "决定组合预算", "ai_assumption": "不新增预算承诺",
                "depends_on": [], "status": "resolved", "resolved": "确认不超过100万元",
                "safe_constraint": "单一推荐方案不超过标书预算上限。",
                "affected_refs": ["RES-BUDGET"], "assumption_risk": False,
            },
        ],
        "decision_jobs": [{
            "id": "DJ-DELIVER", "job_kind": "deliver", "section_ref": "CH-01",
            "role_refs": ["ROLE-BUSINESS"], "criterion_refs": ["CRIT-DELIVERY"],
            "value_proposition_refs": ["VP-CLOSED-LOOP"], "claim_refs": ["CL-CLOSED-LOOP"],
            "action_refs": ["DA-CLOSED-LOOP"],
            "entry_judgment": "方案看起来有方向但未证明能落地",
            "expected_judgment": "责任、节奏和验收已经闭环",
            "transition": {"inherits": "项目目标", "must_advance": "交付可信度", "hands_off": "风险确认"},
        }],
        "sections": [{
            "id": "CH-01", "n": 1, "title": "以单一责任链保障稳定交付",
            "sub": ["责任闭环", "验收闭环"], "addresses": ["M-01", "S-01"],
            "primary_decision_job_ref": "DJ-DELIVER", "secondary_decision_job_ref": None,
        }],
        "change_log": [],
    }
    intel = {
        "schema_version": "intel-pool/v3",
        "revision": 1,
        "evidence": [
            {"id": "EV-TENDER", "kind": "tender_clause", "title": "标书执行要求", "content": "须提供完整执行方案", "source": "招标文件", "visibility": "public", "quality": "high", "status": "active", "allowed_uses": ["proposal_narrative"]},
            {"id": "EV-CAPABILITY", "kind": "verified_capability", "title": "内部原始配置证明", "safe_title": "项目经理配置证明", "content": "敏感原始材料：某客户名称与金额", "approved_projection": "已核验项目经理可用", "source": "投标人材料", "visibility": "approved_anonymized", "quality": "high", "status": "active", "allowed_uses": ["proposal_narrative", "bidder_capability"], "publication_authority_ref": "GATE-CAPABILITY-RESOLVED"},
        ],
        "gaps": [], "research_manifest": {}, "change_log": [],
    }
    return {
        "requirements.json": requirements,
        "customer-value.json": customer_value,
        "delivery-plan.json": delivery,
        "strategy.json": strategy,
        "intel-pool.json": intel,
    }


def _make_state(directory, documents=None):
    documents = documents or _valid_documents()
    for filename, value in documents.items():
        _write_json(os.path.join(directory, filename), value)
    _write_json(os.path.join(directory, "source-manifest.json"), {
        "schema_version": "source-manifest/v1", "revision": 1, "sources": []
    })
    _write_json(os.path.join(directory, "run-manifest.json"), {
        "schema_version": "run-manifest/v1", "revision": 1,
        "engine": "v3", "engine_version": "3.0", "fallback_policy": "explicit",
        "policy_version": "proposal-v3/policy-1",
    })
    prop_v3._ensure_layout(directory)
    return documents


def _lean_documents():
    documents = prop_v3._upgrade_to_lean_documents(_valid_documents())
    documents["strategy.json"]["sections"][0]["visible_outputs"] = [{
        "id": "OUT-RESPONSIBILITY-CARD",
        "purpose": "让评委直接看到责任与检查节点",
        "supports_refs": ["VP-CLOSED-LOOP", "M-01"],
        "required_fields": ["责任人", "检查节点"],
        "grounding_refs": ["M-01", "EV-TENDER"],
        "grounding_mode": "tender",
        "truth_boundary": "只呈现标书要求和已确认项目经理职责，不扩大 SLA",
        "requiredness": "required",
    }]
    return documents


def _make_submission_ready_lean_state(directory):
    documents = _lean_documents()
    _make_state(directory, documents)
    section_path = os.path.join(directory, "sections", "section-1.md")
    section_text = (
        "### 1.1 一条责任链闭环交付\n\n"
        "项目经理对阶段检查与验收闭环承担单一责任。\n\n"
        "责任人：项目经理；检查节点：每个阶段交付前。\n"
    )
    with open(section_path, "w", encoding="utf-8") as handle:
        handle.write(section_text)
    compiled = prop_v3.compile_context(
        directory, "section", target_id="CH-01")
    semantic_path = os.path.join(directory, "semantic.json")
    _write_json(semantic_path, {
        "schema_version": "semantic-realization/v1",
        "section_ref": "CH-01",
        "snapshot_id": compiled["brief"]["generation_snapshot_id"],
        "brief_hash": compiled["brief"]["brief_hash"],
        "evaluator": "independent-test/v1",
        "evaluations": [
            {
                "canonical_ref": "CL-CLOSED-LOOP", "contribution": "prove",
                "quote": "项目经理对阶段检查与验收闭环承担单一责任。",
                "semantic_status": "entailed",
                "observed_commitment_level": "committed",
                "reason": "命题、范围和责任一致", "confidence": "high",
                "evidence_refs_presented": [],
            },
            {
                "canonical_ref": "DA-CLOSED-LOOP",
                "contribution": "operationalize",
                "quote": "项目经理对阶段检查与验收闭环承担单一责任。",
                "semantic_status": "entailed",
                "observed_commitment_level": "committed",
                "reason": "动作和责任已落地", "confidence": "high",
                "evidence_refs_presented": [],
            },
        ],
        "requirement_evaluations": [
            {"requirement_ref": "M-01", "status": "addressed",
             "quote": "项目经理对阶段检查与验收闭环承担单一责任。",
             "reason": "提供责任与验收机制", "confidence": "high"},
            {"requirement_ref": "S-01", "status": "addressed",
             "quote": "项目经理对阶段检查与验收闭环承担单一责任。",
             "reason": "回应人员和验收闭环", "confidence": "high"},
        ],
        "visible_output_evaluations": [{
            "output_ref": "OUT-RESPONSIBILITY-CARD", "status": "filled",
            "field_evidence": [
                {"field": "责任人", "quote": "责任人：项目经理",
                 "reason": "责任主体为实值"},
                {"field": "检查节点", "quote": "检查节点：每个阶段交付前",
                 "reason": "节点为项目内可执行时点"},
            ],
            "grounding_refs_presented": ["M-01"],
            "reason": "两个必填字段均可直接检查", "confidence": "high",
        }],
        "unexpected_claims": [], "overall": "valid",
    })
    audited = prop_v3.audit_realization(
        directory, "CH-01", section_path, None,
        compiled["output_path"], semantic_path)
    if not audited["passed"]:
        raise AssertionError(audited["issues"])

    summary_compiled = prop_v3.compile_context(directory, "exec-summary")
    summary_path = os.path.join(directory, "sections", "section-0.md")
    with open(summary_path, "w", encoding="utf-8") as handle:
        handle.write("项目经理对阶段检查与验收闭环承担单一责任。\n")
    summary_semantic_path = os.path.join(directory, "summary-semantic.json")
    _write_json(summary_semantic_path, {
        "schema_version": "semantic-realization/v1", "section_ref": "CH-00",
        "snapshot_id": summary_compiled["brief"]["generation_snapshot_id"],
        "brief_hash": summary_compiled["brief"]["brief_hash"],
        "evaluator": "independent-test/v1",
        "evaluations": [
            {"canonical_ref": "CL-CLOSED-LOOP", "contribution": "summarize",
             "quote": "项目经理对阶段检查与验收闭环承担单一责任。",
             "semantic_status": "entailed",
             "observed_commitment_level": "committed", "reason": "等义摘要",
             "confidence": "high", "evidence_refs_presented": []},
            {"canonical_ref": "DA-CLOSED-LOOP", "contribution": "summarize",
             "quote": "项目经理对阶段检查与验收闭环承担单一责任。",
             "semantic_status": "entailed",
             "observed_commitment_level": "committed", "reason": "等义摘要",
             "confidence": "high", "evidence_refs_presented": []},
        ],
        "requirement_evaluations": [],
        "visible_output_evaluations": [],
        "unexpected_claims": [], "overall": "valid",
    })
    summary_audited = prop_v3.audit_realization(
        directory, "CH-00", summary_path, None,
        summary_compiled["output_path"], summary_semantic_path)
    if not summary_audited["passed"]:
        raise AssertionError(summary_audited["issues"])
    return documents, compiled, audited


class ProposalV3Tests(unittest.TestCase):
    def test_malformed_changeset_returns_repairable_issue(self):
        with tempfile.TemporaryDirectory() as directory:
            changeset_path = os.path.join(directory, "broken-changeset.json")
            with open(changeset_path, "w", encoding="utf-8") as handle:
                handle.write("{invalid")

            result = prop_v3.apply_changeset(directory, changeset_path)

        self.assertFalse(result["passed"])
        self.assertTrue(any(
            "changeset unreadable" in issue for issue in result["issues"]
        ), result["issues"])

    def test_malformed_realization_hints_return_repairable_issue(self):
        with tempfile.TemporaryDirectory() as directory:
            _make_state(directory)
            compiled = prop_v3.compile_context(
                directory, "section", target_id="CH-01"
            )
            self.assertTrue(compiled["passed"], compiled.get("issues"))
            section_path = os.path.join(directory, "sections", "section-1.md")
            hints_path = os.path.join(directory, "broken-hints.json")
            with open(section_path, "w", encoding="utf-8") as handle:
                handle.write("项目经理承担阶段检查与验收责任。\n")
            with open(hints_path, "w", encoding="utf-8") as handle:
                handle.write("{invalid")

            result = prop_v3.audit_realization(
                directory,
                "CH-01",
                section_path,
                hints_path,
                compiled["output_path"],
            )

        self.assertFalse(result["passed"])
        self.assertTrue(any(
            "realization hints unreadable" in issue for issue in result["issues"]
        ), result["issues"])

    def test_invalid_evidence_month_is_not_current(self):
        evidence = {"status": "active", "valid_until": "2026-13"}

        self.assertFalse(prop_v3._evidence_is_current(evidence))

    def test_token_estimate_weights_cjk_and_ascii(self):
        self.assertGreaterEqual(prop_v3._estimate_tokens("中文" * 100), 200)
        self.assertEqual(prop_v3._estimate_tokens("a" * 400), 100)

    def test_value_selection_context_contains_complete_task25_objects(self):
        documents = _valid_documents()
        with tempfile.TemporaryDirectory() as directory:
            _make_state(directory, documents)
            compiled = prop_v3.compile_context(
                directory, "value-selection", token_budget=36000
            )

        self.assertTrue(compiled["passed"], compiled.get("issues"))
        must_use = compiled["brief"]["must_use"]
        self.assertEqual(must_use["claims"], documents["customer-value.json"]["claims"])
        self.assertEqual(must_use["metrics"], documents["customer-value.json"]["metrics"])
        self.assertEqual(
            must_use["delivery_roles"],
            documents["delivery-plan.json"]["delivery_roles"],
        )
        self.assertEqual(
            must_use["customer_dependencies"],
            documents["delivery-plan.json"]["customer_dependencies"],
        )
        self.assertEqual(
            must_use["acceptance_contracts"],
            documents["delivery-plan.json"]["acceptance_contracts"],
        )
        self.assertEqual(
            must_use["decisions"], documents["strategy.json"]["open_questions"]
        )
        self.assertNotIn("decision_jobs", must_use)
        self.assertIn("decision_paths", must_use)
        self.assertEqual(must_use["sections"], documents["strategy.json"]["sections"])
        self.assertEqual(
            must_use["requirements"]["budget_cap"],
            documents["requirements.json"]["budget_cap"],
        )

    def test_value_selection_context_marks_assumed_gate_as_safe_draft(self):
        documents = _valid_documents()
        decision = documents["strategy.json"]["open_questions"][1]
        decision.update(
            status="assumed",
            resolved=decision["ai_assumption"],
            assumption_risk=True,
        )
        with tempfile.TemporaryDirectory() as directory:
            _make_state(directory, documents)
            compiled = prop_v3.compile_context(
                directory, "value-selection", token_budget=36000
            )

        self.assertTrue(compiled["passed"], compiled.get("issues"))
        policy = compiled["brief"]["must_use"]["draft_policy"]
        self.assertEqual(policy["mode"], "assumed_safe_draft")
        self.assertEqual(
            policy["assumed_decision_refs"], ["GATE-BUDGET-RESOLVED"]
        )
        self.assertFalse(policy["direct_submission_allowed"])
        self.assertNotIn("internal_provisional_planning", policy)
        self.assertIn("unknown resources stay unknown", policy["safe_draft_rule"])

    def test_changeset_rejects_reopened_gate_with_assumed_residue(self):
        documents = _valid_documents()
        decision = documents["strategy.json"]["open_questions"][1]
        decision.update(
            status="assumed",
            resolved=decision["ai_assumption"],
            assumption_risk=True,
        )
        invalid_reopen = copy.deepcopy(decision)
        invalid_reopen["status"] = "open"
        with tempfile.TemporaryDirectory() as directory:
            _make_state(directory, documents)
            changeset_path = os.path.join(directory, "invalid-reopen.json")
            _write_json(changeset_path, {
                "schema_version": "changeset/v1",
                "changeset_id": "CS-T25-INVALID-REOPEN",
                "producer": "task2.5",
                "base_revisions": {"strategy.json": 1},
                "rationale": "复现 assumed Gate 重开时遗留状态",
                "validate_stage": "draft",
                "operations": [{
                    "file": "strategy.json",
                    "op": "replace",
                    "path": "/open_questions/1",
                    "value": invalid_reopen,
                }],
                "affected_refs": [decision["id"]],
            })
            result = prop_v3.apply_changeset(directory, changeset_path)
            strategy = prop_v3._read_json(os.path.join(directory, "strategy.json"))

        self.assertFalse(result["passed"])
        self.assertTrue(result["rolled_back"])
        self.assertEqual(strategy["revision"], 1)
        self.assertEqual(strategy["open_questions"][1]["status"], "assumed")
        self.assertTrue(any(
            "open decision retains resolved value" in issue
            for issue in result["issues"]
        ), result["issues"])

    def test_bootstrap_preserves_preexisting_tender_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            tender_path = os.path.join(directory, "tender.txt")
            with open(tender_path, "w", encoding="utf-8") as handle:
                handle.write("原始标书输入")
            proposal_path = os.path.join(directory, "proposals", "task1.bootstrap.json")
            canonical = _valid_documents()
            for evidence in canonical["intel-pool.json"]["evidence"]:
                evidence["source_ref"] = "SRC-TENDER"
            _write_json(proposal_path, {
                "schema_version": "bootstrap-proposal/v1",
                "canonical": canonical,
                "source_manifest": {
                    "schema_version": "source-manifest/v1", "revision": 1,
                    "sources": [{
                        "id": "SRC-TENDER", "path": "tender.txt",
                        "kind": "tender", "visibility": "tender", "hash": None,
                    }],
                },
            })
            result = prop_v3.bootstrap_state(directory, proposal_path)
            manifest = prop_v3._read_json(os.path.join(directory, "source-manifest.json"))
            with open(tender_path, "r", encoding="utf-8") as handle:
                tender = handle.read()

        self.assertTrue(result["passed"], result.get("issues"))
        self.assertEqual(tender, "原始标书输入")
        self.assertRegex(manifest["sources"][0]["hash"], r"^sha256:[0-9a-f]{64}$")

    def test_bootstrap_rejects_model_supplied_source_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            tender_path = os.path.join(directory, "tender.txt")
            with open(tender_path, "w", encoding="utf-8") as handle:
                handle.write("真实标书内容")
            proposal_path = os.path.join(directory, "proposal.json")
            _write_json(proposal_path, {
                "schema_version": "bootstrap-proposal/v1",
                "canonical": _valid_documents(),
                "source_manifest": {
                    "schema_version": "source-manifest/v1", "revision": 1,
                    "sources": [{
                        "id": "SRC-TENDER", "path": "tender.txt", "kind": "tender",
                        "visibility": "tender", "hash": "sha256:" + "0" * 64,
                    }],
                },
            })
            result = prop_v3.bootstrap_state(directory, proposal_path)

        self.assertFalse(result["passed"])
        self.assertTrue(any("source hash mismatch" in issue for issue in result["issues"]))

    def test_generation_gate_and_section_context_use_canonical_public_projection(self):
        with tempfile.TemporaryDirectory() as directory:
            _make_state(directory)
            checked = prop_v3.check_canonical(directory, stage="generation")
            compiled = prop_v3.compile_context(directory, "section", target_id="CH-01")

        self.assertTrue(checked["passed"], checked["issues"])
        self.assertTrue(compiled["passed"], compiled["issues"])
        brief = compiled["brief"]
        self.assertEqual(brief["generation_snapshot_id"][:3], "GS-")
        self.assertEqual(brief["expected_realization_refs"], ["CL-CLOSED-LOOP", "DA-CLOSED-LOOP"])
        self.assertEqual(brief["expected_requirement_refs"], ["M-01", "S-01"])
        rendered = json.dumps(brief, ensure_ascii=False)
        self.assertNotIn("http", rendered)
        self.assertIn("EV-CAPABILITY", rendered)
        self.assertIn("项目经理配置证明", rendered)
        self.assertNotIn("敏感原始材料：某客户名称与金额", rendered)
        self.assertNotIn("formal_power", rendered)
        self.assertNotIn('"capacity"', rendered)

    def test_compiled_writer_and_redteam_contexts_redact_private_customer_semantics(self):
        documents = _valid_documents()
        documents["customer-value.json"]["roles"][0]["decision_concern"] = (
            "私密角色判断原句")
        documents["customer-value.json"]["needs"][0].update(
            name="私密需求名称", statement="私密需求原句",
            publication_status="publicly_supportable", source_visibility="private",
            approved_projection="公开需求投影",
        )
        documents["customer-value.json"]["criteria"][0].update(
            name="私密标准名称", statement="私密标准原句",
            publication_status="publicly_supportable",
            approved_projection="公开标准投影",
        )
        documents["strategy.json"]["open_questions"].append({
            "id": "GATE-PRIVATE-PREFERENCE", "title": "私密决策标题",
            "q": "内部偏好是什么？", "why_matters": "只影响内部判断",
            "ai_assumption": "不进入正文", "depends_on": [],
            "status": "assumed", "resolved": "不进入正文",
            "assumption_risk": True, "visibility": "private",
            "safe_constraint": "不得披露未经确认的内部偏好。",
            "affected_refs": [],
        })
        documents["intel-pool.json"]["evidence"].append({
            "id": "EV-PRIVATE-NOTE", "kind": "private_note",
            "title": "私密证据标题", "content": "私密证据原句",
            "source": "沟通纪要", "visibility": "private",
            "quality": "asserted_from_text", "status": "active",
            "allowed_uses": ["matching"],
        })
        with tempfile.TemporaryDirectory() as directory:
            _make_state(directory, documents)
            research = prop_v3.compile_context(directory, "research")
            section = prop_v3.compile_context(
                directory, "section", target_id="CH-01")
            redteam = prop_v3.compile_context(
                directory, "redteam", role="audit")

        self.assertTrue(research["passed"], research.get("issues"))
        self.assertTrue(section["passed"], section.get("issues"))
        self.assertTrue(redteam["passed"], redteam.get("issues"))
        rendered = json.dumps({
            "research": research["brief"],
            "section": section["brief"],
            "redteam": redteam["brief"],
        }, ensure_ascii=False)
        for secret in (
                "私密角色判断原句", "私密需求名称", "私密需求原句",
                "私密标准名称", "私密标准原句", "私密决策标题",
                "私密证据标题", "私密证据原句"):
            self.assertNotIn(secret, rendered)
        self.assertIn("GATE-PRIVATE-PREFERENCE", rendered)
        self.assertIn("不得披露未经确认的内部偏好。", rendered)
        self.assertIn("公开需求投影", rendered)
        self.assertIn("公开标准投影", rendered)
        self.assertNotIn("name", prop_v3._safe_need({
            "id": "NEED-PRIVATE", "name": "内部名称",
            "publication_status": "internal_only",
        }))

    def test_path_components_distinguish_unicode_ids(self):
        first = prop_v3._safe_path_component("章节甲")
        second = prop_v3._safe_path_component("章节乙")

        self.assertNotEqual(first, second)
        self.assertRegex(first, r"^[A-Za-z0-9_.-]+$")
        self.assertEqual(prop_v3._safe_path_component("CH-01"), "CH-01")
        self.assertNotIn(prop_v3._safe_path_component(".."), ("", ".", ".."))

    def test_report_qa_blocks_private_raw_wording_but_allows_approved_projection(self):
        with tempfile.TemporaryDirectory() as directory:
            _make_state(directory)
            report_path = os.path.join(directory, "report.md")
            prefix = "# 测试方案\n\n项目名称：测试\n\n## 目录\n\n## 应标响应与评分对照表\n\n"
            with open(report_path, "w", encoding="utf-8") as handle:
                handle.write(prefix + "敏感原始材料：某客户名称与金额\n")
            blocked = prop_tools.qa_proposal(
                report_path, "standard", os.path.join(directory, "strategy.json"),
                "zh", os.path.join(directory, "requirements.json"), directory)
            with open(report_path, "w", encoding="utf-8") as handle:
                handle.write(prefix + "已核验项目经理可用。\n")
            approved = prop_tools.qa_proposal(
                report_path, "standard", os.path.join(directory, "strategy.json"),
                "zh", os.path.join(directory, "requirements.json"), directory)

        self.assertFalse(blocked["checks"]["no_private_raw_leak"]["passed"])
        self.assertIn({"ref": "EV-CAPABILITY", "field": "content"},
                      blocked["checks"]["no_private_raw_leak"]["found"])
        self.assertTrue(approved["checks"]["no_private_raw_leak"]["passed"])

    def test_changeset_is_atomic_and_rejects_stale_or_forbidden_producer(self):
        with tempfile.TemporaryDirectory() as directory:
            documents = _make_state(directory)
            changeset = {
                "schema_version": "changeset/v1", "changeset_id": "CS-BAD",
                "producer": "task2.5",
                "base_revisions": {"customer-value.json": 1, "strategy.json": 1},
                "validate_stage": "draft",
                "operations": [
                    {"file": "customer-value.json", "op": "replace", "path": "/value_propositions/0/name", "value": "新名称"},
                    {"file": "strategy.json", "op": "replace", "path": "/decision_jobs/0/role_refs", "value": ["ROLE-MISSING"]},
                ],
                "affected_refs": ["VP-CLOSED-LOOP", "DJ-DELIVER"],
            }
            path = os.path.join(directory, "bad.json")
            _write_json(path, changeset)
            result = prop_v3.apply_changeset(directory, path)
            current = prop_v3._read_json(os.path.join(directory, "customer-value.json"))
            changeset["operations"] = [{
                "file": "customer-value.json", "op": "replace",
                "path": "/value_propositions/0/portfolio_role", "value": "supporting",
            }]
            _write_json(path, changeset)
            success = prop_v3.apply_changeset(directory, path)
            stale = prop_v3.apply_changeset(directory, path)
            changeset.update(changeset_id="CS-WRITER", producer="task3", base_revisions={"customer-value.json": 2})
            _write_json(path, changeset)
            forbidden = prop_v3.apply_changeset(directory, path)

        self.assertFalse(result["passed"])
        self.assertTrue(result["rolled_back"])
        self.assertEqual(current["value_propositions"][0]["name"], documents["customer-value.json"]["value_propositions"][0]["name"])
        self.assertEqual(current["revision"], 1)
        self.assertTrue(success["passed"], success.get("issues"))
        self.assertFalse(stale["passed"])
        self.assertTrue(stale["stale"])
        self.assertFalse(forbidden["passed"])

    def test_gate2_cannot_resolve_gate_and_migration_is_not_a_changeset_producer(self):
        with tempfile.TemporaryDirectory() as directory:
            gate2_dir = os.path.join(directory, "gate2")
            migration_dir = os.path.join(directory, "migration")
            os.makedirs(gate2_dir)
            os.makedirs(migration_dir)
            _make_state(gate2_dir)
            _make_state(migration_dir)

            changed = copy.deepcopy(_valid_documents()["strategy.json"]["open_questions"][0])
            changed["resolved"] = "由红队越权改写"
            gate2_path = os.path.join(gate2_dir, "gate2.json")
            _write_json(gate2_path, {
                "schema_version": "changeset/v1", "changeset_id": "CS-G2-BAD",
                "producer": "gate2", "base_revisions": {"strategy.json": 1},
                "operations": [{
                    "file": "strategy.json", "op": "replace",
                    "path": "/open_questions/0", "value": changed,
                }],
            })
            gate2_result = prop_v3.apply_changeset(gate2_dir, gate2_path)

            migration_path = os.path.join(migration_dir, "migration.json")
            _write_json(migration_path, {
                "schema_version": "changeset/v1", "changeset_id": "CS-MIG-BAD",
                "producer": "migration",
                "base_revisions": {"customer-value.json": 1},
                "operations": [{
                    "file": "customer-value.json", "op": "replace",
                    "path": "/value_propositions/0/name", "value": "越权改写",
                }],
            })
            migration_result = prop_v3.apply_changeset(
                migration_dir, migration_path)

        self.assertFalse(gate2_result["passed"])
        self.assertTrue(any(
            "cannot alter resolved Gate" in issue
            for issue in gate2_result["issues"]
        ), gate2_result["issues"])
        self.assertFalse(migration_result["passed"])
        self.assertTrue(any(
            "producer migration cannot mutate" in issue
            for issue in migration_result["issues"]
        ), migration_result["issues"])

    def test_changeset_requires_each_touched_base_and_task25_cannot_reauthorize(self):
        with tempfile.TemporaryDirectory() as directory:
            _make_state(directory)
            path = os.path.join(directory, "changeset.json")
            _write_json(path, {
                "schema_version": "changeset/v1", "changeset_id": "CS-NO-BASE",
                "producer": "task2.5", "base_revisions": {"customer-value.json": 1},
                "operations": [{
                    "file": "delivery-plan.json", "op": "replace",
                    "path": "/actions/0/name", "value": "扩大后的承诺动作",
                }],
            })
            missing_base = prop_v3.apply_changeset(directory, path)
            _write_json(path, {
                "schema_version": "changeset/v1", "changeset_id": "CS-T25-EXPAND",
                "producer": "task2.5", "base_revisions": {"delivery-plan.json": 1},
                "operations": [{
                    "file": "delivery-plan.json", "op": "replace",
                    "path": "/actions/0/name", "value": "扩大后的承诺动作",
                }],
            })
            expanded = prop_v3.apply_changeset(directory, path)
            _write_json(path, {
                "schema_version": "changeset/v1", "changeset_id": "CS-T25-VP-REWRITE",
                "producer": "task2.5", "base_revisions": {"customer-value.json": 1},
                "validate_stage": "generation",
                "operations": [{
                    "file": "customer-value.json", "op": "replace",
                    "path": "/value_propositions/0/expected_change",
                    "value": "保证实现100%营收增长并零风险交付",
                }],
            })
            rewritten_vp = prop_v3.apply_changeset(directory, path)
            _write_json(path, {
                "schema_version": "changeset/v1", "changeset_id": "CS-T25-NEED-REWRITE",
                "producer": "task2.5", "base_revisions": {"customer-value.json": 1},
                "operations": [{
                    "file": "customer-value.json", "op": "replace",
                    "path": "/needs/0/statement", "value": "未经授权改写的客户内部偏好",
                }],
            })
            rewritten_need = prop_v3.apply_changeset(directory, path)
            _write_json(path, {
                "schema_version": "changeset/v1", "changeset_id": "CS-T25-GATE",
                "producer": "task2.5", "base_revisions": {"strategy.json": 1},
                "operations": [{
                    "file": "strategy.json", "op": "replace",
                    "path": "/open_questions/0/resolved", "value": "Task2.5 自行批准",
                }],
            })
            fake_gate = prop_v3.apply_changeset(directory, path)

        self.assertFalse(missing_base["passed"])
        self.assertTrue(missing_base["stale"])
        self.assertFalse(expanded["passed"])
        self.assertTrue(any("authorized actions" in issue for issue in expanded["issues"]))
        self.assertFalse(rewritten_vp["passed"])
        self.assertTrue(any("cannot rewrite ValueProposition semantics" in issue for issue in rewritten_vp["issues"]))
        self.assertFalse(rewritten_need["passed"])
        self.assertTrue(any("customer semantics collection needs" in issue for issue in rewritten_need["issues"]))
        self.assertFalse(fake_gate["passed"])

    def test_fake_or_unrelated_authority_cannot_unlock_commitment(self):
        documents = _valid_documents()
        documents["customer-value.json"]["claims"][0]["authority_ref"] = "GATE-FAKE"
        documents["delivery-plan.json"]["actions"][0]["authority_ref"] = "M-01"
        with tempfile.TemporaryDirectory() as directory:
            _make_state(directory, documents)
            checked = prop_v3.check_canonical(directory, stage="generation")

        rules = {item["rule_id"] for item in checked["diagnostics"] if item["severity"] == "blocker"}
        self.assertFalse(checked["passed"])
        self.assertIn("claim.authority", rules)
        self.assertIn("action.authority", rules)

    def test_invalid_acceptance_authority_is_rejected_at_draft_boundary(self):
        documents = _valid_documents()
        requirements = documents["requirements.json"]
        requirements["deliverables"].append({
            "id": "D-01",
            "item": "提交阶段交付物",
            "acceptance_text": "文件可打开并可追溯",
        })
        action = documents["delivery-plan.json"]["actions"][0]
        action["requirement_refs"].append("D-01")
        acceptance = documents["delivery-plan.json"]["acceptance_contracts"][0]
        acceptance["authority_ref"] = "D-01"

        with tempfile.TemporaryDirectory() as directory:
            _make_state(directory, documents)
            invalid = prop_v3.check_canonical(directory, stage="draft")

            requirements["deliverables"][0].update(
                authority_uses=["commitment_authority"],
                authorizes_refs=["AC-CLOSED-LOOP"],
            )
            _make_state(directory, documents)
            repaired = prop_v3.check_canonical(directory, stage="draft")

        self.assertFalse(invalid["passed"])
        invalid_rules = {
            item["rule_id"] for item in invalid["diagnostics"]
            if item["severity"] == "fatal"
        }
        self.assertIn("acceptance.authority_scope", invalid_rules)
        self.assertTrue(repaired["passed"], repaired["issues"])

    def test_anonymized_and_allowed_use_evidence_are_hard_gated(self):
        missing_projection = _valid_documents()
        evidence = missing_projection["intel-pool.json"]["evidence"][1]
        evidence.pop("safe_title")
        evidence.pop("approved_projection")
        missing_use = _valid_documents()
        missing_use["intel-pool.json"]["evidence"][1]["allowed_uses"] = ["matching"]

        with tempfile.TemporaryDirectory() as directory:
            projection_dir = os.path.join(directory, "projection")
            use_dir = os.path.join(directory, "use")
            os.makedirs(projection_dir); os.makedirs(use_dir)
            _make_state(projection_dir, missing_projection)
            _make_state(use_dir, missing_use)
            projection_check = prop_v3.check_canonical(projection_dir, stage="generation")
            use_check = prop_v3.check_canonical(use_dir, stage="generation")

        self.assertTrue(any(item["rule_id"] == "evidence.anonymized_projection" for item in projection_check["diagnostics"]))
        self.assertTrue(any(item["rule_id"] == "claim.evidence_quality" for item in use_check["diagnostics"]))

    def test_third_party_evidence_cannot_prove_bidder_capability(self):
        documents = _valid_documents()
        evidence = documents["intel-pool.json"]["evidence"][1]
        evidence.update(kind="third_party_case", third_party=True)
        with tempfile.TemporaryDirectory() as directory:
            _make_state(directory, documents)
            checked = prop_v3.check_canonical(directory, stage="generation")

        self.assertFalse(checked["passed"])
        self.assertTrue(any(item["rule_id"] == "claim.evidence_quality" for item in checked["diagnostics"]))

    def test_strong_counter_evidence_blocks_publishable_target(self):
        documents = _valid_documents()
        documents["intel-pool.json"]["evidence"].append({
            "id": "EV-COUNTER", "kind": "verified_capability", "title": "能力限制",
            "content": "当前项目经理不可用于本合同", "source": "已核验排期",
            "visibility": "authorized_source", "quality": "verified", "status": "active",
            "allowed_uses": ["proposal_narrative"],
        })
        documents["customer-value.json"]["evidence_links"].append({
            "id": "EL-COUNTER", "evidence_ref": "EV-COUNTER",
            "target_ref": "CL-CLOSED-LOOP", "relation": "refutes",
            "strength": "direct", "scope": "本合同期", "reason": "排期直接冲突",
            "confidence": "high",
        })
        with tempfile.TemporaryDirectory() as directory:
            _make_state(directory, documents)
            checked = prop_v3.check_canonical(directory, stage="generation")

        self.assertFalse(checked["passed"])
        self.assertTrue(any(item["rule_id"] == "evidence.counter" for item in checked["diagnostics"]))

    def test_each_selected_action_requires_explicit_budget_treatment(self):
        documents = _valid_documents()
        documents["delivery-plan.json"]["actions"].append({
            "id": "DA-NO-COST-MAP", "name": "未归集预算的辅助动作",
            "selection_status": "selected", "readiness_status": "planned",
            "commitment_level": "intended", "required": False,
            "accountable_role_ref": "DR-PM", "responsible_role_refs": ["DR-PM"],
            "resource_refs": ["RES-PM"],
            "resource_demands": [{
                "resource_ref": "RES-PM", "time_window": "contract", "low": 0, "high": 0,
            }],
            "time_window": "contract", "dependency_refs": [], "acceptance_refs": [],
        })
        with tempfile.TemporaryDirectory() as directory:
            _make_state(directory, documents)
            checked = prop_v3.check_canonical(directory, stage="generation")

        self.assertTrue(checked["passed"], checked["issues"])
        self.assertTrue(any(item["rule_id"] == "budget.action_unmapped" for item in checked["diagnostics"]))
        budget_issue = next(
            item for item in checked["diagnostics"]
            if item["rule_id"] == "budget.action_unmapped"
        )
        self.assertEqual(budget_issue["blocks"], ["submission"])

    def test_delivery_cycle_and_requirement_transfer_are_blocked(self):
        documents = _valid_documents()
        action = documents["delivery-plan.json"]["actions"][0]
        action["predecessor_refs"] = ["DA-CLOSED-LOOP"]
        action["dependency_refs"] = ["DEP-CUSTOMER"]
        documents["delivery-plan.json"]["customer_dependencies"] = [{
            "id": "DEP-CUSTOMER", "input": "客户确认稿",
            "needed_by": "阶段制作前", "delay_impact": "顺延内部制作节奏",
            "fallback": "先完成不依赖确认的部分", "escalation_path": "项目联席确认",
            "transferred_requirement_refs": ["M-01"],
        }]
        with tempfile.TemporaryDirectory() as directory:
            _make_state(directory, documents)
            checked = prop_v3.check_canonical(directory, stage="generation")

        rules = {item["rule_id"] for item in checked["diagnostics"]}
        self.assertIn("delivery.precedence_cycle", rules)
        self.assertIn("dependency.responsibility_transfer", rules)

    def test_resource_portfolio_overload_blocks_submission(self):
        documents = _valid_documents()
        second = copy.deepcopy(documents["delivery-plan.json"]["actions"][0])
        second["id"] = "DA-SECOND"
        second["claim_refs"] = []
        second["value_proposition_refs"] = []
        second["resource_demands"] = [second["resource_demands"][0]]
        second["resource_demands"][0].update(low=2, high=2)
        documents["delivery-plan.json"]["actions"].append(second)
        with tempfile.TemporaryDirectory() as directory:
            _make_state(directory, documents)
            checked = prop_v3.check_canonical(directory, stage="generation")

        overloads = [item for item in checked["diagnostics"] if item["rule_id"] == "resource.overload"]
        self.assertEqual(len(overloads), 1)
        self.assertEqual(set(overloads[0]["subject_refs"]), {"RES-PM", "DA-CLOSED-LOOP", "DA-SECOND"})

    def test_budget_cap_requires_one_bounded_portfolio_envelope(self):
        missing_documents = _valid_documents()
        missing_documents["delivery-plan.json"]["resource_envelopes"] = [
            item for item in missing_documents["delivery-plan.json"]["resource_envelopes"]
            if item["id"] != "RES-BUDGET"
        ]
        missing_documents["delivery-plan.json"]["actions"][0]["resource_refs"] = ["RES-PM"]
        missing_documents["delivery-plan.json"]["actions"][0]["resource_demands"] = [
            {"resource_ref": "RES-PM", "time_window": "contract", "low": 1, "high": 1}
        ]
        over_documents = _valid_documents()
        for item in over_documents["delivery-plan.json"]["resource_envelopes"]:
            if item["id"] == "RES-BUDGET":
                item["capacity"]["high"] = 120

        with tempfile.TemporaryDirectory() as directory:
            missing_dir = os.path.join(directory, "missing")
            over_dir = os.path.join(directory, "over")
            os.makedirs(missing_dir); os.makedirs(over_dir)
            _make_state(missing_dir, missing_documents)
            _make_state(over_dir, over_documents)
            missing = prop_v3.check_canonical(missing_dir, stage="generation")
            over = prop_v3.check_canonical(over_dir, stage="generation")

        self.assertFalse(missing["passed"])
        self.assertTrue(any(item["rule_id"] == "budget.envelope" for item in missing["diagnostics"]))
        self.assertFalse(over["passed"])
        self.assertTrue(any(item["rule_id"] == "budget.cap" for item in over["diagnostics"]))

    def test_realization_and_submission_fit_require_semantic_audit(self):
        with tempfile.TemporaryDirectory() as directory:
            _make_state(directory)
            section_path = os.path.join(directory, "sections", "section-1.md")
            with open(section_path, "w", encoding="utf-8") as handle:
                handle.write("### 1.1 一条责任链闭环交付\n\n项目经理对阶段检查与验收闭环承担单一责任。\n")
            compiled = prop_v3.compile_context(directory, "section", target_id="CH-01")
            hints = {
                "schema_version": "realization-hints/v1",
                "section_ref": "CH-01",
                "snapshot_id": compiled["brief"]["generation_snapshot_id"],
                "brief_hash": compiled["brief"]["brief_hash"],
                "realizations": [
                {"canonical_ref": "CL-CLOSED-LOOP", "contribution": "prove", "quote": "项目经理对阶段检查与验收闭环承担单一责任。"},
                {"canonical_ref": "DA-CLOSED-LOOP", "contribution": "operationalize", "quote": "项目经理对阶段检查与验收闭环承担单一责任。"},
                ],
            }
            hints_path = os.path.join(directory, "hints.json")
            semantic_path = os.path.join(directory, "semantic.json")
            _write_json(hints_path, hints)
            without_semantic = prop_v3.audit_realization(
                directory, "CH-01", section_path, hints_path,
                compiled["output_path"], None,
            )
            _write_json(semantic_path, {
                "schema_version": "semantic-realization/v1",
                "section_ref": "CH-01",
                "snapshot_id": compiled["brief"]["generation_snapshot_id"],
                "brief_hash": compiled["brief"]["brief_hash"],
                "evaluator": "independent-test/v1",
                "evaluations": [
                    {"canonical_ref": "CL-CLOSED-LOOP", "semantic_status": "entailed", "observed_commitment_level": "committed", "reason": "原文等义", "confidence": "high"},
                    {"canonical_ref": "DA-CLOSED-LOOP", "semantic_status": "entailed", "observed_commitment_level": "committed", "reason": "动作已明确", "confidence": "high"},
                ],
                "requirement_evaluations": [
                    {"requirement_ref": "M-01", "status": "addressed", "quote": "项目经理对阶段检查与验收闭环承担单一责任。", "reason": "明确责任与验收闭环", "confidence": "high"},
                    {"requirement_ref": "S-01", "status": "addressed", "quote": "项目经理对阶段检查与验收闭环承担单一责任。", "reason": "实质回应人员责任与验收", "confidence": "high"},
                ],
                "unexpected_claims": [], "overall": "valid",
            })
            audited = prop_v3.audit_realization(
                directory, "CH-01", section_path, hints_path,
                compiled["output_path"], semantic_path,
            )
            summary_compiled = prop_v3.compile_context(directory, "exec-summary")
            summary_path = os.path.join(directory, "sections", "section-0.md")
            with open(summary_path, "w", encoding="utf-8") as handle:
                handle.write("项目经理对阶段检查与验收闭环承担单一责任。\n")
            summary_hints_path = os.path.join(directory, "summary-hints.json")
            summary_semantic_path = os.path.join(directory, "summary-semantic.json")
            _write_json(summary_hints_path, {
                "schema_version": "realization-hints/v1", "section_ref": "CH-00",
                "snapshot_id": summary_compiled["brief"]["generation_snapshot_id"],
                "brief_hash": summary_compiled["brief"]["brief_hash"],
                "realizations": [
                    {"canonical_ref": "CL-CLOSED-LOOP", "contribution": "summarize", "quote": "项目经理对阶段检查与验收闭环承担单一责任。"},
                    {"canonical_ref": "DA-CLOSED-LOOP", "contribution": "summarize", "quote": "项目经理对阶段检查与验收闭环承担单一责任。"},
                ],
            })
            _write_json(summary_semantic_path, {
                "schema_version": "semantic-realization/v1", "section_ref": "CH-00",
                "snapshot_id": summary_compiled["brief"]["generation_snapshot_id"],
                "brief_hash": summary_compiled["brief"]["brief_hash"],
                "evaluator": "independent-test/v1",
                "evaluations": [
                    {"canonical_ref": "CL-CLOSED-LOOP", "semantic_status": "entailed", "observed_commitment_level": "committed", "reason": "原文等义", "confidence": "high"},
                    {"canonical_ref": "DA-CLOSED-LOOP", "semantic_status": "entailed", "observed_commitment_level": "committed", "reason": "动作已明确", "confidence": "high"},
                ],
                "requirement_evaluations": [], "unexpected_claims": [], "overall": "valid",
            })
            summary_audited = prop_v3.audit_realization(
                directory, "CH-00", summary_path, summary_hints_path,
                summary_compiled["output_path"], summary_semantic_path,
            )
            submission = prop_v3.check_canonical(
                directory, stage="submission",
                realization_dir=os.path.join(directory, "derived", "realization"),
            )
            fit = prop_v3.customer_fit(directory, checkpoint="submission")

        self.assertFalse(without_semantic["passed"])
        self.assertEqual(without_semantic["manifest"]["status"], "needs_semantic_review")
        self.assertTrue(audited["passed"], audited["issues"])
        self.assertTrue(summary_compiled["passed"], summary_compiled.get("issues"))
        self.assertTrue(summary_audited["passed"], summary_audited["issues"])
        self.assertTrue(submission["passed"], submission["issues"])
        self.assertTrue(fit["passed"], fit["issues"])
        self.assertEqual(fit["scorecard"]["overall"]["rating"], "credible")
        self.assertNotIn("fit_range", fit["scorecard"]["overall"])
        self.assertIn("differentiation", fit["scorecard"]["uncertainty_drivers"])

    def test_realization_requires_registered_brief_metadata_and_addressed_requirements(self):
        with tempfile.TemporaryDirectory() as directory:
            _make_state(directory)
            section_path = os.path.join(directory, "sections", "section-1.md")
            with open(section_path, "w", encoding="utf-8") as handle:
                handle.write("### 1.1 责任闭环\n\n项目经理对阶段检查与验收闭环承担单一责任。\n")
            compiled = prop_v3.compile_context(directory, "section", target_id="CH-01")
            hints_path = os.path.join(directory, "hints.json")
            semantic_path = os.path.join(directory, "semantic.json")
            hints = {
                "schema_version": "realization-hints/v1", "section_ref": "CH-01",
                "snapshot_id": compiled["brief"]["generation_snapshot_id"],
                "brief_hash": compiled["brief"]["brief_hash"],
                "realizations": [
                    {"canonical_ref": "CL-CLOSED-LOOP", "contribution": "prove", "quote": "项目经理对阶段检查与验收闭环承担单一责任。"},
                    {"canonical_ref": "DA-CLOSED-LOOP", "contribution": "operationalize", "quote": "项目经理对阶段检查与验收闭环承担单一责任。"},
                ],
            }
            _write_json(hints_path, hints)
            no_brief = prop_v3.audit_realization(
                directory, "CH-01", section_path, hints_path, None, None)
            bad_hints = copy.deepcopy(hints)
            bad_hints.pop("snapshot_id")
            _write_json(hints_path, bad_hints)
            missing_meta = prop_v3.audit_realization(
                directory, "CH-01", section_path, hints_path,
                compiled["output_path"], None)
            _write_json(hints_path, hints)
            _write_json(semantic_path, {
                "schema_version": "semantic-realization/v1", "section_ref": "CH-01",
                "snapshot_id": compiled["brief"]["generation_snapshot_id"],
                "brief_hash": compiled["brief"]["brief_hash"],
                "evaluator": "independent-test/v1",
                "evaluations": [
                    {"canonical_ref": "CL-CLOSED-LOOP", "semantic_status": "entailed", "observed_commitment_level": "committed", "reason": "等义", "confidence": "high"},
                    {"canonical_ref": "DA-CLOSED-LOOP", "semantic_status": "entailed", "observed_commitment_level": "committed", "reason": "动作明确", "confidence": "high"},
                ],
                "requirement_evaluations": [
                    {"requirement_ref": "M-01", "status": "partial", "quote": "项目经理对阶段检查与验收闭环承担单一责任。", "reason": "未写完整执行方案", "confidence": "high"},
                    {"requirement_ref": "S-01", "status": "addressed", "quote": "项目经理对阶段检查与验收闭环承担单一责任。", "reason": "责任验收明确", "confidence": "high"},
                ],
                "unexpected_claims": [], "overall": "repair_required",
            })
            partial = prop_v3.audit_realization(
                directory, "CH-01", section_path, hints_path,
                compiled["output_path"], semantic_path)

        self.assertFalse(no_brief["passed"])
        self.assertFalse(missing_meta["passed"])
        self.assertIn("deprecated hints snapshot does not match brief", missing_meta["issues"])
        self.assertFalse(partial["passed"])
        self.assertIn("M-01", partial["manifest"]["missing_requirement_evaluations"] + [item["requirement_ref"] for item in partial["manifest"]["requirement_realizations"] if item["status"] != "addressed"])

    def test_sidecars_cannot_impersonate_authoritative_realization(self):
        with tempfile.TemporaryDirectory() as directory:
            _make_state(directory)
            realization_dir = os.path.join(directory, "derived", "realization")
            fake = {
                "schema_version": "realization/v1", "section_ref": "CH-01",
                "snapshot_id": "GS-FAKE", "status": "valid", "realizations": [],
            }
            _write_json(os.path.join(realization_dir, "CH-01.proposed.json"), fake)
            _write_json(os.path.join(realization_dir, "CH-01.semantic.json"), fake)
            premature_summary = prop_v3.compile_context(directory, "exec-summary")
            checked = prop_v3.check_canonical(
                directory, stage="submission", realization_dir=realization_dir)

        self.assertFalse(checked["passed"])
        self.assertFalse(premature_summary["passed"])
        self.assertTrue(any(
            item["rule_id"] == "realization.missing" and "CH-01" in item["subject_refs"]
            for item in checked["diagnostics"]))

    def test_private_only_evidence_cannot_publish(self):
        documents = _valid_documents()
        documents["intel-pool.json"]["evidence"][1]["visibility"] = "internal"
        with tempfile.TemporaryDirectory() as directory:
            _make_state(directory, documents)
            checked = prop_v3.check_canonical(directory, stage="generation")

        private = [item for item in checked["diagnostics"] if item["rule_id"] == "claim.private_only"]
        self.assertEqual(len(private), 1)
        self.assertIn("submission", private[0]["blocks"])

    def test_research_promotion_validates_and_updates_both_authorities(self):
        with tempfile.TemporaryDirectory() as directory:
            _make_state(directory)
            intel_path = os.path.join(directory, "proposals", "task2.intel.json")
            links_path = os.path.join(directory, "proposals", "task2.links.json")
            _write_json(intel_path, {
                "schema_version": "research-evidence/v1",
                "proposal_id": "CS-T2-NEW",
                "base_revisions": {"intel-pool.json": 1},
                "evidence_candidates": [{
                    "id": "EV-NEW-PUBLIC", "kind": "buyer_publication",
                    "title": "公开规划", "content": "采购人强调全过程留痕",
                    "source": "采购人官网", "url": "https://example.com/policy",
                    "visibility": "public", "quality": "high", "status": "active",
                    "allowed_uses": ["proposal_narrative"],
                }],
                "gaps": [],
                "manifest": {
                    "source_count": 1, "unique_domains": 1,
                    "fetch_method": "direct_fetch",
                    "counter_evidence_queries": 1, "intel_limited": False,
                },
            })
            _write_json(links_path, {
                "schema_version": "research-links/v1",
                "changeset_id": "CS-T2-NEW",
                "base_revisions": {"customer-value.json": 1},
                "link_candidates": [{
                    "id": "EL-NEW-PUBLIC", "evidence_ref": "EV-NEW-PUBLIC",
                    "target_ref": "VP-CLOSED-LOOP", "relation": "supports",
                    "strength": "medium", "scope": "本项目流程留痕价值",
                    "reason": "采购人公开规划直接支持过程可视化价值",
                    "confidence": "high",
                }],
            })
            result = prop_v3.promote_research(directory, intel_path, links_path)
            intel = prop_v3._read_json(os.path.join(directory, "intel-pool.json"))
            customer = prop_v3._read_json(os.path.join(directory, "customer-value.json"))
            stale = prop_v3.promote_research(directory, intel_path, links_path)

        self.assertTrue(result["passed"], result.get("issues"))
        self.assertEqual(result["promoted_evidence"], 1)
        self.assertEqual(intel["revision"], 2)
        self.assertEqual(customer["revision"], 2)
        self.assertIn("EV-NEW-PUBLIC", [item["id"] for item in intel["evidence"]])
        self.assertIn("EL-NEW-PUBLIC", [item["id"] for item in customer["evidence_links"]])
        self.assertEqual(intel["research_manifest"]["source_count"], 1)
        self.assertEqual(intel["research_manifest"]["fetch_method"], "direct_fetch")
        self.assertFalse(stale["passed"])

    def test_auto_state_unlocks_generation_but_blocks_submission(self):
        documents = _valid_documents()
        documents["strategy.json"]["open_questions"].append({
            "id": "GATE-NARRATIVE-CHOICE", "title": "表达顺序",
            "q": "是否先写客户风险？", "why_matters": "影响表达但不改变承诺",
            "ai_assumption": "先写客户风险", "depends_on": [], "status": "open",
            "resolved": None, "safe_constraint": "仅调整表达顺序。",
            "affected_refs": [], "assumption_risk": False,
        })
        with tempfile.TemporaryDirectory() as directory:
            _make_state(directory, documents)
            result = prop_v3.apply_auto_state(directory)
            generation = prop_v3.check_canonical(directory, stage="generation")
            strategy_fit = prop_v3.customer_fit(directory, checkpoint="strategy")
            submission = prop_v3.check_canonical(directory, stage="submission")

        self.assertTrue(result["passed"], result.get("issues"))
        self.assertEqual(result["converted"], 1)
        self.assertTrue(generation["passed"], generation["issues"])
        self.assertTrue(strategy_fit["passed"], strategy_fit["issues"])
        assumed = [item for item in submission["diagnostics"] if item["rule_id"] == "decision.assumed"]
        self.assertEqual(len(assumed), 1)
        self.assertFalse(submission["submission_ready"])

    def test_auto_state_revokes_commitments_bound_to_an_assumed_gate(self):
        documents = _valid_documents()
        decision = documents["strategy.json"]["open_questions"][0]
        decision.update(status="open", resolved=None, assumption_risk=False)
        with tempfile.TemporaryDirectory() as directory:
            _make_state(directory, documents)
            result = prop_v3.apply_auto_state(directory)
            customer = prop_v3._read_json(os.path.join(directory, "customer-value.json"))
            delivery = prop_v3._read_json(os.path.join(directory, "delivery-plan.json"))
            intel = prop_v3._read_json(os.path.join(directory, "intel-pool.json"))
            generation = prop_v3.check_canonical(directory, stage="generation")

        self.assertTrue(result["passed"], result.get("issues"))
        self.assertEqual(customer["claims"][0]["commitment_level"], "intended")
        self.assertEqual(customer["claims"][0]["status"], "draft_ready")
        self.assertIsNone(customer["claims"][0]["authority_ref"])
        self.assertEqual(delivery["actions"][0]["readiness_status"], "planned")
        self.assertEqual(delivery["resource_envelopes"][0]["status"], "unknown")
        self.assertEqual(intel["evidence"][1]["visibility"], "internal")
        self.assertTrue(generation["passed"], generation["issues"])

    def test_archive_preserves_previous_state_as_last_good(self):
        with tempfile.TemporaryDirectory() as directory:
            state = os.path.join(directory, "run")
            bundle = os.path.join(directory, "bundle")
            os.makedirs(state)
            _make_state(state)
            with open(os.path.join(state, "sections", "section-1.md"), "w", encoding="utf-8") as handle:
                handle.write("可恢复的章节正文\n")
            first = prop_v3.archive_state(state, bundle, require_submission_ready=False)
            strategy_path = os.path.join(state, "strategy.json")
            strategy = prop_v3._read_json(strategy_path)
            strategy["revision"] = 2
            _write_json(strategy_path, strategy)
            second = prop_v3.archive_state(state, bundle, require_submission_ready=False)
            archived = prop_v3._read_json(os.path.join(bundle, "_state", "strategy.json"))
            previous = prop_v3._read_json(os.path.join(bundle, "_state.last-good", "strategy.json"))
            with open(os.path.join(bundle, "_state", "sections", "section-1.md"), "r", encoding="utf-8") as handle:
                archived_section = handle.read()

        self.assertTrue(first["passed"], first.get("issues"))
        self.assertTrue(second["passed"], second.get("issues"))
        self.assertEqual(archived["revision"], 2)
        self.assertEqual(previous["revision"], 1)
        self.assertEqual(archived_section, "可恢复的章节正文\n")

    def test_archive_promotion_failure_preserves_target_and_last_good(self):
        with tempfile.TemporaryDirectory() as directory:
            state = os.path.join(directory, "run")
            bundle = os.path.join(directory, "bundle")
            os.makedirs(state)
            _make_state(state)
            first = prop_v3.archive_state(
                state, bundle, require_submission_ready=False
            )
            self.assertTrue(first["passed"], first.get("issues"))

            strategy_path = os.path.join(state, "strategy.json")
            strategy = prop_v3._read_json(strategy_path)
            strategy["revision"] = 2
            _write_json(strategy_path, strategy)
            second = prop_v3.archive_state(
                state, bundle, require_submission_ready=False
            )
            self.assertTrue(second["passed"], second.get("issues"))

            target = os.path.join(bundle, "_state")
            last_good = os.path.join(bundle, "_state.last-good")
            target_before = prop_v3._read_json(os.path.join(target, "strategy.json"))
            last_good_before = prop_v3._read_json(
                os.path.join(last_good, "strategy.json")
            )
            strategy["revision"] = 3
            _write_json(strategy_path, strategy)

            real_replace = os.replace
            promotion_calls = []

            def fail_staging_promotion(source, destination):
                if (os.path.basename(os.fspath(source)).startswith(
                        "._state-staging-")
                        and os.fspath(destination) == target):
                    promotion_calls.append(
                        (os.fspath(source), os.fspath(destination))
                    )
                    raise OSError("injected state promotion failure")
                return real_replace(source, destination)

            with mock.patch.object(
                    prop_v3.os, "replace", side_effect=fail_staging_promotion):
                failed = prop_v3.archive_state(
                    state, bundle, require_submission_ready=False
                )

            target_preserved = os.path.isdir(target) and bool(os.listdir(target))
            last_good_preserved = (
                os.path.isdir(last_good) and bool(os.listdir(last_good))
            )
            claimed_preserved = any(
                "last-good preserved" in issue for issue in failed["issues"]
            )
            self.assertFalse(failed["passed"])
            self.assertEqual(promotion_calls[0][1], target)
            self.assertTrue(target_preserved)
            self.assertTrue(last_good_preserved)
            self.assertEqual(claimed_preserved, last_good_preserved)
            if target_preserved:
                target_after = prop_v3._read_json(
                    os.path.join(target, "strategy.json")
                )
                self.assertEqual(target_after["revision"], target_before["revision"])
            if last_good_preserved:
                last_good_after = prop_v3._read_json(
                    os.path.join(last_good, "strategy.json")
                )
                self.assertEqual(
                    last_good_after["revision"], last_good_before["revision"]
                )
            self.assertFalse(any(
                name.startswith("._state-staging-") for name in os.listdir(bundle)
            ))

    def test_allow_draft_archive_refuses_corrupt_canonical(self):
        with tempfile.TemporaryDirectory() as directory:
            state = os.path.join(directory, "run")
            bundle = os.path.join(directory, "bundle")
            os.makedirs(state)
            _make_state(state)
            first = prop_v3.archive_state(state, bundle, require_submission_ready=False)
            with open(os.path.join(state, "requirements.json"), "w", encoding="utf-8") as handle:
                handle.write("{not-json")
            corrupt = prop_v3.archive_state(state, bundle, require_submission_ready=False)
            archived = prop_v3._read_json(os.path.join(bundle, "_state", "requirements.json"))

        self.assertTrue(first["passed"])
        self.assertFalse(corrupt["passed"])
        self.assertEqual(archived["schema_version"], "requirements/v3")

    def test_lean_schema_embeds_paths_jobs_outputs_and_reuses_snapshot(self):
        documents = _lean_documents()
        with tempfile.TemporaryDirectory() as directory:
            _make_state(directory, documents)
            checked = prop_v3.check_canonical(directory, stage="generation")
            first = prop_v3.compile_context(
                directory, "section", target_id="CH-01")
            second = prop_v3.compile_context(
                directory, "section", target_id="CH-01")
            artifact_registry_exists = os.path.exists(os.path.join(
                directory, "derived", "manifests", "artifacts.json"))

        self.assertTrue(checked["passed"], checked["issues"])
        self.assertEqual(
            documents["customer-value.json"]["schema_version"],
            "customer-value/v2")
        self.assertIn("decision_paths", documents["customer-value.json"])
        self.assertNotIn("role_need_links", documents["customer-value.json"])
        self.assertEqual(
            documents["strategy.json"]["schema_version"], "strategy/v4")
        self.assertNotIn("decision_jobs", documents["strategy.json"])
        self.assertIn("decision_job", documents["strategy.json"]["sections"][0])
        self.assertEqual(
            first["brief"]["expected_visible_output_refs"],
            ["OUT-RESPONSIBILITY-CARD"])
        self.assertIn("narrative_guide", first["brief"]["common"])
        self.assertFalse(first["snapshot_reused"])
        self.assertTrue(second["snapshot_reused"])
        self.assertFalse(artifact_registry_exists)

    def test_lean_lead_requires_small_visible_output_contract(self):
        documents = _lean_documents()
        documents["strategy.json"]["sections"][0]["visible_outputs"] = []
        with tempfile.TemporaryDirectory() as directory:
            _make_state(directory, documents)
            checked = prop_v3.check_canonical(directory, stage="generation")

        self.assertFalse(checked["passed"])
        self.assertTrue(any(
            item["rule_id"] == "visible_output.lead_missing"
            for item in checked["diagnostics"]
        ))

    def test_safe_draft_allows_unknown_budget_without_invented_range(self):
        documents = _lean_documents()
        claim = documents["customer-value.json"]["claims"][0]
        claim.update(status="draft_ready", commitment_level="intended")
        claim["authority_ref"] = None
        action = documents["delivery-plan.json"]["actions"][0]
        action.update(
            readiness_status="planned", commitment_level="intended",
            required=False, resource_refs=["RES-PM"],
            resource_demands=[{
                "resource_ref": "RES-PM", "time_window": "contract",
                "low": 1, "high": 1,
            }], authority_ref=None,
        )
        budget = documents["delivery-plan.json"]["resource_envelopes"][1]
        budget.update(status="unknown", capacity={"low": None, "high": None})
        budget.pop("approved_allocation", None)
        decision = documents["strategy.json"]["open_questions"][1]
        decision.update(status="open", resolved=None, assumption_risk=False)

        with tempfile.TemporaryDirectory() as directory:
            _make_state(directory, documents)
            generation = prop_v3.check_canonical(
                directory, stage="generation")
            submission = prop_v3.check_canonical(
                directory, stage="submission")

        self.assertTrue(generation["passed"], generation["issues"])
        self.assertTrue(generation["safe_draft_ready"])
        self.assertEqual(generation["readiness"], "safe_draft_ready")
        self.assertFalse(submission["passed"])
        self.assertTrue(any(
            item["rule_id"] in ("decision.open", "budget.action_unmapped")
            for item in submission["diagnostics"]
        ))

    def test_direct_semantic_audit_fills_visible_output_and_ordinal_fit(self):
        with tempfile.TemporaryDirectory() as directory:
            _make_submission_ready_lean_state(directory)
            submission = prop_v3.check_canonical(
                directory, stage="submission",
                realization_dir=os.path.join(directory, "derived", "realization"))
            fit = prop_v3.customer_fit(directory, checkpoint="submission")

        self.assertTrue(submission["passed"], submission["issues"])
        self.assertTrue(fit["passed"], fit["issues"])
        self.assertEqual(fit["scorecard"]["overall"]["rating"], "credible")
        self.assertNotIn("fit_range", fit["scorecard"]["overall"])
        self.assertFalse(any(
            "weight_range" in item for item in fit["scorecard"]["dimensions"]
        ))

    def test_manifest_self_attestation_rejects_hand_edit_even_for_draft_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            state = os.path.join(directory, "run")
            bundle = os.path.join(directory, "bundle")
            os.makedirs(state)
            _make_submission_ready_lean_state(state)
            manifest_path = os.path.join(
                state, "derived", "realization", "CH-01.json")
            manifest = prop_v3._read_json(manifest_path)
            manifest["status"] = "valid" if manifest["status"] != "valid" else "invalid"
            _write_json(manifest_path, manifest)
            checked = prop_v3.check_canonical(
                state, stage="submission",
                realization_dir=os.path.join(state, "derived", "realization"))
            archived = prop_v3.archive_state(
                state, bundle, require_submission_ready=False,
                checked_result=checked)

        self.assertFalse(checked["passed"])
        self.assertTrue(any(
            item["rule_id"] == "realization.attestation"
            for item in checked["diagnostics"]
        ))
        self.assertFalse(archived["passed"])
        self.assertIn("fatal corruption", archived["issues"][0])

    def test_finalize_run_reuses_one_canonical_check_and_binds_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            state = os.path.join(directory, "run")
            bundle = os.path.join(directory, "bundle")
            os.makedirs(state)
            _make_submission_ready_lean_state(state)
            report_path = os.path.join(directory, "report.md")
            with open(report_path, "w", encoding="utf-8") as handle:
                handle.write(
                    "# 客户价值测试方案\n\n"
                    "项目名称：客户价值测试项目\n\n"
                    "## 目录\n\n一、以单一责任链保障稳定交付\n\n"
                    "## 应标响应与评分对照表\n\n"
                    "| 要求 | 响应 |\n|:---|:---|\n| 完整执行方案 | 第一章 |\n\n"
                    "## 方案综述\n\n项目经理承担阶段检查与验收责任。\n\n"
                    "## 一、以单一责任链保障稳定交付\n\n"
                    "### 1.1 责任与检查节点\n\n"
                    "项目经理对阶段检查与验收闭环承担单一责任。\n\n"
                    "责任人：项目经理；检查节点：每个阶段交付前。\n"
                )
            gate2_path = os.path.join(directory, "gate2.json")
            _write_json(gate2_path, {
                "schema_version": "gate2-decision/v1",
                "status": "resolved", "open_root_causes": [],
            })
            with mock.patch.object(
                    prop_v3, "check_canonical",
                    wraps=prop_v3.check_canonical) as checked:
                result = prop_tools.finalize_run(
                    state, report_path, bundle, gate2_path=gate2_path)
            receipt = prop_v3._read_json(result["receipt_output"])

        self.assertTrue(result["passed"], result["issues"])
        self.assertTrue(result["submission_ready"])
        self.assertEqual(checked.call_count, 1)
        self.assertEqual(receipt["state_hash"], result["validation"]["state_hash"])
        self.assertEqual(
            receipt["report_hash"], result["validation"]["report_hash"])
        self.assertRegex(receipt["receipt_hash"], r"^sha256:[0-9a-f]{64}$")

    def test_legacy_migration_is_non_destructive_and_conservative(self):
        with tempfile.TemporaryDirectory() as directory:
            legacy = os.path.join(directory, "legacy")
            migrated = os.path.join(directory, "v3")
            os.makedirs(legacy)
            os.makedirs(migrated)
            marker_path = os.path.join(migrated, "migration-note.txt")
            with open(marker_path, "w", encoding="utf-8") as handle:
                handle.write("保留现有输入")
            _write_json(os.path.join(legacy, "requirements.json"), {
                "project_name": "旧项目", "mandatory": [],
                "scoring": [{"id": "S1", "item": "方案", "weight": 10}],
            })
            _write_json(os.path.join(legacy, "strategy.json"), {
                "title": "旧项目", "depth_mode": "standard",
                "narrative": {"mode": "logic", "rationale": "", "through_line": ""},
                "buyer_insight": "采购人希望降低管理负担",
                "differentiators": [{"point": "自动看板", "why_wow": "少盯过程"}],
                "decision_map": {"destination": "完成方案", "not_yet_specified": [], "out_of_scope": []},
                "open_questions": [],
                "sections": [{"n": 1, "title": "方案", "addresses": ["S1"]}],
            })
            _write_json(os.path.join(legacy, "intel.json"), [{
                "topic": "旧公开研究",
                "facts": [{"fact": "公开事实", "url": "https://example.com", "conf": "high"}],
                "cases": [{"name": "第三方案例", "url": "https://example.com/case", "what": "行业做法"}],
                "insights": ["旧内部洞察"],
            }])
            before = prop_v3.file_hash(os.path.join(legacy, "strategy.json"))
            result = prop_v3.migrate_state(legacy, migrated)
            after = prop_v3.file_hash(os.path.join(legacy, "strategy.json"))
            customer = prop_v3._read_json(os.path.join(migrated, "customer-value.json"))
            with open(marker_path, "r", encoding="utf-8") as handle:
                marker = handle.read()

        self.assertTrue(result["passed"], result["issues"])
        self.assertEqual(before, after)
        self.assertEqual(customer["value_propositions"][0]["status"], "candidate")
        self.assertEqual(customer["needs"][0]["publication_status"], "internal_only")
        self.assertTrue(result["source_unchanged"])
        self.assertEqual(marker, "保留现有输入")


if __name__ == "__main__":
    unittest.main()
