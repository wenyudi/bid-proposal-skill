import datetime
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


def _strategy():
    return {
        "title": "测试投标方案",
        "depth_mode": "standard",
        "narrative": {
            "mode": "logic",
            "rationale": "技术评分强调论证完整性",
            "through_line": "从问题到结果",
        },
        "decision_map": {
            "destination": "形成一份评分项全覆盖且能力边界经确认的技术标。",
            "not_yet_specified": [
                {
                    "name": "增值服务承诺幅度",
                    "blocked_by": ["交付能力边界"],
                    "promotion_signal": "确认可投入团队与资源后",
                }
            ],
            "out_of_scope": [
                {
                    "item": "投标函",
                    "reason": "按招标模板另行套用",
                    "forbidden_terms": ["法定代表人授权书"],
                }
            ],
        },
        "open_questions": [
            {
                "title": "交付能力边界",
                "q": "哪些增值服务可真实承诺？",
                "why_matters": "承诺过度会造成履约风险",
                "ai_assumption": "只承诺已有团队可覆盖的服务",
                "depends_on": [],
                "status": "open",
                "resolved": None,
                "assumption_risk": False,
            },
            {
                "title": "未公开履约历史",
                "q": "是否存在公开资料查不到、但会影响本次承诺的既往履约情况？",
                "why_matters": "影响能力边界与风险承诺",
                "ai_assumption": "按无未公开履约事项处理",
                "depends_on": [],
                "status": "resolved",
                "resolved": "没有需要额外披露的未公开履约事项",
                "assumption_risk": False,
            },
            {
                "title": "报价边界",
                "q": "最低可接受报价是多少？",
                "why_matters": "影响资源配置和利润",
                "ai_assumption": "按预算上限九成测算",
                "depends_on": ["交付能力边界"],
                "status": "open",
                "resolved": None,
                "assumption_risk": False,
            },
        ],
        "sections": [
            {
                "n": 1,
                "title": "项目理解",
                "addresses": ["S1"],
                "narrative_role": "建立问题判断",
            }
        ],
        "differentiators": [],
    }


