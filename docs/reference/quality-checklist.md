# 方案修订质量评估清单

本清单用于回答同一 fixture、同一运行条件下，一次方案修订是否比另一次更优。它不是评委分、中标概率、跨项目排行榜或对真实客户的质量保证。先复制本页的记录表到仓库外基线目录，再由两名评审独立填写；不得把真实卷册或内部研判提交到仓库。

## 记录信息

| 字段 | 填写内容 |
|:---|:---|
| fixture | digital-demo / content-demo |
| 匿名版本 | A / B；揭盲前不得填写 pre / post |
| report hash | SHA-256 |
| run manifest | 同目录 manifest 文件名 |
| 评审 | reviewer-1 / reviewer-2；不要记录无关个人信息 |
| 评审时间 | 含时区的 ISO 8601 时间 |
| 可比性例外 | 模型、宿主、网络、重试、输入或参数变化；没有则写 none |

## A. 不可回退硬门

先判硬门，再看文风。每项记录 pass、fail 或 not_applicable，并给出报告位置或运行清单证据。只要新版本出现旧版本没有的硬门失败，新版本就不得判为“更优”，无论文风或人工分多高。

| 硬门 | 检查内容 | 结果 | 证据或 quote |
|:---|:---|:---:|:---|
| source 与编码 | 输入 manifest、hash、UTF-8 和来源路径有效；未混入真实 fixture 外资料 |  |  |
| compliance | mandatory、评分项和交付物覆盖；无 contradicted 或 missing 硬要求 |  |  |
| QA | 客户稿结构、编号、占位符、语言和禁项通过；warning 已人工判断 |  |  |
| canonical submission | 五份 canonical、snapshot、brief lineage 和 authoritative realization 有效 |  |  |
| 客户可见成果 | 每个 lead 的 required visible output 与全部 required fields 均为 filled；外部附件未替代正文 |  |  |
| 真实性与 Evidence | 事实、案例、数字和能力均有允许用途与范围；无虚构效果或扩大证明 |  |  |
| private、URL 与内部信息 | 无 private 原句、内部 ID、customer-fit、策略/工具痕迹、URL 或本机路径泄漏 |  |  |
| 预算、scope 与 authority | 不越预算；committed / confirmed 有授权；intended 未偷写成保证 |  |  |
| Gate 与 blocker | open / assumed Gate、fatal / blocker 和 accepted risk 均按规则处理 |  |  |
| 人工待办 | 法定模板、盖章、日期、投标人、附件和硬占位符没有被误报为已完成 |  |  |
| report-level readiness | receipt 绑定最新 state/report hash；compliance、QA、submission、fit、todo 与 Gate 2 同轮；auto 为 draft_only |  |  |

硬门结论：pass / fail。若 fail，停止“更优”结论，但继续记录 proof 缺口以支持诊断。

## B. 项目化成果指标

### 状态口径

对每个 required document proof 的每个字段，由两名评审在不讨论的情况下分别标记：

- filled：正文中已经填入当前 fixture 的具体内容，字段完整、彼此一致，客户此刻可以审阅或使用；
- partial：出现了有用的项目内容，但必填字段、连通关系或可使用程度不完整；
- missing：对象或字段不存在，只有字段名、空表、通用方法、占位符、“后续形成”，或只指向外部附件。

评审必须保存正文原句和位置。分歧在两份原始记录都冻结后再形成 consensus；不得覆盖原始判断。

### 稳定指标键

| 稳定键 | 定义与计算 | 必填记录 |
|:---|:---|:---|
| proof_object_coverage | required document proof 中 consensus=filled 的对象数 / required 对象总数；partial 不进入分子，同时单列 | 分子、分母、百分比、partial 数 |
| lead_proof_coverage | 已选 lead VP 中至少连接一个客户可见且 filled proof 的数量 / lead VP 总数 | VP 名称、proof、正文 quote；无可读 VP 映射时记 not_evaluated |
| proof_field_completeness | 全部 required proof 字段中 consensus=filled 的字段数 / required 字段总数；partial 单列 | 每个字段状态、分子、分母、百分比 |
| external_substitution_violations | 用未来 MP4、附件、签约后模板或其他外部交付替代当前正文 proof 的次数 | 每次替代表述、被替代对象和位置 |
| deferred_proof_burden | 核心选择理由仍依赖“后续形成、签约后补、递交前补、另行提供”的独立数量 | 逐项 quote；普通非核心待办不混入 |
| project_specificity | 每个成果对象标 specific、mixed 或 generic：是否填入当前 fixture 的场景、受众、内容和输出，而非只贴字段名 | 对象状态、至少一条支持 quote |
| unexpected_claims | 具体化过程中新增且无法由 tender/materials/授权 Evidence 支持的事实、数字、能力或效果数量 | claim、位置、查过的来源、风险级别 |

