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

    def test_bad_coverage_value_fails(self):
        bad = self.index.replace("虚构补全", "瞎写状态")
        res = prop_tools.validate_index(bad, self.doc, self.score, self.risk)
        self.assertFalse(res["passed"])

    def test_no_score_table_passes_trivially(self):
        res = prop_tools.validate_index("", self.doc, {"has_score_table": False}, None)
        self.assertTrue(res["passed"], res["errors"])


if __name__ == "__main__":
    unittest.main()
