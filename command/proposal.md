---
description: 政企传媒投标方案 v3.1 — 客户价值、正文成果、独立审计与 receipt 终验
---

<command-instruction>
Load and follow the `proposal` skill exactly.

```text
skill(name="proposal")
```

Parse `$ARGUMENTS`:
- 标书输入：本地文件路径（.pdf/.docx/.md/.txt）或粘贴的标书文本（二者必居其一，否则向用户索要）
- 可选素材：资质/报价参考的路径；**沟通纪要**（踏勘/答疑会/售前笔记 → 标 `[notes]`，只作理解输入，不进正文）
- 案例库：`{SKILLDIR}/casebase/` 非空则自动纳入，无需传路径
- 模式标志：
  - `-quick` → 快速应标（小标/时间紧）
  - `-deep`  → 大标/重点项目（强竞争/多轮答辩）
  - 无标志   → 标准投标（默认）
- 叙事标志（可选，可与模式标志并用；无标志则由 Task1 按标书特征自动判定）：
  - `-logic`    → 逻辑征服（论证链服人，适合技术分权重高/专家评委/暗标）
  - `-story`    → 故事打动（叙事弧线动人，适合城市形象/文旅/品牌传播/有讲标环节）
  - `-vision`   → 愿景共创（未来图景+伙伴关系，适合多年框架/长期代运营）
  - `-evidence` → 数据实证（可核验结果说话，适合效果导向/投放增长类）
- 关卡标志：
  - `-auto` → 自动生成安全草案，跳过人工确认；`apply-auto-state` 生成 assumed、降级失效授权并进入待办，receipt 必须为 draft_only
  - 无标志  → 默认停 ⛳ Gate 1 与 ⛳ Gate 2；每轮只问一个决策并给推荐。quick 合并红队调用，但要 submission-ready 仍需 Gate 2 attestation
- 引擎标志：
  - 无标志 / `-v3` → v3（默认；`-v3` 仅作兼容 no-op）
  - `-legacy` → 显式运行 2.x 回退链，加载 `LEGACY.md`；不得与 v3 状态或章节混用
</command-instruction>

<user-request>
$ARGUMENTS
</user-request>

---
```
proposal skill · 3.1.1 · lean direct-default
```
