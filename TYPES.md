# 提案类型、叙事与评审先验

本文件只帮助 Task 1 做完备性检查、研究排序和叙事选型，不是事实、固定章节模板或评分权重。标书、澄清、公开职责和用户确认始终优先；先验最多 medium confidence，不能单独生成 required path、selected VP、committed Claim 或 blocker。

## 六类常见标型

| 标型 | 适用信号 | 评委重点 | 优先补的 Evidence / Delivery burden | 典型客户可见成果 |
|:---|:---|:---|:---|:---|
| 品牌传播 / IMC | 年度传播、形象升级、整合战役 | 策略闭环、Big Idea、跨渠道性价比 | 受众/品牌依据、创意机制、渠道协同、版权与舆情 | 内容样例 + 渠道编排 + 传播时序 |
| 活动 / 事件营销 | 发布会、节庆、路演、展会、赛事 | 体验亮点、现场落地、安全应急 | run-of-show、场地/人员容量、审批、彩排、fallback | 分钟级流程 + 体验节点 + 应急卡 |
| 数字营销 / 新媒体 | 代运营、社媒矩阵、内容/投放增长 | 持续产能、数据闭环、平台与政务合规 | 基线、栏目产能、排班、平台规则、数据源与优化频率 | 已填内容日历 + 样帖 + 看板/优化示例 |
| 政务宣传 / 城市形象 | 政策解读、城市/文旅、主题宣传 | 导向、权威性、公共价值、舆情安全 | 政策原文、公开城市事实、受众依据、审校与升级机制 | 叙事样例 + 内容矩阵 + 审校路径 |
| 影视 / 内容制作 | 宣传片、纪录片、TVC、短视频 | 立意/质感、样片、里程碑、版权 | 我方样片角色、主创可用性、脚本分镜、素材授权、审改验收 | 含时间码/画面/声音的分镜 + 视觉系统 |
| 媒介采购 / 投放 | 户外/线上/电视采购与执行 | 资源真实性、价格、监播、结案 | 刊例/授权、库存点位、折扣依据、覆盖测算、监播与补量 | 计算样例 + 排期分配 + 监播证据样式 |

使用规则：

1. 先读本标 Requirement、角色依据和组织职责；表中角色/成果可判 not_applicable，未列内容也可加入。
2. 章节完全服从评分骨架；整合型项目可融合多行，不为补齐类型新增孤儿章。
3. 成果示例只提示“评委需要看到什么”，Task 2.5 仍要依据本项目 truth boundary 收敛 `visible_outputs`；不能照表编造内容。
4. 真实投标后的误报、遗漏和客户反馈作为校准样本；不因一次胜负固化先验。

## 客户决策进程

`job_kind` 只有 understand / believe / value / deliver / safe / choose。它们可合并、回访、重排，不要求六阶段一一对应章节。DecisionJob 内嵌所属 Section，只描述“谁依据什么标准，在本章后形成什么新判断”，不把术语写进客户稿。

## 一页纸客户语境

| context | 主要“好”标准 | 不可平均掉的边界 |
|:---|:---|:---|
| `government_public` | 公共价值、政策连续性、服务可达、治理与审计妥帖 | 不用商业焦虑贬低现状，不以声量替代公共结果 |
| `commercial` | 生意洞察、客户行为、经济机制、可验证增长 | 不用宏大愿景替代购买/使用摩擦与商业取舍 |
| `hybrid` | 明确以上哪一套为主、另一套为约束 | 不能把两者平均成“品牌+社会效益双提升”套话 |

## customer-fit 十维索引

need_alignment、role_decision_coverage、insight_credibility、value_strength、differentiation、evidence_quality、delivery_readiness、commitment_safety、reading_efficiency、consistency。

十维只输出 ordinal level 与 overall rating，不设类型固定权重或伪精确区间；`not_evaluated` 不得宣称 competitive/strong。

## 红队角色索引

| key | 关注点 |
|:---|:---|
| `buyer` | 是否真正解决客户问题、减少管理负担、有人负责 |
| `expert` | 逻辑、专业机制、数据/案例可比性与可执行性 |
| `strategy_critic` | 洞察锐度、记忆句、推导闭环、名称互换、signature 主亮点、阅读效率、逐章主线与落地可信度 |
| `audit` | mandatory、真实性、报价、授权、负偏离与政务导向 |
| `rival` | 差异化是否可复制、最脆弱环节、资源/价格被反制方式 |
| `buyer_expert` | 兼容旧 profile 的 buyer + expert 合并角色 |
| `audit_rival` | standard 合并 audit + rival，同时看合规硬伤与对手利用方式 |
| `integrated` | quick 一次覆盖四类；硬门不降级，只减少调用 |

红队无最低条数、不改稿。明确硬门立即修，其余 root cause 进入 Gate 2。

## 叙事选择索引

完整写作 guide 的单一事实源是 `narratives.json`，`compile-context` 只投影当前模式的短 guide。这里仅用于 Task 1 选型：

| mode | 优先信号 | 主要风险 |
|:---|:---|:---|
| `logic` | 技术/服务方案重、暗标、机制复杂 | 变成枯燥说明书 |
| `story` | 城市/文旅/公益/品牌、创意契合度高、需讲标 | 虚构场景或故事盖过评分响应 |
| `vision` | 多年框架、长期代运营、明确战略语境 | 愿景无本合同期交付 |
| `evidence` | 效果/投放/增长、量化与报价确定性强 | 数据越权、目标冒充保证 |
| `custom` | 四种均不贴，且能写清手法与理由 | 风格缺乏统一边界 |

选择顺序：用户显式指定 → 命中信号最多 → 最高权重评分维度定夺 → custom。主叙事全案唯一，可有 secondary；Section 用 `narrative_role=primary|secondary:<mode>|fixed:logic|fixed:evidence` 声明本章取法，报价、合规、资质必须 fixed。叙事只有 presentation authority，不裁剪 Requirement 或改变承诺。

## 客户稿编号

| 层级 | Markdown | 格式 | 示例 |
|:---|:---|:---|:---|
| 章 | `##` | 汉字数字 + 顿号 | `## 三、传播策略与大概念` |
| 子节 | `###` | 阿拉伯数字 N.x | `### 3.1 核心传播主张` |
| 子子节 | `####` | 括号阿拉伯数字 | `#### (1) 线上引爆路径` |

同层统一、不可跳级；每章子节从 N.1 开始。内部成果契约和 audit label 不出现在标题中。

---
`proposal skill · 3.3.0 · comparative-strategy lean priors`