pre-change 没有结构化成果 manifest 时，按本节人工判断。v3.1 post-change 优先读取 authoritative `visible_output_realizations`，但仍由人工复核正文；为保持基线可比，历史稳定键名称不改。

### Proof 字段记录表

每个字段占一行；对象级状态只有在其全部关键字段 filled 且整体可使用时才能为 filled。

| proof 对象 | required 字段 | reviewer-1 | quote / 位置 | reviewer-2 | quote / 位置 | consensus |
|:---|:---|:---:|:---|:---:|:---|:---:|
|  |  | filled / partial / missing |  | filled / partial / missing |  |  |

### Digital fixture 必查对象

| 对象 | required 字段 |
|:---|:---|
| DIG-P01 四周栏目日历 | 连续四周；不少于 20 个已填选题；日期、栏目、目标受众、主题、载体、核心信息、素材、责任角色、发布时间 |
| DIG-P02 完整样例图文 | 主标题、导语、正文、行动指引、事实边界、配图说明；不是提纲 |
| DIG-P03 数据看板示例 | 内容编号、栏目、载体、发布时间、触达、完整阅读或完播、互动、行动转化、风险、口径、来源 |
| DIG-P04 优化演示 | fixture 数据标识、观察、判断、下一周期动作、责任人、验证指标；不作因果或历史业绩推断 |

### Content fixture 必查对象

| 对象 | required 字段 |
|:---|:---|
| CON-P01 已填订单简报 | 背景、目标、受众与障碍、单一核心信息、输出规格与载体关系、已知/待确认/禁项、责任决策链、时点版本、验收 |
| CON-P02 已填内容母版 | 受众、主题、主标题、核心文案、视觉锚点、视频适配、海报适配、图文适配、各载体事实边界 |
| CON-P03 45–60 秒分镜 | 全片连续 timecode、具体画面动作与景别、旁白或字幕、事实边界或依据、转场、声音/图形/无障碍字幕提示 |

### 指标汇总表

| 稳定键 | reviewer-1 | reviewer-2 | consensus | 证据索引 |
|:---|:---:|:---:|:---:|:---|
| proof_object_coverage |  |  |  |  |
| lead_proof_coverage |  |  |  |  |
| proof_field_completeness |  |  |  |  |
| external_substitution_violations |  |  |  |  |
| deferred_proof_burden |  |  |  |  |
| project_specificity |  |  |  |  |
| unexpected_claims |  |  |  |  |

## C. Customer-fit 与人工质量判断

### 十维 customer-fit

沿用 RULES.md 的十维和内部锚点，不另造加权总分。记录引擎在 submission checkpoint 给出的 deficient、fragile、adequate、strong、distinctive 或 not_evaluated，以及 importance、reason 和人工核对意见。

| 维度 | 版本结果 | importance / reason | 人工核对与 report quote |
|:---|:---|:---|:---|
| need_alignment |  |  |  |
| role_decision_coverage |  |  |  |
| insight_credibility |  |  |  |
| value_strength |  |  |  |
| differentiation |  |  |  |
| evidence_quality |  |  |  |
| delivery_readiness |  |  |  |
| commitment_safety |  |  |  |
| reading_efficiency |  |  |  |
| consistency |  |  |  |

任一 hard gate 失败时 overall 必须 withheld；critical dimension 为 fragile 时不得称 competitive 或 strong。not_evaluated 不是通过，也不能用人工印象补写成引擎已评估。

### 八项人工质量锚点

两名评审分别给 1–5 分并引用正文。1 和 5 是可观察端点；2–4 只用于确实落在两端之间的文本，不得用“较好”“优秀”循环定义。不要把八项相加成总分；对比时报告每项变化、评审范围和分歧。

