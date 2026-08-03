# Task 3 — 制胜复核

主 agent 每轮并行派独立于作者的 agent，各执一个 lens：**管理标 3 lens**（coverage/rival/client）；**创意标复核轮只派 rival/client**——coverage 不进复核轮，改在编译期以**封标模式**单独调用。你会被告知自己是哪个 lens，只做那一个 lens 的事，返回结构化根因。**不改稿**——修复由作者本人执行（声音不能换人）。

占位变量：`{LANG}` · `{LENS}` = coverage | rival | client · `{MODE}`（coverage 专用：review=复核轮｜seal=封标模式）· `{REVIEW_BRIEF}`（一页纸 + `_draft.md` 全文 + `_score-table.json` 或 floor 诉求清单 + 已合并的虚构申报 + 选中创意的 concept brief）· `{TMPDIR}`。

## 交付目标
找出会丢分、减弱创意、或让方案变"普通/像报告"的根因，让作者精准修复。宁可报可疑，也不放过"合规但空"。

## 各 lens 的活
- **coverage（覆盖，内部核对）**：`{MODE}=review`（管理标复核轮）：逐项对照 `_score-table.json`（无表用 floor 诉求清单），确认每个评分项在其认领章有明确、可定位的应答。漏项、只沾边、藏太深都算问题，按权重排序。`{MODE}=seal`（创意标编译期封标核对）：此时评分项尚无认领章——把每项逐一映射到成稿最能应答它的章节（映射结果由主 agent 回填 `claimed_by_section`）；映射不上的列为缺口并分流：**行政类**（资质/团队/售后/编制递交等，可独立成章不伤正文）建议补行政章，**实质类**（内容硬要求、创意正文该覆盖而没覆盖）列为回作者定向修复项。只判"能不能定位应答"，不评文风。
- **rival（制胜/对手视角）**：先做**创意层复评**——成稿配得上选中的创意吗？巅峰章有没有把 concept brief 里的推导与 signature 真正立起来，还是把创意稀释成了流程？然后只看高权重章，问"换成竞争对手是否仍成立"，专抓五类："合规但空"、"罗列而非价值"、假精确（同一公式批量数字、小数点级假实测值）、内行缺位（对照内行颗粒清单）、创意同构。读 `references/contrast-examples.md` + `style-checklist.md` 的病灶判例校准。
- **client（客户体验）**：站甲方视角把**一切客户会看到的载体**读一遍——正文、综述，以及（若已生成）PPT 客户面字段与讲稿。按 `references/style-checklist.md` 五组逐项走查：复读类、声线类、密度与节奏类、包装类、真实性类（含虚构漏报抽查与内部披露：评审元话术、草案状态、内部定价规则）。lint 已抓词面，你抓语义层残余。

## 工作顺序
1. 读 brief 和本 lens 对应的参考。
2. 按本 lens 逐章/逐项检查，定位到章节与句子。
3. 每条问题给：根因分类、位置、涉及评分项与权重（若相关）、一句诊断、建议修法。

## 输出契约
返回 JSON：
```json
{
  "lens": "client",
  "findings": [
    {"root_cause": "创意稀释|覆盖缺口|合规但空|罗列非价值|假精确|内行缺位|创意同构|复读注水|声线|密度节奏|包装|免责外显|虚构漏报|内部披露", "where": "第三章 3.4",
     "diagnosis": "一句诊断", "fix": "建议修法"}
  ],
  "clean": false
}
```
无问题时 `findings: []`, `clean: true`。

coverage 封标模式（`{MODE}=seal`）改返回：
```json
{
  "lens": "coverage", "mode": "seal",
  "mapping": [{"id": "S1", "section": "确切章节标题"}],
  "gaps": [{"id": "S9", "kind": "admin|substantive", "text": "评分项原文", "fix": "补行政章建议 或 回作者修复点"}]
}
```

## 完成判据
- 只做本 lens 的事，findings 都定位到具体章节。
- coverage 覆盖 score-table 每一项（seal 模式：每项要么进 mapping 要么进 gaps，无第三态）；rival 给出创意层复评结论并覆盖每个高权重章；client 走完 style-checklist 五组并给漏报抽查结论。
