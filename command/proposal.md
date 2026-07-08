---
description: 政企传媒投标方案生成 — 读甲方标书，联网调研，产出保基础、控成本、给惊喜的正式投标方案文档
---

<command-instruction>
Load and follow the `proposal` skill exactly.

```text
skill(name="proposal")
```

Parse `$ARGUMENTS`:
- 标书输入：本地文件路径（.pdf/.docx/.md/.txt）或粘贴的标书文本（二者必居其一，否则向用户索要）
- 可选素材：案例库/资质/报价参考的路径
- 模式标志：
  - `-quick` → 快速应标（小标/时间紧）
  - `-deep`  → 大标/重点项目（强竞争/多轮答辩）
  - 无标志   → 标准投标（默认）
- 叙事标志（可选，可与模式标志并用；无标志则由 Task1 按标书特征自动判定）：
  - `-logic`    → 逻辑征服（论证链服人，适合技术分权重高/专家评委/暗标）
  - `-story`    → 故事打动（叙事弧线动人，适合城市形象/文旅/品牌传播/有讲标环节）
  - `-vision`   → 愿景共创（未来图景+伙伴关系，适合多年框架/长期代运营）
  - `-evidence` → 数据实证（可核验结果说话，适合效果导向/投放增长类）
</command-instruction>

<user-request>
$ARGUMENTS
</user-request>

---
```
proposal skill · 政企传媒投标方案生成
```