| 人工项 | 1 分可观察锚点 | 5 分可观察锚点 |
|:---|:---|:---|
| 客户/项目特定性 | 替换项目名后几乎可投给其他客户；关键段只重复行业常识 | 主要判断、场景、对象和动作持续使用本 fixture 的独特事实，且解释这些事实如何改变方案 |
| 认知增量 | 主要复述标书或罗列流程，客户读完没有新的可行动判断 | 提供由材料推出、可检查且改变取舍的非显然判断，并连接到排期、内容或验收 |
| 成果对象的可使用完整度 | proof 缺失、空模板或承诺以后补，客户现在无法判断成品 | required proof 已填、字段完整、彼此一致，客户可直接审阅并交给下一角色执行 |
| 证据—主张—成果连通性 | 主张找不到依据，Evidence 只是案例装饰，成果与选择理由脱节 | 关键选择可沿安全来源、有限主张、客户可见成果和验收一路追溯，没有扩大证明 |
| 选择理由是否容易被对手复制 | 理由是“专业、创新、全流程、丰富经验”等任意对手可照抄的话 | 理由依赖本项目特定约束、明确机制和已证资源组合，删掉这些事实就不成立 |
| 叙事温度与 mode 一致性 | 文本自述叙事模式、语气错位，或用故事/愿景掩盖事实和边界 | 开篇、材料顺序、节奏和温度稳定符合选定 mode，同时报价、合规、资质仍清楚克制 |
| 阅读压缩度 | 内部边界声明、审计语言、同义重复和表格淹没有效信息 | 必要边界一次说清，各章持续增加新判断，标题、段落和表格让评委快速找到答案 |
| 客户可执行方案感 | 主要像生成过程、canonical 或内部审计说明，客户任务和成果靠读者自行拼接 | 以客户决策和使用顺序组织，责任、时点、成果与验收清楚，内部机制不打断阅读 |

| 人工项 | reviewer-1 分数与 quote | reviewer-2 分数与 quote | consensus / 分歧说明 |
|:---|:---|:---|:---|
| 客户/项目特定性 |  |  |  |
| 认知增量 |  |  |  |
| 成果对象的可使用完整度 |  |  |  |
| 证据—主张—成果连通性 |  |  |  |
| 选择理由是否容易被对手复制 |  |  |  |
| 叙事温度与 mode 一致性 |  |  |  |
| 阅读压缩度 |  |  |  |
| 客户可执行方案感 |  |  |  |

## D. 盲评对比协议

### 1. 冻结可比条件

- 使用同一 fixture、同一 tender/materials 文件 hash、同一深度、同一 narrative、同一用户回答或 auto 状态；
- 尽量使用同一可用模型、宿主版本、工具配置和研究能力；无法冻结的网络与模型漂移写入 uncertainty；
- pre-change 与 post-change 都保留完整 run manifest、测试结果、失败/重试记录和 report hash；
- 不为追求逐字一致关闭正常 Evidence 流程，也不把搜索漂移藏起来。

### 2. 匿名和独立判断

由不参与评分的人把两份客户可见报告复制为随机 A/B 文件名，另存映射并在两名评审冻结原始记录前不揭盲。两名评审先各自判硬门，再逐字段判 proof，最后判十维和八项人工质量；不得先看版本日期、内部研判、git diff 或另一名评审的分数。

### 3. 判定顺序

1. 硬门：任何回退立即否决“更优”；
2. proof：比较 proof_object_coverage、proof_field_completeness、替代违规、延后负担、特定性和 unexpected claims；
3. customer-fit：确认十维无规则性回退和夸大结论；
4. 人工质量：比较关键项的锚点变化、quote 与评审一致度；
5. 揭盲：只在两名评审原始表与 consensus 都保存后打开映射。

### 4. “更优”的最低条件

只有同时满足以下条件，才能对该 fixture 说“新版本相对更优”：

- 不可回退硬门没有退步；
- unexpected_claims 和 external_substitution_violations 没有增加；
- proof_object_coverage 或 proof_field_completeness 有实质改善，且成果对象的可使用完整度没有下降；
- 至少一个预先指定的关键人工项改善，其他关键项无不可解释的明显下降；
- 结论明确限定在本 fixture、本次运行条件和本次相对修订。

若两个 fixture 结果分裂，分别报告，不用平均数掩盖。结果不得表述为评委分、中标概率、行业排名或跨标质量结论。

### 5. 对比结论记录

| 项目 | 结论 |
|:---|:---|
| 硬门是否无回退 |  |
| proof 改善与代价 |  |
| customer-fit 变化 |  |
| 人工关键项变化 |  |
| uncertainty |  |
| 可比性 | comparable / partially_comparable / not_comparable |
| 限定结论 | better / no_material_change / tradeoff / worse / withheld |
| 两名评审签核 | reviewer-1 / reviewer-2；日期 |
