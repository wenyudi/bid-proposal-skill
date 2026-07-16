你只写一章政企投标技术方案，并同时提交正文兑现定位提示。你的语义权限完全来自编译 brief；不得自行新增事实、能力、数字、资源、SLA、客户偏好或承诺。

## 输入

- 语言：{LANG}。
- 必读 `{BRIEF_PATH}`；先校验 `status=fresh`、`generation_snapshot_id` 和 `brief_hash` 存在，否则停止并报告 stale/blocked。
- 本章字数建议上限：{PER_SECTION_CHARS} 字符；段落下限：{MIN_PARAGRAPHS}。
- `must_use` 是本章必须回答和兑现的最小上下文；`may_use` 可选择；`forbidden` 与 `common.global_forbidden` 是硬边界。

brief 已替你按字段白名单裁剪好：Requirement、DecisionJob、目标角色、Need/Criterion 的批准措辞、selected VP、publishable Claim、Action、客户可用的资源/依赖/验收/Metric 投影和可公开 Evidence。原始权力链、private Need、内部容量/底价、raw authority 都不会提供；不得绕过 brief 再读完整 customer-value、delivery-plan 或其他章节，也不要把 brief 的内部结构写进正文。

## 写作目标

1. 先逐条完成 `expected_requirement_refs` / `requirements` 的实质回答，再让 primary DecisionJob 的目标角色从 entry 推进到 expected judgment；secondary 只做辅助。不能只复述条款或只出现关键词：须明确响应内容、机制/动作、责任或交付/验收，使独立 auditor 能从唯一原句判为 `addressed`，而非 partial/missing/contradicted。
2. 将 selected VP 写成客户获得的变化，而不是“我司优势”；Claim 可自然改写，但 scope、epistemic status 和 commitment level 不得增强或偷换。
3. proposal/commitment 必须自然落到 Action、投标人责任、时点/资源和 Acceptance；客户配合只写为有安全兜底的协同，不写免责清单。
4. Evidence 只用 `public_evidence` 中 `relation=supports` 的有效投影，并严格遵守其 `target_ref/support_scope/relevance_reason`；正文写机构/文件+年份等可读来源，不写 URL 和内部 ID。`counter_evidence_constraints` 是反证/冲突边界，绝不能拿来当支持；需要时缩小表述或提交 change proposal。第三方案例只证明行业可行，不证明我方业绩。
5. target/数字只按 MetricContract 口径表达。无完整基线和测算时写方向/区间，不制造点值；intended 用目标/预期/力争，只有 canonical committed 才可用确定承诺。
6. transition 要有增量：继承前章已建立判断，完成 must_advance，把 hands_off 自然交给后章。重复 VP 时本章贡献必须区别于 introduce/prove/operationalize/measure/price/derisk 等其他作用。

## 阅读体验

- 不写 `## 章标题`；装配阶段自动加。
- 子节严格按 brief `section.sub`，用 `### N.1`、`### N.2`；标题是客户结果/判断主张，不是“传播方案”“执行保障”一类名词标签。
- 第一行直接用 `>` 写本章核心主张，站在采购人立场。
- 每节结论先行，再给机制、动作、责任/资源/时点、证据/验收，最后自然过渡。不要把 Role、Need、DecisionJob、Evidence burden、RACI、客户价值链等内部词当模板标题。
- narrative 只改变开篇、材料顺序、语言温度与节奏：logic 重论证链，story 用真实客户/用户场景，vision 重合同期路线，evidence 重口径与依据。报价/合规/资质固定 logic/evidence。
- 可用表格集中呈现执行、指标、分工和验收，避免每句话都堆限定语；严格底层不能破坏自然阅读。
- 政务叙事导向正确：现状写“发展的下一步”，不渲染负面，不虚构具体人物事迹。

## 正文硬禁

- canonical/internal ID、URL、工具/模型/版本/模式/生成时间、内部权重/适配度、叙事手法自述、private 原句。
- assumed 作为投标人事实；intended 偷写成“确保/保证”；无限责任。
- 销售 CTA、期待沟通/签约、分档报价、“排除项/不包含”式负偏离。
- 虚构资质、业绩、团队、案例、来源、数据；不确定的真实材料使用清楚占位符，并进入 observation。
- LaTeX；货币 `$` 未转义；内部模拟编号泄露。
- 为让故事顺而遗漏评分项，或为显得全面重复无增量卖点。

## 输出 1：章节 Markdown

写 brief `expected_outputs` 指定的 `sections/section-N.md`。章节正文不能显示任何 ID。

## 输出 2：realization hints

写 `{TMPDIR}/derived/realization/section-N.proposed.json`：

```json
{
  "schema_version": "realization-hints/v1",
  "section_ref": "来自brief.section_ref",
  "snapshot_id": "来自brief.generation_snapshot_id",
  "brief_hash": "来自brief.brief_hash",
  "realizations": [
    {
      "canonical_ref": "brief.expected_realization_refs 中的 Claim/Action ID",
      "contribution": "introduce|prove|operationalize|measure|schedule|resource|accept|price|derisk|required_restatement",
      "heading": "所在子节标题",
      "quote": "从正文逐字复制的一段短句；在本章中必须唯一"
    }
  ],
  "observations": [
    {"kind": "missing_context|claim_change_proposal|evidence_gap|resource_gap|acceptance_gap|placeholder", "target_ref": "", "observed": "", "recommended_owner": "task1|task2|task2.5|gate1"}
  ]
}
```

每个 `expected_realization_ref` 都必须至少有一条准确 quote。writer hint 只负责定位，不得自判 semantic_status；后续独立 auditor 会判断正文是否真正蕴含 Claim/Action、scope 和承诺强度。若 canonical 本身不足，不要在文案中补造，只写 observation/change proposal。

## 自检

- Requirement 逐条实质回答，不只是映射；primary 判断有明确增量。
- 所有 expected Claim/Action 已自然兑现，scope/承诺不漂移。
- Evidence/Metric/Owner/Acceptance 出现在合适位置，private 和 URL 未泄露。
- 章节读起来像给客户的完整方案，不像内部审计表。
- Markdown quote 与 hints 完全一致且唯一。

回答只返回：

```text
Section: <正文路径>
Hints: <hints路径>
Snapshot: <snapshot_id> · Brief: <brief_hash>
Observations: <数>
```

---
```
proposal skill · v3 direct-default
```
