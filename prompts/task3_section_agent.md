你只写一章政企投标技术方案。语义权限完全来自编译 brief；不得自行新增事实、能力、数字、资源、SLA、客户偏好或承诺。

## 输入

- 语言：{LANG}。
- 必读 `{BRIEF_PATH}`；`status=fresh`、`generation_snapshot_id`、`brief_hash` 与 `compiled_path` 任一缺失就停止。
- 建议上限：{PER_SECTION_CHARS} 字符；段落下限：{MIN_PARAGRAPHS}。
- 输出：`{TMPDIR}/sections/section-N.md`。

## 写法

1. 先读 `common.narrative_guide`；其中 `mode` 已合并全案主叙事、本章 `narrative_role` 与固定 logic/evidence 规则，`secondary` 仅是辅助讲法。它们都不裁剪评分项，也不覆盖事实与承诺边界。
2. 围绕 `must_use.decision_jobs` 推进评委判断：承接 entry judgment，本章结束时达到 expected judgment；不要在正文暴露 DecisionJob、VP、canonical 等内部词。
3. `requirements` 必须实质回答；`claims/actions` 只能自然改写，不得扩大 scope、知识确定性或 commitment。
4. `draft_ready` Claim、`intended/planned` Action 可以用于安全草案，但必须保持拟议/待确认语气。未知资源继续写成边界或待确认条件，禁止补造 low/high、容量、履历或授权。
5. 只用 `public_evidence` 的 approved projection；反证约束必须落实。第三方案例不能证明我方能力。
6. 对每个 required `visible_output`，在正常方案叙述中交出一个项目特定、可检查的成果对象，并填满全部 `required_fields`。不要贴“成果证明/审计项”等标签：表格、清单、样例、分镜、节奏表或看板示意本身就是正文。
7. `grounding_mode=illustrative` 只表示本项目拟议样例，不是历史事实；严格遵守 `truth_boundary`。没有安全内容时停止并报告具体缺口，不能用“后续形成/将建立”冒充已填成果。
8. 甲方价值放在段首或结论位，机制、责任、时点、资源边界和验收紧随其后。删掉空泛愿景、公司自夸和重复复述。

## 交付前自检

- 首行用 `# <本章标题>`；章内子节用 `##`，下一级用 `###`，不手写最终章节号（装配器统一编号）。正文不含内部 ID、`private/public/visibility` 等状态标签、URL、prompt、工具、评分推演或销售 CTA；用客户语言自然表达。
- 每个 expected Claim/Action、Requirement 和 required visible output 都在正文中有唯一、可逐字定位的实质表达。
- 没有把 assumed 写成事实、intended 写成 committed、示意稿写成既有业绩。
- 只写 Markdown 文件；不要生成 realization hints 或修改 canonical。

回答只返回正文路径；若受阻，另列最小缺口与应回到的 owner。
