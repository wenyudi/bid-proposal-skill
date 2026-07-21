#!/usr/bin/env python3
"""proposal v4 轻量校验工具。

两个确定性子命令，替下游图片工作流和评标现场兜底那些"模型不该自觉"的错误：

  validate-blueprint  校验 presentation-blueprint/v1 结构稿，通过后确定性写 outline.md
  validate-index      校验响应对照索引：引用章节真实存在、评分项无漏行、虚构行有风险登记

只用标准库。JSON/Markdown 一律按 UTF-8 无 BOM 读写。
每个子命令打印一个 JSON 结果并以 0（passed）/ 1（failed）退出。
"""

import argparse
import json
import os
import re
import sys

VALID_MODES = {"generate", "strict_input", "style_reference"}
VALID_STATUS = {"generate", "available", "needs_user"}
VALID_COVERAGE = {"完整", "部分", "虚构补全", "待实件"}

# 上屏文案不允许出现的内部痕迹
URL_RE = re.compile(r"https?://|www\.", re.IGNORECASE)
INTERNAL_MARKER_RE = re.compile(
    r"(?:GATE-|VP-|CL-|DA-|RES-|AC-|snapshot|canonical|_state|schema_version)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------- helpers

def _load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _read_text(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _write_text(path, text):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def _result(passed, errors, warnings, extra=None):
    out = {"passed": bool(passed and not errors), "errors": errors, "warnings": warnings}
    if extra:
        out.update(extra)
    return out


def _norm_heading(text):
    """去掉 markdown 标记与中/英文编号前缀，返回可比较的标题正文。"""
    t = text.strip().lstrip("#").strip()
    # 去掉 "三、" "3." "3.1 " "(1)" 等前缀
    t = re.sub(r"^[（(]?[0-9]+[)）]?[、.．：: ]+", "", t)
    t = re.sub(r"^[一二三四五六七八九十百]+[、.．：: ]+", "", t)
    return t.strip()


def _doc_headings(doc_text):
    heads = []
    for line in doc_text.splitlines():
        if line.lstrip().startswith("#"):
            heads.append(_norm_heading(line))
    return [h for h in heads if h]


def _id_in_text(item_id, text):
    """item_id 作为独立 token 出现（避免 S1 命中 S10）。"""
    return re.search(r"(?<![0-9A-Za-z])" + re.escape(item_id) + r"(?![0-9])", text) is not None


def _parse_md_table(text):
    """把第一张 markdown 表格解析为 [[cell,...], ...]（跳过表头与分隔行）。"""
    rows = []
    seen_header = False
    for line in text.splitlines():
        s = line.strip()
        if not (s.startswith("|") and s.endswith("|")):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if re.match(r"^[:\- ]+$", "".join(cells)):  # 分隔行
            continue
        if not seen_header:
            seen_header = True  # 第一条是表头
            continue
        rows.append(cells)
    return rows


# ---------------------------------------------------------------- blueprint

def validate_blueprint(bp, blueprint_path, assets_root):
    errors, warnings = [], []

    if bp.get("schema_version") != "presentation-blueprint/v1":
        errors.append("schema_version 必须为 presentation-blueprint/v1")

    deck = bp.get("deck") or {}
    slides = bp.get("slides")
    if not isinstance(slides, list) or not slides:
        errors.append("slides 必须为非空数组")
        return _result(False, errors, warnings)

    # 页码连续 1..N
    ns = [s.get("n") for s in slides]
    if sorted(ns) != list(range(1, len(slides) + 1)):
        errors.append("slides 的 n 必须是从 1 开始的连续页码，无重复无跳号")

    ordered = sorted(slides, key=lambda s: (s.get("n") or 0))

    # core 全部在 appendix 之前
    seen_appendix = False
    for s in ordered:
        track = s.get("track")
        if track not in ("core", "appendix"):
            errors.append(f"slide {s.get('id')} 的 track 必须是 core 或 appendix")
        if track == "appendix":
            seen_appendix = True
        elif track == "core" and seen_appendix:
            errors.append(f"slide {s.get('id')} 是 core，却排在 appendix 之后")

    # 逐页字段 + 上屏文案 + 素材 + 证据图红线
    ids = []
    sig_ids = []
    core_ids = []
    appendix_ids = []
    needs_user = 0
    for s in ordered:
        sid = s.get("id")
        ids.append(sid)
        if s.get("track") == "core":
            core_ids.append(sid)
        elif s.get("track") == "appendix":
            appendix_ids.append(sid)
        for field in ("id", "role", "emphasis", "title"):
            if not s.get(field):
                errors.append(f"slide {sid} 缺字段 {field}")
        rt = s.get("render_text") or {}
        if rt.get("title") != s.get("title"):
            errors.append(f"slide {sid} 的 render_text.title 必须与 title 完全一致")
        if s.get("role") == "signature" and s.get("emphasis") == "signature":
            sig_ids.append(sid)

        # 上屏文案不含 URL / 内部 ref
        for chunk in _onscreen_strings(s):
            if URL_RE.search(chunk):
                errors.append(f"slide {sid} 上屏文案含 URL：{chunk[:40]}")
            if INTERNAL_MARKER_RE.search(chunk):
                errors.append(f"slide {sid} 上屏文案含内部 ref：{chunk[:40]}")

        # unverified_notes 必须是列表
        un = s.get("unverified_notes")
        if un is not None and not isinstance(un, list):
            errors.append(f"slide {sid} 的 unverified_notes 必须是数组")

        # 素材请求
        visual = s.get("visual") or {}
        for a in visual.get("asset_requests") or []:
            aid = a.get("asset_id")
            for field in ("asset_id", "role", "mode", "status"):
                if not a.get(field):
                    errors.append(f"slide {sid} 素材 {aid} 缺字段 {field}")
            if a.get("mode") not in VALID_MODES:
                errors.append(f"slide {sid} 素材 {aid} mode 非法：{a.get('mode')}")
            if a.get("status") not in VALID_STATUS:
                errors.append(f"slide {sid} 素材 {aid} status 非法：{a.get('status')}")
            # 证据图红线
            if a.get("evidence") is True and a.get("mode") == "generate":
                errors.append(
                    f"slide {sid} 素材 {aid} 是证据图（evidence=true），禁止 generate；"
                    f"只能 strict_input + needs_user 真实素材"
                )
            if a.get("status") == "needs_user":
                needs_user += 1
            if a.get("status") == "available":
                path = a.get("path")
                if not path:
                    errors.append(f"slide {sid} 素材 {aid} status=available 但缺 path")
                else:
                    base = assets_root or os.path.dirname(os.path.abspath(blueprint_path))
                    if not os.path.exists(os.path.join(base, path)):
                        errors.append(f"slide {sid} 素材 {aid} 路径不存在：{path}")
            if a.get("rights_status") == "needs_review":
                warnings.append(f"slide {sid} 素材 {aid} rights_status=needs_review，生成前需确认")

    if len(set(ids)) != len(ids):
        errors.append("slide id 必须全稿唯一")

    # 唯一 signature + sample 映射
    if len(sig_ids) != 1:
        errors.append(f"必须恰有一张 signature 页（role=signature 且 emphasis=signature），当前 {len(sig_ids)}")
    else:
        if deck.get("signature_slide_ref") != sig_ids[0]:
            errors.append("deck.signature_slide_ref 必须指向唯一 signature 页")
        if deck.get("sample_slide_ref") != sig_ids[0]:
            errors.append("deck.sample_slide_ref 必须与 signature 页相同")

    # story_arc：每个 core 页恰一次；appendix 不进 arc
    arc_refs = []
    for beat in deck.get("story_arc") or []:
        arc_refs.extend(beat.get("slide_refs") or [])
    for cid in core_ids:
        c = arc_refs.count(cid)
        if c != 1:
            errors.append(f"core 页 {cid} 在 story_arc 中应恰好出现一次，实际 {c}")
    for aid in appendix_ids:
        if aid in arc_refs:
            errors.append(f"appendix 页 {aid} 不应进入 story_arc")

    extra = {
        "slides": len(slides),
        "core": len(core_ids),
        "appendix": len(appendix_ids),
        "signature_slide": sig_ids[0] if len(sig_ids) == 1 else None,
        "needs_user_assets": needs_user,
    }
    return _result(True, errors, warnings, extra)


def _onscreen_strings(slide):
    out = [slide.get("title") or ""]
    rt = slide.get("render_text") or {}
    for v in rt.values():
        if isinstance(v, str):
            out.append(v)
        elif isinstance(v, list):
            out.extend([x for x in v if isinstance(x, str)])
    return [s for s in out if s]


def _write_outline(bp, output_dir):
    deck = bp.get("deck") or {}
    ordered = sorted(bp.get("slides") or [], key=lambda s: (s.get("n") or 0))
    lines = ["# 演示大纲（结构稿，待页序确认）", ""]
    lines.append("> 状态：ready_for_outline_review · 图片未生成 · 事实以 deck-blueprint.json 为准")
    lines.append("")
    lines.append(f"**主张**：{deck.get('core_thesis', '')}")
    lines.append("")
    for track, label in (("core", "核心轨"), ("appendix", "附录轨")):
        rows = [s for s in ordered if s.get("track") == track]
        if not rows:
            continue
        lines.append(f"## {label}")
        for s in rows:
            assets = (s.get("visual") or {}).get("asset_requests") or []
            amark = "、".join(f"{a.get('mode')}:{a.get('status')}" for a in assets) or "—"
            flag = " ⚠待核实" if s.get("unverified_notes") else ""
            star = "★" if s.get("emphasis") == "signature" else ""
            lines.append(
                f"{s.get('n')}. [{s.get('role')}]{star} {s.get('title')} "
                f"— {s.get('audience_takeaway', '')}；素材：{amark}{flag}"
            )
        lines.append("")
    _write_text(os.path.join(output_dir, "outline.md"), "\n".join(lines).rstrip() + "\n")


def cmd_validate_blueprint(args):
    bp = _load_json(args.blueprint)
    res = validate_blueprint(bp, args.blueprint, args.assets_root)
    if res["passed"] and args.output_dir:
        _write_outline(bp, args.output_dir)
        validation = {
            "schema_version": "presentation-validation/v1",
            "status": "ready_for_outline_review",
            "image_generation_started": False,
            "slides": res.get("slides"),
            "core": res.get("core"),
            "appendix": res.get("appendix"),
            "signature_slide": res.get("signature_slide"),
            "needs_user_assets": res.get("needs_user_assets"),
            "warnings": res.get("warnings"),
        }
        _write_text(
            os.path.join(args.output_dir, "presentation-validation.json"),
            json.dumps(validation, ensure_ascii=False, indent=2) + "\n",
        )
        res["outline"] = os.path.join(args.output_dir, "outline.md")
    return res


# ---------------------------------------------------------------- index

def validate_index(index_text, doc_text, score_table, risk_text):
    errors, warnings = [], []

    if not score_table.get("has_score_table", True):
        return _result(True, errors, warnings, {"note": "无评分表，跳过对照索引校验"})

    items = score_table.get("items") or []
    if not items:
        errors.append("score-table.items 为空")
        return _result(False, errors, warnings)

    headings = _doc_headings(doc_text)
    rows = _parse_md_table(index_text)
    if not rows:
        errors.append("响应对照索引没有可解析的表格行")
        return _result(False, errors, warnings)

    # 每个评分项在索引中恰有一行
    for it in items:
        iid = it.get("id")
        hits = [r for r in rows if _id_in_text(iid, r[0])] if iid else []
        if len(hits) == 0:
            errors.append(f"评分项 {iid} 在响应对照索引中缺行")
        elif len(hits) > 1:
            errors.append(f"评分项 {iid} 在索引中出现 {len(hits)} 行，应恰好一行")

    # 每行：章节位置真实存在 + 覆盖状态合法 + 虚构补全须有风险登记
    for r in rows:
        if len(r) < 4:
            errors.append(f"索引行列数不足（需 评分项|权重|章节位置|覆盖状态）：{r}")
            continue
        item_cell, _weight, sect_cell, cover_cell = r[0], r[1], r[2], r[3]
        cover = cover_cell.strip()
        if cover not in VALID_COVERAGE:
            errors.append(f"覆盖状态非法：'{cover}'（应为 完整/部分/虚构补全）")
        sect = _norm_heading(sect_cell)
        if not any(sect and (sect in h or h in sect) for h in headings):
            errors.append(f"索引引用的章节在正文中不存在：'{sect_cell}'")
        if cover == "虚构补全" and risk_text is not None:
            key_id = next((it.get("id") for it in items if it.get("id") and _id_in_text(it["id"], item_cell)), None)
            hit = (key_id and _id_in_text(key_id, risk_text)) or (sect and sect in risk_text)
            if not hit:
                errors.append(f"覆盖状态为'虚构补全'的行未在 _风险与待核实.md 找到对应登记：{item_cell[:30]}")

    return _result(True, errors, warnings, {"items": len(items), "rows": len(rows)})


def cmd_validate_index(args):
    return validate_index(
        _read_text(args.index),
        _read_text(args.doc),
        _load_json(args.score_table),
        _read_text(args.risk) if args.risk else None,
    )


# ---------------------------------------------------------------- cli

def main(argv=None):
    parser = argparse.ArgumentParser(prog="prop_tools", description="proposal v4 校验工具")
    sub = parser.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("validate-blueprint", help="校验 PPT 结构稿并写 outline")
    b.add_argument("--blueprint", required=True)
    b.add_argument("--output-dir", default=None)
    b.add_argument("--assets-root", default=None)
    b.set_defaults(func=cmd_validate_blueprint)

    i = sub.add_parser("validate-index", help="校验响应对照索引")
    i.add_argument("--index", required=True)
    i.add_argument("--doc", required=True)
    i.add_argument("--score-table", required=True)
    i.add_argument("--risk", default=None)
    i.set_defaults(func=cmd_validate_index)

    args = parser.parse_args(argv)
    res = args.func(args)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res.get("passed") else 1


if __name__ == "__main__":
    sys.exit(main())
