# 案例库（casebase）

这里保存公司真实案例的**人工事实源**。v3 不再把整篇案例当万能证明，而是：

```text
CaseRecord（身份/范围/权限）
  → CaseEvidenceItem（原子业绩/交付/能力/结果证据）
  → 本标 EvidenceLink（它能证明哪个 Need/VP/Claim）
```

- 每个案例一个 `.md`，可分子目录；`_` 开头与 README 不作为案例。
- 案例必须真实可核验。虚构客户、合同、结果、奖项、团队或我方角色可能构成骗标风险。
- 旧无 schema 案例继续可检索，不要求批量重写：`results` 只按 `asserted_from_text`，`verifiable` 只按 `material_listed`，都不自动等于 verified。
- 只有案例被当前标选中且承担资格、高风险业绩、数字或公开署名证明时，才渐进补齐 v2 人工字段。

## CaseRecord v2

复制 `_template.md`。frontmatter 由人确认以下事实：

- `case_id`、项目/客户、日期、行业、服务范围和预算。
- 我方真实角色：`prime / consortium / subcontract / unknown`；不清楚时正文禁用“主导/全案负责”。
- 案例生命周期：`draft / active / contested / retired`。
- 可见性与用途分开：案例即使可匿名，也不代表客户名、Logo、评价、金额和数字结果都获授权。
- 核验材料“列出”不等于“已核验”；只有人实际检查后才能把 EvidenceItem 标 verified。

frontmatter 示例：

```yaml
---
schema_version: case-record/v2
case_id: CASE-CITY-2024
status: active
name: XX市城市形象整合传播
client: XX市文化广电旅游局
client_type: 政府
industry: 文旅, 城市品牌
services: 整合营销, 短视频, 活动执行
start_date: 2024-03
end_date: 2024-12
budget: 80万元
bidder_role: prime
engagement_scope: 品牌策略、内容制作与活动执行
visibility: anonymized
allowed_uses: matching, capability_reasoning, proposal_narrative
client_name_permission: false
logo_permission: false
testimonial_permission: false
numeric_result_permission: false
qualification_material_available: true
sensitive_or_disputed: false
---
```

## CaseEvidenceItem

正文的 `case-evidence/v1` JSON 是可被按标引用的原子事实。每项只证明自己的范围：合同证明参与与合同范围，验收证明被验收部分，截图证明特定时点数据，历史结果不自动证明归因或本项目目标。

```json
{
  "schema_version": "case-evidence/v1",
  "items": [
    {
      "id": "CE-CITY-SCOPE-01",
      "kind": "engagement_fact|deliverable_fact|capability_observation|outcome_observation|testimonial|award|qualification",
      "statement": "我方在合同范围内完成品牌策略与系列短视频制作",
      "scope": "合同约定服务范围",
      "period": "2024-03 至 2024-12",
      "source_material": "合同第X条、验收报告第X页",
      "verification_status": "asserted|material_listed|verified|expired|contested|rejected",
      "visibility": "internal_only|anonymized|named|public",
      "allowed_uses": ["matching", "qualification_attachment", "capability_reasoning", "proposal_narrative", "bidder_capability", "numeric_result", "client_name", "logo", "testimonial"],
      "safe_title": "经授权的匿名/署名标题；没有则留空",
      "approved_wording": "经授权可在方案中使用的表述；没有则留空",
      "publication_authority": "人工核验的授权材料/Gate；没有则留空",
      "limitations": "不能证明的内容或归因边界"
    }
  ]
}
```

量化结果另补：指标定义、统计对象/公式、单位、基线、目标/结果、时间窗、数据源、归因与允许误差。缺任一关键口径时可参与匹配，但不能支持 publishable 数字 Claim。

`capability_reasoning` 只表示内部匹配，不自动获得 v3 Evidence 的 `bidder_capability`。只有 EvidenceItem verified、bidder_role/scope 相符，且授权允许用于本标证明我方能力时，按标迁移才可显式增加 `bidder_capability`。匿名正文还必须有 safe_title + approved_wording + publication_authority；缺一项保持 internal，不由模型自行“批准”。

## 按标选择规则

1. 先检查标书“类似业绩”的定义、年份、我方角色、材料、权限与硬排除。
2. 再按当前 Requirement、selected VP、Claim evidence burden 和 DecisionJob 查找具体 EvidenceItem。
3. 比较机制、规模、渠道、时效、我方角色、结果口径和可迁移边界，不只看行业标签。
4. 选择覆盖 qualification / experience / capability / method / outcome benchmark 的**最小充分 proof portfolio**，不设固定 3–8 个配额。
5. 没有安全案例就明确 material gap 并留待办，不能用第三方案例或无核验文字顶替我方业绩。
6. Task 3 只接收 approved public/anonymized projection，不读取完整敏感案例记录。

---
```
proposal skill · casebase v2
```
