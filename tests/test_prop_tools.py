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


class DetectEngineTests(unittest.TestCase):
    def test_unset_probe_url_does_not_access_network(self):
        with mock.patch.dict(os.environ, {}, clear=True), \
                mock.patch("urllib.request.urlopen") as urlopen:
            result = prop_tools.detect_engine()

        urlopen.assert_not_called()
        self.assertEqual(result, {
            "engine": "none",
            "available": False,
            "hint": "set PROPOSAL_SEARCH_PROBE_URL to enable probing",
        })

    def test_configured_probe_url_is_used_with_short_timeout(self):
        probe_url = "https://search.example.test/search?q=probe&format=json"
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = b'{"results": []}'

        with mock.patch.dict(
                os.environ,
                {"PROPOSAL_SEARCH_PROBE_URL": probe_url},
                clear=True,
        ), mock.patch("urllib.request.urlopen", return_value=response) as urlopen:
            result = prop_tools.detect_engine()

        urlopen.assert_called_once_with(mock.ANY, timeout=5)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, probe_url)
        self.assertEqual(result, {"engine": "searxng", "available": True})


class CheckStrategyTests(unittest.TestCase):
    def _write_json(self, directory, name, value):
        path = os.path.join(directory, name)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False)
        return path

    def _assembly_fixture(self, directory):
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
        strategy_path = self._write_json(directory, "strategy.json", strategy)
        requirements_path = self._write_json(
            directory, "requirements.json", requirements
        )
        intel_path = self._write_json(directory, "intel.json", [])
        sections_dir = os.path.join(directory, "sections")
        output_dir = os.path.join(directory, "reports")
        os.makedirs(sections_dir)
        with open(
            os.path.join(sections_dir, "section-1.md"), "w", encoding="utf-8"
        ) as handle:
            handle.write("### 1.1 关键问题\n\n采购人需要完整响应。\n")
        return {
            "strategy": strategy_path,
            "requirements": requirements_path,
            "intel": intel_path,
            "sections": sections_dir,
            "output": output_dir,
        }

    def _assemble_at(self, fixture, timestamp):
        with mock.patch.object(prop_tools.datetime, "datetime") as fake_datetime:
            fake_datetime.now.return_value = timestamp
            return prop_tools.assemble_proposal(
                fixture["strategy"],
                fixture["requirements"],
                fixture["intel"],
                fixture["sections"],
                "standard",
                fixture["output"],
                "zh",
            )

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

    def test_rejects_missing_and_duplicate_section_numbers(self):
        strategy = _strategy()
        strategy["sections"] = [
            {
                "title": "项目理解",
                "addresses": ["S1"],
                "narrative_role": "建立问题判断",
            },
            {
                "n": 2,
                "title": "实施路径",
                "addresses": ["S1"],
                "narrative_role": "说明执行路径",
            },
            {
                "n": 2,
                "title": "验收机制",
                "addresses": ["S1"],
                "narrative_role": "明确验收标准",
            },
        ]

        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "strategy.json", strategy)
            result = prop_tools.check_strategy(path, "standard")

        self.assertFalse(result["passed"])
        self.assertTrue(any(
            "sections[0] 缺 n 或 n 非正整数" in issue
            for issue in result["issues"]
        ), result["issues"])
        self.assertTrue(any(
            "sections[2].n 重复" in issue and "2" in issue
            for issue in result["issues"]
        ), result["issues"])

    def test_allows_unique_nonconsecutive_section_numbers(self):
        strategy = _strategy()
        strategy["sections"].append({
            "n": 3,
            "title": "验收机制",
            "addresses": ["S1"],
            "narrative_role": "明确验收标准",
        })

        with tempfile.TemporaryDirectory() as directory:
            path = self._write_json(directory, "strategy.json", strategy)
            result = prop_tools.check_strategy(path, "standard")

        self.assertTrue(result["passed"], result["issues"])

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

    def test_human_todo_blocks_front_matter_and_summary_placeholders(self):
        strategy = _strategy()
        strategy["decision_map"]["not_yet_specified"] = []
        strategy["open_questions"] = []
        requirements = {
            "budget_cap": {"value": 100, "unit": "万元"},
            "mandatory": [],
            "scoring": [
                {"id": "S1", "item": "项目理解", "weight": 20, "basis": "理解准确"}
            ],
        }
        report = (
            "# 测试投标方案\n\n"
            "投标人：【待填写：投标人全称并加盖公章】\n\n"
            "## 方案综述\n\n"
            "核心成果：【占位】\n\n"
            "## 一、项目理解\n\n"
            "本章完整响应采购需求。\n"
        )

        with tempfile.TemporaryDirectory() as directory:
            strategy_path = self._write_json(directory, "strategy.json", strategy)
            requirements_path = self._write_json(
                directory, "requirements.json", requirements
            )
            report_path = os.path.join(directory, "report.md")
            output_path = os.path.join(directory, "todo.md")
            with open(report_path, "w", encoding="utf-8") as handle:
                handle.write(report)

            result = prop_tools.human_todo(
                requirements_path,
                strategy_path,
                report_path,
                "standard",
                output_path,
                "zh",
            )
            with open(output_path, "r", encoding="utf-8") as handle:
                output = handle.read()

        self.assertEqual(result["blocking_count"], 2)
        self.assertEqual(result["scoring_count"], 0)
        blocking_section = output.split("## ⚠ 废标风险项（必须处理）", 1)[1]
        blocking_section = blocking_section.split("## AI 策略假设", 1)[0]
        self.assertIn("卷首/方案综述", blocking_section)
        self.assertIn("待填写：投标人全称并加盖公章", blocking_section)
        self.assertIn("占位", blocking_section)

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

    def test_assembly_normalizes_writer_local_heading_hierarchy(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = self._assembly_fixture(directory)
            section_path = os.path.join(fixture["sections"], "section-1.md")
            with open(section_path, "w", encoding="utf-8") as handle:
                handle.write(
                    "# 1. 项目理解\n\n"
                    "## 先看客户任务\n\n正文。\n\n"
                    "### 核心判断\n\n细化内容。\n\n"
                    "## 9.9 再看交付\n\n正文。\n\n"
                    "## 1.5倍响应不是编号\n\n正文。\n"
                )

            result = self._assemble_at(
                fixture, datetime.datetime(2026, 7, 15, 12, 0, 0)
            )
            with open(result["output_path"], "r", encoding="utf-8") as handle:
                report = handle.read()
            qa = prop_tools.qa_proposal(
                result["output_path"], "standard", fixture["strategy"], "zh"
            )

        self.assertTrue(result["passed"], result.get("issues"))
        self.assertIn("## 一、项目理解", report)
        self.assertIn("### 1.1 先看客户任务", report)
        self.assertIn("#### (1) 核心判断", report)
        self.assertIn("### 1.2 再看交付", report)
        self.assertIn("### 1.3 1.5倍响应不是编号", report)
        self.assertNotIn("## 先看客户任务", report)
        self.assertTrue(qa["checks"]["heading_hierarchy"]["passed"])

    def test_qa_blocks_chapter_local_heading_at_h2(self):
        strategy = _strategy()
        strategy["decision_map"]["not_yet_specified"] = []
        strategy["open_questions"] = []
        report = (
            "# 测试\n\n项目名称：测试\n\n## 目录\n\n"
            "## 应标响应与评分对照表\n\n## 一、项目理解\n\n"
            "## 错误子节\n\n正文。\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            strategy_path = self._write_json(directory, "strategy.json", strategy)
            report_path = os.path.join(directory, "report.md")
            with open(report_path, "w", encoding="utf-8") as handle:
                handle.write(report)
            result = prop_tools.qa_proposal(
                report_path, "standard", strategy_path, "zh"
            )

        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["heading_hierarchy"]["passed"])

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

    def test_assembly_promotion_failure_preserves_bundle_and_last_good(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = self._assembly_fixture(directory)
            first = self._assemble_at(
                fixture, datetime.datetime(2026, 7, 15, 12, 0, 0)
            )
            second = self._assemble_at(
                fixture, datetime.datetime(2026, 7, 15, 12, 1, 0)
            )
            self.assertTrue(first["passed"], first.get("issues"))
            self.assertTrue(second["passed"], second.get("issues"))

            current_bundle = second["bundle_dir"]
            last_good = second["last_good_bundle"]
            current_report = os.path.join(current_bundle, "技术方案-完整版.md")
            last_good_report = os.path.join(last_good, "技术方案-完整版.md")
            with open(current_report, "r", encoding="utf-8") as handle:
                current_before = handle.read()
            with open(last_good_report, "r", encoding="utf-8") as handle:
                last_good_before = handle.read()

            expected_target = os.path.join(
                fixture["output"], "测试投标方案-20260715-120200"
            )
            real_replace = os.replace
            promotion_calls = []

            def fail_staging_promotion(source, target):
                if (os.path.basename(os.fspath(source)).startswith(
                        ".proposal-bundle-staging-")
                        and os.fspath(target) == expected_target):
                    promotion_calls.append((os.fspath(source), os.fspath(target)))
                    raise OSError("injected bundle promotion failure")
                return real_replace(source, target)

            with mock.patch.object(
                    prop_tools.os, "replace", side_effect=fail_staging_promotion):
                with self.assertRaisesRegex(OSError, "injected bundle promotion failure"):
                    self._assemble_at(
                        fixture, datetime.datetime(2026, 7, 15, 12, 2, 0)
                    )

            self.assertEqual(promotion_calls[0][1], expected_target)
            self.assertTrue(os.path.isdir(current_bundle))
            with open(current_report, "r", encoding="utf-8") as handle:
                self.assertEqual(handle.read(), current_before)
            self.assertTrue(os.path.isdir(last_good))
            self.assertTrue(os.listdir(last_good))
            with open(last_good_report, "r", encoding="utf-8") as handle:
                self.assertEqual(handle.read(), last_good_before)
            self.assertFalse(any(
                name.startswith(".proposal-bundle-staging-")
                for name in os.listdir(fixture["output"])
            ))

    def test_assembly_build_failure_cleans_staging_and_preserves_recovery_points(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = self._assembly_fixture(directory)
            self._assemble_at(fixture, datetime.datetime(2026, 7, 15, 12, 0, 0))
            second = self._assemble_at(
                fixture, datetime.datetime(2026, 7, 15, 12, 1, 0)
            )
            current_report = second["output_path"]
            last_good_report = os.path.join(
                second["last_good_bundle"], "技术方案-完整版.md"
            )
            with open(current_report, "r", encoding="utf-8") as handle:
                current_before = handle.read()
            with open(last_good_report, "r", encoding="utf-8") as handle:
                last_good_before = handle.read()

            real_write = prop_tools.write_text_atomic
            failed_paths = []

            def fail_combined_write(path, content):
                parent = os.path.basename(os.path.dirname(os.fspath(path)))
                if (os.path.basename(os.fspath(path)) == "技术方案-完整版.md"
                        and parent.startswith(".proposal-bundle-staging-")):
                    failed_paths.append(os.fspath(path))
                    raise OSError("injected staging write failure")
                return real_write(path, content)

            with mock.patch.object(
                    prop_tools, "write_text_atomic", side_effect=fail_combined_write):
                with self.assertRaisesRegex(OSError, "injected staging write failure"):
                    self._assemble_at(
                        fixture, datetime.datetime(2026, 7, 15, 12, 2, 0)
                    )

            self.assertEqual(len(failed_paths), 1)
            with open(current_report, "r", encoding="utf-8") as handle:
                self.assertEqual(handle.read(), current_before)
            with open(last_good_report, "r", encoding="utf-8") as handle:
                self.assertEqual(handle.read(), last_good_before)
            self.assertFalse(any(
                name.startswith(".proposal-bundle-staging-")
                for name in os.listdir(fixture["output"])
            ))

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
