# 客户价值模型

v3 的客户价值模型回答的不是“方案里有哪些模块”，而是“不同客户角色为什么会认为这份方案值得选、可信、可执行且风险可控”。

## 从真实决策角色开始

CustomerRole 不是想象出来的性格画像，而是本标中有依据的判断、使用、监督、否决或履约角色。例如业务负责人、评标专家、采购合规、财务纪检、决策领导和最终使用者。

角色的几个维度分开记录：

- formal power：正式决策权；
- veto：明确否决权；
- practical influence：实际影响；
- delivery impact：对履约的影响；
- scrutiny：被审计或问责的程度。

低置信度推断可以调整软优先级，不能凭空制造硬否决或个人偏好。

## Requirement、Need 与 Criterion 不相同

- **Requirement** 是标书要求投标人必须响应或争取的内容。
- **CustomerNeed** 是某个角色希望获得的结果，或希望避免的风险。
- **DecisionCriterion** 是该角色判断方案可信、优选或不可接受的标准。

例如，“提交月度运营报告”可以是 Requirement；业务负责人真正需要的是“减少日常盯盘成本”；其 Criterion 可能是“异常可发现、责任可定位、决策有依据”。只重复月报要求，只能保基础；把月报设计成可执行的决策闭环，才可能形成价值。

## 覆盖单位为什么是 Role × Need × Criterion

同一个 Need 对不同角色并不等价。业务负责人关注省心，财务纪检可能关注留痕，评标专家关注方法是否成立。v3.3 继续用一个轻量 `DecisionPath` 直接记录有依据的 `Role × Need × Criterion`，而不是维护三套可漂移 link 或只列一个笼统“客户需求清单”。

它也不会生成全图笛卡尔积。路径分为 required、expected、exploratory，只有有来源或有明确决策意义的组合才进入覆盖义务。

## 从客户价值到可交付承诺

```text
Role × Need × Criterion
          ↓
ValueProposition：客户会得到怎样更好的结果、更低风险或更少管理成本
          ↓
Claim：正文允许表达的原子主张及其知识/承诺强度
          ↓
EvidenceLink：具体 Evidence 为什么、在什么 scope 内支持该主张
          ↓
DeliveryAction：由谁、在何时、用什么资源执行
          ↓
AcceptanceContract：怎样验收、留痕和纠正
          ↓
Section：内嵌 DecisionJob 与客户可见成果契约
          ↓
realization：正文是否回答、兑现并把成果字段填实
```

ValueProposition 不是标书条款的换句话说。“完成平台日更”是响应义务；“用可替补内容产能和异常响应机制降低业务方日常催办成本”才是可检验的价值主张。

## 一页纸策略与 Big Idea 的位置

一页纸策略先解释客户张力、尖锐洞察、核心命题和洞察到执行/证明的推导；Big Idea 只是其中 core thesis / recall line 的表达投影。它帮助评委记住方案，但不替代原子价值，也不能掩盖证据或交付短板。

一个漂亮主题如果无法连接 Role、Need、Criterion 和真实 Action，只能留作候选表达；反过来，底层完整但没有记忆结构的价值组合，也可能在评标现场失去辨识度。v3 要求二者相互支撑，而不是互相冒充。

## 严格模型会不会限制方案发散

候选阶段和发布阶段采用不同门槛：

- candidate 可以缺 Evidence，可以探索新机制；
- investigating 表示值得查证，而不是立即淘汰；
- 未知能力或新增成本进入 Gate；
- selected 可以进入 safe draft；publishable / committed 才需要完整的证据、authority 和交付确认。任何阶段都不能泄露 private 或编造能力。

因此 Task 1 只加载策略骨架，不加载 rubric 和反模式；模型不会在灵感刚出现时就要求它像合同承诺一样完备。研究后 Task 2.5 才用行为锚点收敛一页纸，未选命题仍留在 reserve。这样质量门定义写作入口，不反向删除发散历史。

选择也不奖励数量。lead 负责最关键的客户判断，supporting 补足组合缺口，reserve 保留后手。最终少而强，比把所有候选写进正文更利于评委形成清楚判断。

## 角色冲突怎样处理

不同角色的需求冲突时，优先级是：

1. 法律、mandatory、预算、真实性和明确 veto；
2. 投标人能力边界；
3. 能同时服务多个角色的共同解；
4. 评分权重、角色优先级、Evidence 和损失比较。

重大能力、报价或偏好取舍形成 diagnostic/Gate decision，不另维护 `role_conflicts` 主 collection，也不由叙事策略暗中决定。CustomerDependency 不能把我方责任转嫁给客户，必须提供延误影响、安全 fallback 和升级路径。

## DecisionJob 如何改善阅读

DecisionJob 直接内嵌 Section。每个正式章节只有一个 primary、最多一个 secondary；它描述评委读完本章应形成的新判断，例如“相信该机制能持续产出”或“确认风险和预算可控”。

同一 VP 或 Claim 跨章出现时，必须贡献不同增量：introduce、prove、operationalize、measure、price 或 derisk。没有增量的重复会被视为阅读负担。

这些 Job 不会作为标签印在客户稿里。writer 只把它们转化为标题、材料顺序、论证节奏和自然过渡。

每个 lead VP 还要在所属章给出一个小型 `visible_output` contract：它只规定评委要看到什么、必填字段和 truth boundary，不规定表格或版式。全案从这些对象中选择一个 signature 主亮点，其余分为 supporting/reference。这样保留写作发散，同时让评委既看到可检查对象，也能迅速分辨“最值得记住的一个”。

## customer-fit 的作用

customer-fit 用十个维度检查客户路径、证据、价值、差异化、交付、承诺和阅读效率。它输出 withheld / fragile / credible / competitive / strong 的内部 ordinal rating 和 top gaps，不输出伪精确权重/区间，也不是“我们能得多少分”。visible output filled 只影响成果完整性，不再推断阅读效率；后者以及独立差异化判断必须有当前报告 exact quote。未评价 differentiation 或 reading efficiency 时，不能称 competitive/strong。

scorecard 规定修复目标，不规定唯一创意解；同一客户问题仍可以有多个不同但都可靠的方案方向。
