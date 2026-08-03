"""proposal v4 校验工具测试：validate-blueprint 与 validate-index 的正反例。"""

import copy
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import prop_tools  # noqa: E402

FIX = os.path.join(ROOT, "tests", "fixtures")


def _json(name):
    with open(os.path.join(FIX, name), encoding="utf-8") as f:
        return json.load(f)


def _text(name):
    with open(os.path.join(FIX, name), encoding="utf-8") as f:
        return f.read()


class BlueprintTests(unittest.TestCase):
    def setUp(self):
        self.bp = _json("blueprint-good.json")
        self.path = os.path.join(FIX, "blueprint-good.json")

    def test_good_passes_and_writes_outline(self):
        res = prop_tools.validate_blueprint(self.bp, self.path, None)
        self.assertTrue(res["passed"], res["errors"])
        self.assertEqual(res["signature_slide"], "s3")
        self.assertEqual(res["needs_user_assets"], 1)
        with tempfile.TemporaryDirectory() as d:
            rc = prop_tools.main(["validate-blueprint", "--blueprint", self.path, "--output-dir", d])
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.exists(os.path.join(d, "outline.md")))
            with open(os.path.join(d, "outline.md"), encoding="utf-8") as of:
                self.assertIn("素材替换清单", of.read())
            self.assertTrue(os.path.exists(os.path.join(d, "presentation-validation.json")))
            with open(os.path.join(d, "presentation-validation.json"), encoding="utf-8") as vf:
                val = json.load(vf)
            self.assertEqual(val["status"], "ready_for_outline_review")
            self.assertFalse(val["image_generation_started"])

    def test_evidence_image_generate_fails(self):
        bp = copy.deepcopy(self.bp)
        bp["slides"][3]["visual"]["asset_requests"][0]["mode"] = "generate"
        res = prop_tools.validate_blueprint(bp, self.path, None)
        self.assertFalse(res["passed"])
        self.assertTrue(any("证据图" in e for e in res["errors"]), res["errors"])

    def test_duplicate_signature_fails(self):
        bp = copy.deepcopy(self.bp)
        bp["slides"][0]["role"] = "signature"
        bp["slides"][0]["emphasis"] = "signature"
        res = prop_tools.validate_blueprint(bp, self.path, None)
        self.assertFalse(res["passed"])
        self.assertTrue(any("signature" in e for e in res["errors"]), res["errors"])

    def test_page_number_gap_fails(self):
        bp = copy.deepcopy(self.bp)
        bp["slides"][3]["n"] = 5
        res = prop_tools.validate_blueprint(bp, self.path, None)
        self.assertFalse(res["passed"])

    def test_story_arc_missing_core_fails(self):
        bp = copy.deepcopy(self.bp)
        bp["deck"]["story_arc"] = bp["deck"]["story_arc"][:2]  # 丢掉 s3 的 beat
        res = prop_tools.validate_blueprint(bp, self.path, None)
        self.assertFalse(res["passed"])
        self.assertTrue(any("story_arc" in e for e in res["errors"]), res["errors"])

    def test_render_title_mismatch_fails(self):
        bp = copy.deepcopy(self.bp)
        bp["slides"][0]["render_text"]["title"] = "与标题不一致"
        res = prop_tools.validate_blueprint(bp, self.path, None)
        self.assertFalse(res["passed"])

    def test_onscreen_url_fails(self):
        bp = copy.deepcopy(self.bp)
        bp["slides"][0]["render_text"]["key_points"].append("详见 https://example.com")
        res = prop_tools.validate_blueprint(bp, self.path, None)
        self.assertFalse(res["passed"])

    def test_begging_onscreen_fails(self):
        bp = copy.deepcopy(self.bp)
        bp["slides"][0]["render_text"]["key_points"].append("案例现场照片待提供")
        res = prop_tools.validate_blueprint(bp, self.path, None)
        self.assertFalse(res["passed"])
        self.assertTrue(any("索要" in e for e in res["errors"]), res["errors"])

    def test_blank_slot_prompt_seed_fails(self):
        bp = copy.deepcopy(self.bp)
        bp["slides"][3]["visual"]["prompt_seed"] = "证书网格版式，真实设备图位置留白，光大紫配色"
        res = prop_tools.validate_blueprint(bp, self.path, None)
        self.assertFalse(res["passed"])
        self.assertTrue(any("预留空位" in e for e in res["errors"]), res["errors"])

    def test_evidence_gap_without_standin_fails(self):
        bp = copy.deepcopy(self.bp)
        bp["slides"][3]["visual"]["asset_requests"] = [
            a for a in bp["slides"][3]["visual"]["asset_requests"] if a["asset_id"] == "a4"
        ]
        bp["slides"][3]["visual"]["prompt_seed"] = ""
        res = prop_tools.validate_blueprint(bp, self.path, None)
        self.assertFalse(res["passed"])
        self.assertTrue(any("顶位" in e for e in res["errors"]), res["errors"])

    def test_dangling_stand_in_for_fails(self):
        bp = copy.deepcopy(self.bp)
        for a in bp["slides"][3]["visual"]["asset_requests"]:
            if a["asset_id"] == "a4b":
                a["stand_in_for"] = "zzz"
        res = prop_tools.validate_blueprint(bp, self.path, None)
        self.assertFalse(res["passed"])

    def test_draft_state_onscreen_fails(self):
        bp = copy.deepcopy(self.bp)
        bp["slides"][0]["render_text"]["key_points"].append("执行价暂按单项限价88%")
        res = prop_tools.validate_blueprint(bp, self.path, None)
        self.assertFalse(res["passed"])
        self.assertTrue(any("草案状态/内部定价" in e for e in res["errors"]), res["errors"])

    def test_draft_state_in_takeaway_fails(self):
        bp = copy.deepcopy(self.bp)
        bp["slides"][1]["audience_takeaway"] = "所有单价须由真实底稿待授权后生效"
        res = prop_tools.validate_blueprint(bp, self.path, None)
        self.assertFalse(res["passed"])

    def test_draft_state_in_deck_fields_fails(self):
        bp = copy.deepcopy(self.bp)
        bp["deck"]["purpose"] = "技术标现场演示，并明确所有待实件边界"
        res = prop_tools.validate_blueprint(bp, self.path, None)
        self.assertFalse(res["passed"])
        self.assertTrue(any("deck 级字段" in e for e in res["errors"]), res["errors"])

    def test_missing_field_contract_warns(self):
        bp = copy.deepcopy(self.bp)
        bp["deck"].pop("field_contract", None)
        res = prop_tools.validate_blueprint(bp, self.path, None)
        self.assertTrue(res["passed"], res["errors"])
        self.assertTrue(any("field_contract" in w for w in res["warnings"]))

    def test_appendix_before_core_fails(self):
        bp = copy.deepcopy(self.bp)
        # 把 appendix 页排到中间：交换 n
        bp["slides"][3]["n"] = 2
        bp["slides"][1]["n"] = 4
        res = prop_tools.validate_blueprint(bp, self.path, None)
        self.assertFalse(res["passed"])


