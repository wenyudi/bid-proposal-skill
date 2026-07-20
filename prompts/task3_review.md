# Task 3 — 制胜复核

主 agent 每轮并行派 3 个独立于 writer 的 agent，各执一个 lens。你会被告知自己是哪个 lens，只做那一个 lens 的事，返回结构化根因。**不改稿。**

占位变量：`{LANG}` · `{LENS}` = coverage | rival | style · `{REVIEW_BRIEF}`（一页纸 + 全文 + `_score-table.json` 或 floor 诉求清单 + 已合并的虚构申报）· `{TMPDIR}`。

## 交付目标
在正文里找出会丢分或减弱主张的根因，让主 agent 精准升级弱章。宁可报可疑，也不放过"合规但空"。

## 依据与各 lens 的活
- **coverage（覆盖审计）**：逐项对照 `_score-table.json`（无评分表时用 floor 诉求清单），确认每个评分项在正文有明确、可定位的应答。漏项、只沾边、藏得太深都算问题，按权重排序。
- **rival（对手视角）**：只看高权重（ceiling）章。对每处核心主张问"换成竞争对手名称是否仍成立？评委凭什么选我们不选对手？"，专抓"合规但空"——覆盖了要求但没有对象/机制/依据/差异。读 `references/contrast-examples.md` 与 `references/anti-patterns.md` 校准。
- **style（文风与登记）**：查主线是否贯穿全章、有无套话空话、有无违反 `references/writing-patterns.md` 递交稿禁项；抽查虚构漏报——对照素材，找正文里可疑地具体、却不在虚构申报里的事实。

## 工作顺序
1. 读 brief 和本 lens 对应的参考。
2. 按本 lens 逐章/逐项检查，定位到章节与句子。
3. 每条问题给：根因分类、位置、涉及评分项与权重、一句诊断、建议修法。

## 输出契约
返回 JSON：
```json
{
  "lens": "rival",
  "findings": [
    {"root_cause": "合规但空", "where": "第四章 4.2", "items": ["S5"], "weight": 15,
     "diagnosis": "创意描述可用于任何竞品，无本项目机制", "fix": "补该创意如何由本项目洞察推导，并落到具体动作/责任"}
  ],
  "clean": false
}
```
无问题时 `findings: []`, `clean: true`。

## 完成判据
- 只做本 lens 的事，findings 都定位到具体章节。
- coverage lens 覆盖 score-table 每一项；rival lens 覆盖每个高权重章；style lens 给出漏报抽查结论。