class CheckStrategyTests(unittest.TestCase):
    def _write_json(self, directory, name, value):
        path = os.path.join(directory, name)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False)
        return path

    def test_calculates_frontier_and_blocked_decisions(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "strategy.json", _strategy())
            result = prop_tools.check_strategy(path, "standard")

        self.assertTrue(result["passed"], result["issues"])
        self.assertEqual(result["frontier"], ["交付能力边界"])
        self.assertEqual(result["blocked"], ["报价边界"])
        self.assertEqual(result["fog_count"], 1)

    def test_require_settled_rejects_open_decisions_and_fog(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "strategy.json", _strategy())
            result = prop_tools.check_strategy(path, "standard", require_settled=True)

        self.assertFalse(result["passed"])
        self.assertTrue(any("open 决策" in issue for issue in result["issues"]))
        self.assertTrue(any("not_yet_specified" in issue for issue in result["issues"]))

    def test_resolved_and_assumed_decisions_can_settle_map(self):
        strategy = _strategy()
        strategy["decision_map"]["not_yet_specified"] = []
        strategy["open_questions"][0].update(
            status="resolved", resolved="仅承诺现有团队能稳定交付的服务"
        )
        strategy["open_questions"][2].update(
            status="assumed",
            resolved=strategy["open_questions"][2]["ai_assumption"],
            assumption_risk=True,
        )

        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "strategy.json", strategy)
            result = prop_tools.check_strategy(
                path, "standard", require_settled=True, allow_assumed=True
            )

        self.assertTrue(result["passed"], result["issues"])
        self.assertTrue(result["settled"])
        self.assertEqual(result["assumed_count"], 1)

    def test_zero_decisions_are_valid_when_route_is_clear(self):
        strategy = _strategy()
        strategy["decision_map"]["not_yet_specified"] = []
        strategy["open_questions"] = []

        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "strategy.json", strategy)
            result = prop_tools.check_strategy(path, "standard", require_settled=True)

        self.assertTrue(result["passed"], result["issues"])
        self.assertEqual(result["decision_count"], 0)

    def test_assumed_requires_auto_and_exact_assumption(self):
        strategy = _strategy()
        strategy["decision_map"]["not_yet_specified"] = []
        strategy["open_questions"][0].update(
            status="resolved", resolved="仅承诺稳定可交付的服务"
        )
        strategy["open_questions"][2].update(
            status="assumed", resolved="不是预设答案", assumption_risk=True
        )

        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "strategy.json", strategy)
            normal = prop_tools.check_strategy(path, "standard", require_settled=True)
            auto = prop_tools.check_strategy(
                path, "standard", require_settled=True, allow_assumed=True
            )

        self.assertFalse(normal["passed"])
        self.assertTrue(any("不是 -auto" in issue for issue in normal["issues"]))
        self.assertFalse(auto["passed"])
        self.assertTrue(any("必须等于 ai_assumption" in issue for issue in auto["issues"]))

    def test_apply_auto_decisions_is_atomic_and_idempotent(self):
        strategy = _strategy()
        strategy["decision_map"]["not_yet_specified"] = []

        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "strategy.json", strategy)
            first = prop_tools.apply_auto_decisions(path)
            second = prop_tools.apply_auto_decisions(path)
            checked = prop_tools.check_strategy(
                path, "standard", require_settled=True, allow_assumed=True
            )

        self.assertTrue(first["passed"], first["issues"])
        self.assertEqual(first["converted"], 2)
        self.assertTrue(second["passed"], second["issues"])
        self.assertEqual(second["converted"], 0)
        self.assertTrue(checked["passed"], checked["issues"])

    def test_rejects_cycles(self):
        strategy = _strategy()
        strategy["decision_map"]["not_yet_specified"] = []
        strategy["open_questions"][0]["depends_on"] = ["报价边界"]

        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "strategy.json", strategy)
            result = prop_tools.check_strategy(path, "standard")

        self.assertFalse(result["passed"])
        self.assertTrue(any("循环依赖" in issue for issue in result["issues"]))

    def test_reports_malformed_dependency_without_crashing(self):
        strategy = _strategy()
        strategy["open_questions"][0]["depends_on"] = [{"bad": "shape"}]

        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "strategy.json", strategy)
            result = prop_tools.check_strategy(path, "standard")

        self.assertFalse(result["passed"])
        self.assertTrue(any("必须是非空文本" in issue for issue in result["issues"]))

    def test_rejects_invalid_narrative_and_unmapped_section(self):
        strategy = _strategy()
        strategy["narrative"] = {"mode": "sales", "through_line": "错误模式"}
        strategy["sections"][0]["addresses"] = []

        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "strategy.json", strategy)
            result = prop_tools.check_strategy(path, "standard")

        self.assertFalse(result["passed"])
        self.assertTrue(any("narrative.mode 非法" in issue for issue in result["issues"]))
        self.assertTrue(any("缺 rationale" in issue for issue in result["issues"]))
        self.assertTrue(any("addresses 必须是非空数组" in issue for issue in result["issues"]))

    def test_human_todo_includes_auto_assumptions(self):
        strategy = _strategy()
        strategy["decision_map"]["not_yet_specified"] = []
        for decision in strategy["open_questions"]:
            if decision["status"] == "open":
                decision.update(
                    status="assumed",
                    resolved=decision["ai_assumption"],
                    assumption_risk=True,
                )
        requirements = {
            "budget_cap": {"value": 100, "unit": "万元"},
            "mandatory": [],
            "scoring": [
                {"id": "S1", "item": "项目理解", "weight": 20, "basis": "理解准确"}
            ],
        }

        with tempfile.TemporaryDirectory() as directory:
            strategy_path = self._write_json(directory, "strategy.json", strategy)
            requirements_path = self._write_json(directory, "requirements.json", requirements)
            intel_path = self._write_json(directory, "intel.json", [
                {
                    "topic": "竞品",
                    "gaps": [
                        {
                            "kind": "assumption_conflict",
                            "item": "公开资料显示可能存在更低报价对手",
                            "decision": "报价边界",
                            "impact": "需人工复核报价假设",
                        }
                    ],
                }
            ])
            report_path = os.path.join(directory, "report.md")
            output_path = os.path.join(directory, "todo.md")
            with open(report_path, "w", encoding="utf-8") as handle:
                handle.write("## 一、项目理解\n\n采购人需要一份完整响应。\n")

            result = prop_tools.human_todo(
                requirements_path,
                strategy_path,
                report_path,
                "standard",
                output_path,
                "zh",
                intel_path,
            )
            with open(output_path, "r", encoding="utf-8") as handle:
                output = handle.read()

        self.assertEqual(result["assumption_count"], 2)
        self.assertEqual(result["intel_gap_count"], 1)
        self.assertIn("AI 策略假设", output)
        self.assertIn("公开资料显示可能存在更低报价对手", output)
        self.assertIn("交付能力边界", output)
        self.assertIn("报价边界", output)

    def test_assembly_archives_decision_map_only_in_internal_brief(self):
        strategy = _strategy()
        strategy["decision_map"]["not_yet_specified"] = []
        for decision in strategy["open_questions"]:
            if decision["status"] == "open":
                decision.update(
                    status="assumed",
                    resolved=decision["ai_assumption"],
                    assumption_risk=True,
                )
        requirements = {
            "project_name": "测试项目",
            "project_no": "TEST-1",
            "buyer": "测试采购人",
            "budget_cap": {"value": 100, "unit": "万元"},
            "mandatory": [],
            "scoring": [
                {"id": "S1", "item": "项目理解", "weight": 20, "basis": "理解准确"}
            ],
        }

        with tempfile.TemporaryDirectory() as directory:
            strategy_path = self._write_json(directory, "strategy.json", strategy)
            requirements_path = self._write_json(directory, "requirements.json", requirements)
            intel_path = self._write_json(directory, "intel.json", [])
            sections_dir = os.path.join(directory, "sections")
            output_dir = os.path.join(directory, "reports")
            os.makedirs(sections_dir)
            with open(os.path.join(sections_dir, "section-1.md"), "w", encoding="utf-8") as handle:
                handle.write("> 帮助采购人形成清晰判断。\n\n### 1.1 先识别关键问题\n\n正文。\n")

            result = prop_tools.assemble_proposal(
                strategy_path,
                requirements_path,
                intel_path,
                sections_dir,
                "standard",
                output_dir,
                "zh",
                True,
            )
            with open(result["internal_brief"], "r", encoding="utf-8") as handle:
                brief = handle.read()
            with open(result["output_path"], "r", encoding="utf-8") as handle:
                report = handle.read()

        self.assertTrue(result["passed"], result["issues"])
        self.assertIn("投标决策地图", brief)
        self.assertIn("AI 假设（待人工复核）", brief)
        self.assertIn("形成一份评分项全覆盖", brief)
        self.assertNotIn("投标决策地图", report)
        self.assertNotIn("AI 假设", report)

    def test_assembly_rejects_unsettled_strategy_before_writing(self):
        strategy = _strategy()
        requirements = {
            "project_name": "测试项目",
            "buyer": "测试采购人",
            "budget_cap": {"value": 100, "unit": "万元"},
            "mandatory": [],
            "scoring": [{"id": "S1", "item": "项目理解", "weight": 20}],
        }

        with tempfile.TemporaryDirectory() as directory:
            strategy_path = self._write_json(directory, "strategy.json", strategy)
            requirements_path = self._write_json(directory, "requirements.json", requirements)
            intel_path = self._write_json(directory, "intel.json", [])
            sections_dir = os.path.join(directory, "sections")
            output_dir = os.path.join(directory, "reports")
            os.makedirs(sections_dir)
            result = prop_tools.assemble_proposal(
                strategy_path,
                requirements_path,
                intel_path,
                sections_dir,
                "standard",
                output_dir,
                "zh",
            )

        self.assertFalse(result["passed"])
        self.assertTrue(any("Strategy not settled" in issue for issue in result["issues"]))

    def test_reassembly_replaces_old_bundle_and_finalizes_latest(self):
        strategy = _strategy()
        strategy["decision_map"]["not_yet_specified"] = []
        strategy["open_questions"] = []
        requirements = {
            "project_name": "测试项目",
            "project_no": "TEST-1",
            "buyer": "测试采购人",
            "budget_cap": {"value": 100, "unit": "万元"},
            "mandatory": [],
            "scoring": [
                {"id": "S1", "item": "项目理解", "weight": 20, "basis": "理解准确"}
            ],
        }

        with tempfile.TemporaryDirectory() as directory:
            first_time = datetime.datetime(2026, 7, 15, 12, 0, 0)
            second_time = datetime.datetime(2026, 7, 15, 12, 1, 0)
            strategy_path = self._write_json(directory, "strategy.json", strategy)
            requirements_path = self._write_json(directory, "requirements.json", requirements)
            intel_path = self._write_json(directory, "intel.json", [])
            sections_dir = os.path.join(directory, "sections")
            output_dir = os.path.join(directory, "reports")
            os.makedirs(sections_dir)
            with open(os.path.join(sections_dir, "section-1.md"), "w", encoding="utf-8") as handle:
                handle.write("### 1.1 关键问题\n\n采购人需要完整响应。\n")

            with mock.patch.object(prop_tools.datetime, "datetime") as fake_datetime:
                fake_datetime.now.return_value = first_time
                first = prop_tools.assemble_proposal(
                    strategy_path, requirements_path, intel_path, sections_dir,
                    "standard", output_dir, "zh",
                )
            old_todo = os.path.join(first["bundle_dir"], "_人工待办.md")
            prop_tools.human_todo(
                requirements_path, strategy_path, first["output_path"], "standard",
                old_todo, "zh", intel_path,
            )
            self.assertTrue(os.path.exists(old_todo))

            with mock.patch.object(prop_tools.datetime, "datetime") as fake_datetime:
                fake_datetime.now.return_value = second_time
                second = prop_tools.assemble_proposal(
                    strategy_path, requirements_path, intel_path, sections_dir,
                    "standard", output_dir, "zh",
                )

            self.assertNotEqual(first["bundle_dir"], second["bundle_dir"])
            self.assertFalse(os.path.exists(first["bundle_dir"]))
            self.assertTrue(os.path.isdir(second["last_good_bundle"]))
            self.assertTrue(os.path.isfile(os.path.join(
                second["last_good_bundle"], "技术方案-完整版.md"
            )))

            # 同一秒内再次装配也必须清空目标目录，不能遗留预先生成的待办。
            stale_todo = os.path.join(second["bundle_dir"], "_人工待办.md")
            prop_tools.write_text_atomic(stale_todo, "旧待办\n")
            with mock.patch.object(prop_tools.datetime, "datetime") as fake_datetime:
                fake_datetime.now.return_value = second_time
                final = prop_tools.assemble_proposal(
                    strategy_path, requirements_path, intel_path, sections_dir,
                    "standard", output_dir, "zh",
                )
            self.assertEqual(second["bundle_dir"], final["bundle_dir"])
            self.assertFalse(os.path.exists(stale_todo))

            final_todo = os.path.join(final["bundle_dir"], "_人工待办.md")
            prop_tools.human_todo(
                requirements_path, strategy_path, final["output_path"], "standard",
                final_todo, "zh", intel_path,
            )
            self.assertTrue(os.path.exists(final["output_path"]))
            self.assertTrue(os.path.exists(final["internal_brief"]))
            self.assertTrue(os.path.exists(final_todo))

    def test_qa_warns_when_report_hits_out_of_scope_term(self):
        strategy = _strategy()
        strategy["decision_map"]["not_yet_specified"] = []
        strategy["open_questions"] = []

        with tempfile.TemporaryDirectory() as directory:
            strategy_path = self._write_json(directory, "strategy.json", strategy)
            report_path = os.path.join(directory, "report.md")
            with open(report_path, "w", encoding="utf-8") as handle:
                handle.write("# 测试\n\n法定代表人授权书由本方案生成。\n")
            result = prop_tools.qa_proposal(
                report_path, "standard", strategy_path, "zh"
            )

        scope = result["checks"]["scope_guard"]
        self.assertFalse(scope["passed"])
        self.assertTrue(scope["warning"])
        self.assertEqual(scope["hits"][0]["term"], "法定代表人授权书")

    def test_qa_hard_blocks_v3_internal_id_leak(self):
        strategy = _strategy()
        strategy["schema_version"] = "strategy/v3"
        strategy["decision_map"]["not_yet_specified"] = []
        strategy["open_questions"] = []

        with tempfile.TemporaryDirectory() as directory:
            strategy_path = self._write_json(directory, "strategy.json", strategy)
            report_path = os.path.join(directory, "report.md")
            with open(report_path, "w", encoding="utf-8") as handle:
                handle.write("# 测试\n\n项目名称：测试\n\n## 目录\n\n## 应标响应与评分对照表\n\n正文引用 VP-CLOSED-LOOP。\n")
            result = prop_tools.qa_proposal(
                report_path, "standard", strategy_path, "zh"
            )

        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["no_id_leak"]["passed"])
        self.assertFalse(result["checks"]["no_id_leak"]["warning"])

    def test_v3_compliance_includes_deliverable_requirements(self):
        strategy = _strategy()
        strategy["schema_version"] = "strategy/v3"
        strategy["decision_map"]["not_yet_specified"] = []
        strategy["open_questions"] = []
        requirements = {
            "schema_version": "requirements/v3",
            "budget_cap": {"value": 100, "unit": "万元"},
            "mandatory": [],
            "scoring": [{"id": "S1", "item": "项目理解", "weight": 20}],
            "deliverables": [{"id": "REQ-D-REPORT", "item": "结案报告"}],
        }
        report = "# 测试\n\n项目名称：测试\n\n## 目录\n\n## 应标响应与评分对照表\n\n## 一、项目理解\n\n正文\n"

        with tempfile.TemporaryDirectory() as directory:
            strategy_path = self._write_json(directory, "strategy.json", strategy)
            requirements_path = self._write_json(directory, "requirements.json", requirements)
            report_path = os.path.join(directory, "report.md")
            with open(report_path, "w", encoding="utf-8") as handle:
                handle.write(report)
            missing = prop_tools.check_compliance(
                requirements_path, strategy_path, report_path
            )
            strategy["sections"][0]["addresses"].append("REQ-D-REPORT")
            strategy_path = self._write_json(directory, "strategy.json", strategy)
            covered = prop_tools.check_compliance(
                requirements_path, strategy_path, report_path
            )

        self.assertFalse(missing["passed"])
        self.assertEqual(missing["missing_deliverables"][0]["id"], "REQ-D-REPORT")
        self.assertTrue(covered["passed"])
        self.assertEqual(covered["addressed_deliverables"], 1)


if __name__ == "__main__":
    unittest.main()