class IndexTests(unittest.TestCase):
    def setUp(self):
        self.index = _text("index-good.md")
        self.doc = _text("doc-good.md")
        self.score = _json("score-table-good.json")
        self.risk = _text("risk-good.md")

    def test_good_passes(self):
        res = prop_tools.validate_index(self.index, self.doc, self.score, self.risk)
        self.assertTrue(res["passed"], res["errors"])

    def test_missing_score_item_fails(self):
        score = copy.deepcopy(self.score)
        score["items"].append({"id": "S4", "text": "监播结案", "weight": 10, "kind": "floor"})
        res = prop_tools.validate_index(self.index, self.doc, score, self.risk)
        self.assertFalse(res["passed"])
        self.assertTrue(any("S4" in e for e in res["errors"]), res["errors"])

    def test_nonexistent_section_fails(self):
        bad = self.index.replace("三、执行与保障", "四、根本不存在的章节")
        res = prop_tools.validate_index(bad, self.doc, self.score, self.risk)
        self.assertFalse(res["passed"])
        self.assertTrue(any("不存在" in e for e in res["errors"]), res["errors"])

    def test_fabricated_without_risk_entry_fails(self):
        res = prop_tools.validate_index(self.index, self.doc, self.score, "# 风险\n- 无关条目\n")
        self.assertFalse(res["passed"])
        self.assertTrue(any("虚构补全" in e for e in res["errors"]), res["errors"])

    def test_claimed_section_mismatch_fails(self):
        score = copy.deepcopy(self.score)
        score["items"][0]["claimed_by_section"] = "第三章"  # 索引里 S1 在"二、传播策略与大概念"
        res = prop_tools.validate_index(self.index, self.doc, score, self.risk)
        self.assertFalse(res["passed"])
        self.assertTrue(any("认领章节" in e for e in res["errors"]), res["errors"])

    def test_bad_coverage_value_fails(self):
        bad = self.index.replace("虚构补全", "瞎写状态")
        res = prop_tools.validate_index(bad, self.doc, self.score, self.risk)
        self.assertFalse(res["passed"])

    def test_daishijian_coverage_status_passes(self):
        # "待实件"（文字完整·实件待补）是 v4.2 新增合法覆盖状态
        idx = self.index.replace("虚构补全", "待实件")
        res = prop_tools.validate_index(idx, self.doc, self.score, self.risk)
        self.assertTrue(res["passed"], res["errors"])

    def test_no_score_table_passes_trivially(self):
        res = prop_tools.validate_index("", self.doc, {"has_score_table": False}, None)
        self.assertTrue(res["passed"], res["errors"])


