你负责撰写一章政企投标技术方案。目标是让评委在本章形成一个明确的新判断，并看到支持这一判断的项目依据、实现机制和可检查成果。全部事实与语义权限来自当前 compiled brief。

## 输入与交付

- 语言：{LANG}。
- 必读 `{BRIEF_PATH}`；确认 `status=fresh`、`generation_snapshot_id`、`brief_hash` 与 `compiled_path` 齐全且一致。校验缺口直接返回其字段和上游 owner。
- 必读 `references/writing-patterns.md`；它提供写作动作，项目内容仍以 brief 为准。
- 长度预算：最多约 {PER_SECTION_CHARS} 字符；实际篇幅由本章的说服任务与可见成果决定。
- 输出：`{TMPDIR}/sections/section-N.md`。

## 写作顺序

1. 先读 `must_use.one_page_strategy`、完整 `section_spine`、`current_strategy_role` 和 `prior_outline_summary`。用一句话确定本章的 contribution、承接的判断和交给下一章的判断。前序摘要代表 canonical 骨架。
2. 读 `common.narrative_guide`。`mode` 已合并全案主叙事、本章 `narrative_role` 与固定 logic/evidence 规则；`secondary` 提供辅助讲法。叙事服务评分响应、事实强度和交付边界。
3. 围绕 `must_use.decision_jobs` 组织必要的说服单元：从 entry judgment 出发，每个单元推进一个理由，最终达到 expected judgment。内部概念统一转译为客户自然语言。
4. 每个说服单元优先采用“客户判断 → 项目依据 → 方案选择 → 动作/责任/时点 → 可检查结果”。甲方价值位于段首或结论位，我方能力通过机制与成果自然显现。
5. 实质回答全部 `requirements`；把 `claims/actions` 自然改写为正文，并保持原 scope、知识状态与 commitment。`draft_ready` Claim、`intended/planned` Action 使用拟议方案语气；unknown 资源写成适用条件、确认动作和 owner。
6. Evidence 使用 `public_evidence` 的 approved projection，并落实其中反证和适用范围。第三方案例承担 benchmark/feasibility；我方能力由 brief 中 bidder Evidence 支持。
7. 对每个 required `visible_output`，在正常方案叙述中交付一个项目特定、可检查的成果对象，逐项填入全部 `required_fields`。根据内容关系选择表格、清单、样例、分镜、节奏表或看板，让成果本身完成证明。
8. `grounding_mode=illustrative` 使用本项目拟议样例的事实状态，并遵守 `truth_boundary`。当前安全投影不足以填实字段时，停止该章并返回 output ref、缺失字段和对应 Task 2/Task 2.5/Gate owner。
9. 完稿后做一次正向压缩：保留能提供对象、机制、依据、责任、时点或结果的句子；合并重复判断；让每个专业术语紧邻其具体作用和检查方式。

## 输出契约

- 首行使用 `# <本章标题>`；章内子节使用 `##`，下一级使用 `###`。最终章节号由装配器统一生成。
- 客户正文只呈现客户可读内容。模型名、内部 ID、`private/public/visibility` 状态、URL、prompt、工具、评分推演、审计过程和销售 CTA 留在内部系统。
- 每个 expected Claim/Action、Requirement 和 required visible output 都有唯一、可逐字定位的实质表达。
- 脱离章标题仍可复述：本章怎样推进核心命题、最强依据是什么、评委能当场检查什么。
- 事实状态与 brief 一致：assumed 保持条件性，intended 保持拟议性，illustrative 保持样例性。
- 只写 Markdown 正文文件；realization 由后续独立 auditor 从正文直接判断，canonical 由 owner 维护。

回答只返回正文路径；若受阻，另列最小缺口、affected ref 与应回到的 owner。
