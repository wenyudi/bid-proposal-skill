import json
import os
import sys
import tempfile
import unittest
from unittest import mock


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools import prop_tools  # noqa: E402


class QAGateCorpusTests(unittest.TestCase):
    def _qa(self, body, *, state_dir=None):
        report = (
            "# 测试方案\n\n"
            "项目名称：虚构测试项目\n\n"
            "## 目录\n\n"
            "## 应标响应与评分对照表\n\n"
            "## 一、项目理解\n\n"
            f"{body}\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            report_path = os.path.join(directory, "report.md")
            with open(report_path, "w", encoding="utf-8") as handle:
                handle.write(report)
            return prop_tools.qa_proposal(
                report_path,
                "standard",
                None,
                "zh",
                state_dir=state_dir,
            )

    def test_common_technical_terms_are_not_internal_ids(self):
        result = self._qa(
            "平台采用 role-based 权限模型与 need-driven 运营机制。\n\n"
            "系统兼容 AC-3 音频标准、对象存储 S3 与 M2 芯片。"
        )

        check = result["checks"]["no_id_leak"]
        self.assertTrue(check["passed"], check)
        self.assertEqual(check["found"], [])

    def test_canonical_and_legacy_ids_are_blocked(self):
        result = self._qa(
            "内部映射 REQ-M-QUALIFICATION、VP-CLOSED-LOOP 与 "
            "GATE-CAPABILITY-TEAM、OUT-RESPONSIBILITY-CARD 不得进入正文；"
            "评分编号 S1、S3 与 M2 也不得出现。"
        )

        check = result["checks"]["no_id_leak"]
        self.assertFalse(check["passed"])
        self.assertTrue({
            "REQ-M-QUALIFICATION",
            "VP-CLOSED-LOOP",
            "GATE-CAPABILITY-TEAM",
            "OUT-RESPONSIBILITY-CARD",
            "S1",
            "S3",
            "M2",
        }.issubset(set(check["found"])), check)

    def test_ambiguous_technical_token_is_blocked_when_state_names_it(self):
        documents = {
            "delivery-plan.json": {
                "acceptance_contracts": [{"id": "AC-3"}],
            },
            "strategy.json": {"open_questions": []},
        }
        with mock.patch.object(prop_tools, "_private_raw_leaks", return_value=[]), \
                mock.patch.object(
                    prop_tools.prop_v3,
                    "load_state",
                    return_value=(documents, {}),
                ):
            result = self._qa("正文意外带入 AC-3。", state_dir="/valid-state")

        check = result["checks"]["no_id_leak"]
        self.assertFalse(check["passed"])
        self.assertIn("AC-3", check["found"])

    def test_state_load_failure_degrades_id_check_fail_closed(self):
        with mock.patch.object(prop_tools, "_private_raw_leaks", return_value=[]), \
                mock.patch.object(
                    prop_tools.prop_v3,
                    "load_state",
                    side_effect=RuntimeError("broken state"),
                ):
            result = self._qa("正文没有任何内部编号。", state_dir="/broken-state")

        check = result["checks"]["no_id_leak"]
        self.assertFalse(check["passed"])
        self.assertTrue(check["degraded"])
        self.assertIn("state 加载失败", check["hint"])

    def test_chinese_words_are_not_mistaken_for_subsection_numbers(self):
        result = self._qa(
            "### 一体化传播平台\n\n统一承接内容生产。\n\n"
            "### 三维可视化大屏\n\n集中展示项目进度。"
        )

        check = result["checks"]["subsection_numbering"]
        self.assertTrue(check["passed"], check)
        self.assertEqual(check["issues"], [])

    def test_chinese_numbered_subsections_are_blocked(self):
        result = self._qa(
            "### 一、核心主张\n\n先形成统一判断。\n\n"
            "### 二. 执行路径\n\n再落实具体动作。"
        )

        check = result["checks"]["subsection_numbering"]
        self.assertFalse(check["passed"])
        self.assertEqual(len(check["issues"]), 2)

    def test_operational_time_and_canonical_format_are_not_internal_metadata(self):
        result = self._qa(
            "数据平台的日报生成时间：每日 9:00。\n\n"
            "交换接口支持 canonical 数据格式。"
        )

        check = result["checks"]["no_internal_leak"]
        self.assertTrue(check["passed"], check)
        self.assertEqual(check["leaked"], [])

    def test_internal_metadata_strategy_and_url_are_blocked_with_location(self):
        result = self._qa(
            "> **投标方案** · 生成时间：2026-07-01\n\n"
            "叙事：story\n\n"
            "详见 https://example.com/report"
        )

        check = result["checks"]["no_internal_leak"]
        self.assertFalse(check["passed"])
        self.assertIn("生成时间戳", check["leaked"])
        self.assertTrue(any("研报式元数据块" in item for item in check["leaked"]), check)
        self.assertTrue(any("叙事策略" in item for item in check["leaked"]), check)
        self.assertTrue(any("URL（第" in item for item in check["leaked"]), check)

    def test_risk_sentence_is_not_mistaken_for_excluded_scope(self):
        result = self._qa("已将风险排除项逐条封闭管理，并纳入复核台账。")

        check = result["checks"]["no_sales_cta"]
        self.assertTrue(check["passed"], check)
        self.assertEqual(check["found"], [])

    def test_excluded_scope_heading_and_list_item_are_flagged(self):
        result = self._qa(
            "## 排除项\n\n以下内容不在响应范围。\n\n"
            "- 不包含以下服务：现场驻场支持。"
        )

        check = result["checks"]["no_sales_cta"]
        self.assertFalse(check["passed"])
        self.assertIn("排除项", check["found"])
        self.assertIn("不包含以下服务", check["found"])

    def test_table_separator_does_not_inflate_word_count(self):
        markdown = "| 指标 | 口径 |\n|:---|:---|\n| A | B |\n"

        self.assertEqual(prop_tools.word_count_text(markdown), 6)

    def test_v3_chapter_gate_uses_exact_strategy_sections_not_profile_floor(self):
        report = (
            "# 测试方案\n\n项目名称：虚构测试项目\n\n"
            "## 目录\n\n## 应标响应与评分对照表\n\n"
            "## 一、项目理解\n\n### 1.1 核心判断\n\n正文。\n"
        )
        strategy = {
            "schema_version": "strategy/v4",
            "sections": [{"id": "CH-01", "n": 1, "title": "项目理解"}],
            "narrative": {"mode": "logic"},
            "decision_map": {"out_of_scope": []},
        }
        with tempfile.TemporaryDirectory() as directory:
            report_path = os.path.join(directory, "report.md")
            strategy_path = os.path.join(directory, "strategy.json")
            with open(report_path, "w", encoding="utf-8") as handle:
                handle.write(report)
            with open(strategy_path, "w", encoding="utf-8") as handle:
                json.dump(strategy, handle, ensure_ascii=False)
            result = prop_tools.qa_proposal(
                report_path, "standard", strategy_path, "zh")

        chapter = result["checks"]["chapter_count"]
        self.assertTrue(chapter["passed"], chapter)
        self.assertEqual(chapter["expected"], 1)
        self.assertEqual(chapter["rule"], "exact strategy.sections count")


if __name__ == "__main__":
    unittest.main()