class LintDocTests(unittest.TestCase):
    CLEAN = (
        "## 一、总览\n\n我们围绕一条主线展开全部工作。**记忆句在此。**\n\n"
        "## 二、执行\n\n每项任务有责任人与时点，验收按贵行确认的标准执行。\n"
    )

    def test_clean_doc_passes(self):
        res = prop_tools.lint_doc(self.CLEAN, recall="记忆句在此。")
        self.assertTrue(res["passed"], res["errors"])
        self.assertEqual(res["counts"]["recall"], 1)

    def test_scaffold_leak_fails(self):
        for bad in (
            "表内数据均为本项目的拟议示例。",
            "专家名单须确认。",
            "全案唯一主亮点是驾驶舱。",
            "本示意不代表真实发布，图中无真实数据。",
            "这份方案围绕三条主线展开。",
        ):
            res = prop_tools.lint_doc(self.CLEAN + bad)
            self.assertFalse(res["passed"], bad)

    def test_voiceless_and_ai_caption_warn(self):
        doc = "## 一、总览\n\n项目按三阶段推进。\n\n> AI 示意·三波节奏。\n"
        res = prop_tools.lint_doc(doc)
        self.assertTrue(res["passed"], res["errors"])
        joined = "".join(res["warnings"])
        self.assertIn("我们", joined)
        self.assertIn("贵方", joined)
        self.assertIn("AI 示意", joined)

    def test_voiced_doc_no_voice_warnings(self):
        doc = "## 一、总览\n\n我们把审批提前一个月启动，贵方只需在两个节点确认。\n"
        res = prop_tools.lint_doc(doc)
        self.assertTrue(res["passed"], res["errors"])
        self.assertFalse(any("我们" in w or "贵方" in w for w in res["warnings"]), res["warnings"])

    def test_relay_marker_fails(self):
        res = prop_tools.lint_doc(self.CLEAN + "本章交出执行底稿；下一章将展开风险预案。\n")
        self.assertFalse(res["passed"])
        self.assertTrue(any("接力棒" in e for e in res["errors"]), res["errors"])

    def test_recall_over_limit_fails(self):
        doc = self.CLEAN + "记忆句在此。\n记忆句在此。\n"
        res = prop_tools.lint_doc(doc, recall="记忆句在此。")
        self.assertFalse(res["passed"])
        self.assertTrue(any("记忆句" in e for e in res["errors"]), res["errors"])

    def test_density_only_warns(self):
        doc = self.CLEAN + "详见第三章。\n" * 12 + "拟议方案A。\n" * 8
        res = prop_tools.lint_doc(doc)
        self.assertTrue(res["passed"], res["errors"])
        self.assertEqual(len(res["warnings"]), 2, res["warnings"])

    def test_bold_density_warns(self):
        doc = "## 一、总览\n\n" + "**重点** " * 8 + "\n"
        res = prop_tools.lint_doc(doc)
        self.assertTrue(res["passed"], res["errors"])
        self.assertTrue(any("加粗" in w for w in res["warnings"]), res["warnings"])

    def test_exemplar_overlap_fails(self):
        exemplar = "先让江州人坐成日常，再让全国游客坐成风景——这条船先是回家的路。"
        doc = self.CLEAN + "我们主张：先让江州人坐成日常，再让全国游客坐成风景。\n"
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "ex.md")
            with open(p, "w", encoding="utf-8") as f:
                f.write(exemplar)
            res = prop_tools.lint_doc(doc, exemplars=[p])
            self.assertFalse(res["passed"])
            self.assertTrue(any("范例" in e for e in res["errors"]), res["errors"])
            clean = prop_tools.lint_doc(self.CLEAN, exemplars=[p])
            self.assertTrue(clean["passed"], clean["errors"])

    def test_exemplar_overlap_ignores_whitespace(self):
        exemplar = "十二个字符的重合检测语句在此处。"
        doc = self.CLEAN + "十二个字符的重合\n检测语句在此处。\n"
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "ex.md")
            with open(p, "w", encoding="utf-8") as f:
                f.write(exemplar)
            res = prop_tools.lint_doc(doc, exemplars=[p])
            self.assertFalse(res["passed"], res["errors"])

    def test_image_links(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "配图"))
            with open(os.path.join(d, "配图", "01-实景.jpg"), "wb") as f:
                f.write(b"JPG")
            good = self.CLEAN + "![实景](配图/01-实景.jpg)\n"
            res = prop_tools.lint_doc(good, doc_dir=d)
            self.assertTrue(res["passed"], res["errors"])
            broken = self.CLEAN + "![缺图](配图/02-不存在.jpg)\n"
            res2 = prop_tools.lint_doc(broken, doc_dir=d)
            self.assertTrue(any("断链" in e for e in res2["errors"]), res2["errors"])
            hot = self.CLEAN + "![外链](https://example.com/a.jpg)\n"
            res3 = prop_tools.lint_doc(hot, doc_dir=d)
            self.assertTrue(any("外链" in e for e in res3["errors"]), res3["errors"])

    def test_cli_wiring(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "doc.md")
            with open(p, "w", encoding="utf-8") as f:
                f.write(self.CLEAN)
            self.assertEqual(prop_tools.main(["lint-doc", "--doc", p]), 0)


if __name__ == "__main__":
    unittest.main()
