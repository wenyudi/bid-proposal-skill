# 证据、授权与隐私

v3 把“事实是什么”“它能证明什么”“能否对客户说”“能否据此作出承诺”拆开。这样可以避免一份材料被从参与事实一路放大成能力、结果和保证。

## Evidence 与 EvidenceLink 分开

Evidence 是本标中的原始记录，例如政策原文、平台规则、合同、验收、截图、公开报道或已核验案例材料。它拥有来源、时间、visibility、quality、status 和 allowed uses。

EvidenceLink 才说明：

- 这条 Evidence 支持或反驳哪个 Need、Criterion、VP 或 Claim；
- 为什么相关；
- 有效 scope 是什么；
- 支持强度是多少。

同一 Evidence 可以支持多个对象，但每条 link 都必须单独说明 reason 和 scope。把 Evidence 放进池里，不代表所有 Claim 自动有证据。

## 材料的证明边界

| 材料 | 能证明 | 不能自动证明 |
|:---|:---|:---|
| 合同 | 我方参与和合同约定范围 | 实际完成质量、全部结果、超出合同的能力 |
| 验收报告 | 被验收对象和验收范围 | 未验收内容、长期效果、完整归因 |
| 数据截图 | 特定时点、特定口径的数据 | 持续表现、我方独立贡献、未来目标 |
| 行业或第三方案例 | benchmark、机制可行性 | 我方能力、我方业绩、我方可承诺结果 |
| 证书或人员材料 | 文件载明且当前有效的资格 | 本项目实际可用性、未写明的经验 |

历史结果也不能直接变成本项目保证值。量化 Claim 还需要基线、公式或统计对象、单位、窗口、数据源、影响因素和验收口径。

## 可见性与用途是两道门

一个 Evidence 即使是 public，也不一定允许用于 bidder capability；一个案例即使允许匿名叙述，也不代表客户名、Logo、评价、金额或数字结果获准。

可用于客户稿的来源必须有安全投影：

- public / tender / authorized source 使用已批准内容；
- approved anonymized 还必须有 `safe_title`、`approved_projection` 和 scoped publication authority；
- private / internal / unknown 不得直接进入 writer brief 或客户稿。

public Evidence 在研究状态中必须保留抓取 URL，便于复核；客户稿只写机构或文件名与年份，不显示 URL 书目。

## `[notes]` 为什么只能内部使用

沟通、踏勘、售前和答疑纪要可能帮助理解真实约束，但直接引用会带来隐私、不正当接触或语境误读风险。v3 把 `[notes]` 作为 private 校准：

- 原句不进入客户稿；
- 个人偏好不能凭空变成正式否决；
- 后来找到公开依据时，也只使用独立公开投影；
- writer 只收到脱敏的 forbidden boundary 或 safe constraint。

QA 会对 private/internal/匿名前 canonical 原句做规范化指纹扫描，防止换了空格或标点后重新泄露。

## Evidence 强度如何匹配 Claim

publishable Claim 不能依赖 unknown、expired、contested 或 private-only Evidence。高风险 Claim 要求更高质量与更直接的 link；反证足以改变方向时，相关 Need 或 Claim 应进入 contested，而不是隐藏反证。

Claim 同时有三条轴：

- fact / insight / proposal / target；
- evidenced / inferred / assumed；
- none / intended / committed。

有证据的 insight 不等于可以 committed；可执行的 intended proposal 也不等于有 authority 对外保证。

## Authority 从哪里来

committed Claim、confirmed Action、关键 Metric、资源和 Acceptance 的 authority 只能来自：

1. 明确授权该对象/用途的标书 Requirement；
2. active/current、high/verified、用途获准且 scoped 的 Evidence；
3. human-resolved 且 `affected_refs` 覆盖该对象的 Gate。

authority 是对象级、用途级的。任意 `GATE-*` 字符串、无关标书条款、assumed 决策或只有材料列表的 Evidence 都无效。

新增资源、免费增值、排他能力、关键 KPI、SLA 和 outcome guarantee 因此必须人工确认。`-auto` 会主动降级依赖 assumed Gate 的 committed、confirmed 和发布授权，而不是让自动模式更激进。

## 案例的渐进核验

案例库允许旧文本继续参与内部匹配，但只有被本标选中并承担资格、高风险业绩、数字或署名证明时，才需要渐进补齐人工字段。

`material_listed` 表示知道材料在哪里，不等于 `verified`。`capability_reasoning` 表示内部认为可能相关，也不自动获得 `bidder_capability` 用途。匿名发布所需的安全标题、批准措辞和授权必须由人提供。

这套设计使案例库可以逐步治理，而不需要先批量重写所有历史案例，也不会把历史模糊信息静默升级为投标事实。

## 最终责任

工具能检查一致性、来源和授权链，不能替投标人完成法律审核和事实签字。资质、业绩、人员、报价、数字结果与保证性承诺在递交前仍需由有权人员复核。
