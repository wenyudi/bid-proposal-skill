---
schema_version: case-record/v2
case_id: CASE-UNIQUE-ID
status: draft
name: 项目名称（客户 + 项目一句话）
client: 客户全称
client_type: 政府
industry: 行业标签
services: 服务1, 服务2
start_date: 2026-01
end_date: 2026-12
budget: 金额+单位
bidder_role: unknown
engagement_scope: 我方实际承担的范围
visibility: internal_only
allowed_uses: matching
client_name_permission: false
logo_permission: false
testimonial_permission: false
numeric_result_permission: false
qualification_material_available: false
sensitive_or_disputed: false
---

## 背景与客户任务

只写可核验事实；不推测客户内部动机。

## 我方实际范围与做法

说明 prime/consortium/subcontract 角色、包含与未承担范围、关键交付。

## 原子证据

```json
{
  "schema_version": "case-evidence/v1",
  "items": [
    {
      "id": "CE-UNIQUE-01",
      "kind": "engagement_fact",
      "statement": "一条原子、可核验的事实",
      "scope": "事实适用范围",
      "period": "YYYY-MM 至 YYYY-MM",
      "source_material": "合同/验收/截图/证书的具体位置",
      "verification_status": "material_listed",
      "visibility": "internal_only",
      "allowed_uses": ["matching"],
      "safe_title": "",
      "approved_wording": "",
      "publication_authority": "",
      "limitations": "这条材料不能证明什么"
    }
  ]
}
```

## 风险、争议与使用限制（内部）

如有敏感、失败、争议、归因不足、过期或授权限制，在这里如实记录。
