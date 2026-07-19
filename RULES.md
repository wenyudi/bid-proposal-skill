# proposal v3.1 规则与硬门

本文件约束所有 Task、Gate、工具和客户可见正文。规则冲突时顺序为：法律/mandatory/真实性/预算/授权 → canonical 语义与交付边界 → 客户价值与阅读体验 → 叙事偏好。软适配度永远不能抵消硬门。

## 1. 权威性与写入权限

- 五份 canonical 各自只有一个 owner：requirements、customer-value、delivery-plan、strategy、intel-pool。相同事实不得复制成两份可手改真相。
- 主 agent 是逻辑单写者；Task/Gate 只提交 proposal/ChangeSet。Task 3、摘要、红队只能报告 observation/diagnostic。
- ChangeSet 必须有 base revision；先在临时副本应用全部 operation，校验 schema/ref/lifecycle/permission/cross-file gate，全部通过才原子提交并递增 revision。stale 拒绝，失败整组回滚。
- Gate answer 必须同步真正受影响的 Need/VP/Claim/Action/Resource/Acceptance/strategy；只改 decision.status 视为不完整。
- derived brief、coverage、diagnostics、fit、realization 与正文都不是事实源，不能反向静默改 canonical。

## 2. Mandatory 与真实性硬门

| 红线 | 规则 |
|:---|:---|
| 评分/强制零遗漏 | mandatory、scoring、deliverable 保留标书原意与权重；Requirement → Section 映射后还须在正文独立语义审计为 addressed，客户价值软分不可替代 |
| 资质/业绩/团队 | 必须来自标书、可核验用户材料或已授权案例 Evidence；不确定就留占位并阻断，不编造 |
| 案例边界 | 合同只证明参与和范围，截图只证明时点数据，验收只证明验收范围；第三方案例只作 benchmark/feasibility，绝不证明我方能力 |
| 数据与来源 | public Evidence 抓取原文并有 URL；作为支持必须 active/current、用途获授权、Link 有 scope/reason 且质量/强度匹配风险；正文只写机构/文件+年份，不写 URL。重要反证不可隐藏 |
| private | 沟通纪要、内部关系、底价、个人偏好只作内部约束；获得公开支持后也只用独立公开投影，不引用 private 原句。approved_anonymized 必须有人工批准 safe_title/wording 与 scoped authority，绝不回退 raw content |
| 政务导向 | 现状写“发展的下一步”，不渲染负面、不虚构具体人物事迹、不引用不正当接触信息 |
| 预算/负偏离 | 单一最优解在预算边界内；禁止用“排除项/不包含”转嫁 mandatory 责任 |

## 3. 客户价值模型

- CustomerRole 是有据的判断/使用/监督/否决角色，不是猜测的个人画像。formal power、veto、practical influence、delivery impact、scrutiny 分开；inferred 只能调软优先级，不能制造硬否决。
- CustomerNeed 是角色希望获得的结果或规避的风险；DecisionCriterion 是其判断可信、优选或不可接受的标准；Requirement 与二者可关联但不等同。
- coverage 基本单位是 Role × Need × Criterion，不做全图笛卡尔积。required/expected/exploratory 分开；同一 Need 对一个角色覆盖不自动代表其他角色。
- Role 冲突不另建主 collection；按法律/mandatory/预算/真实性/明确 veto → 投标人能力边界 → 多角色共同解 → 评分权重/优先级/Evidence/损失取舍形成 diagnostic 或 Gate decision。重大能力、报价、偏好冲突进 Gate。

### Need 与 Evidence

- Need 将 assertion_mode（explicit/inferred）、source visibility、evidence quality、inference confidence、priority 分开。
- 生命周期：candidate → active / contested / superseded / rejected。新 Evidence 追加，不覆盖历史；冲突足以改变方向时 contested，暂停生成新 publishable Claim。
- Task 2 只能加 Evidence/Link、反证和 change proposal，不能静默改 Need 含义。
- public Claim 不能只靠 private/unknown/expired/contested Evidence。

## 4. 发散与选择

- Task 1 从 Need、Criterion、真实能力/资产、已有案例交叉发散，并覆盖 outcome、efficiency、risk、visibility、experience、asset、contrarian 多镜头。candidate 允许缺 Evidence，不因最终硬门提前收窄。
- ResponseObligation 保基础；ValueProposition 解释客户为何得到更好结果、更低风险或更少管理成本。“完成标书要求”本身不冒充亮点。
- VP 生命周期：candidate / investigating / qualified / selected / publishable / rejected / superseded；组合角色 lead / supporting / reserve 正交。
- 只淘汰不可挽救项：违法/mandatory 冲突、确认能力/预算不可行且无缩减、无真实 Need/Criterion、只能依赖不可安全投影的事实、价值低于新增负担、与策略不可调和。
- 缺 Evidence 留 investigating；普通差异性可降基础增强；未知能力/成本进 Gate；重复等待合并/替代/组合。
- Task 2.5 用关键短板、Pareto 与组合充分性选 lead/supporting；不奖励数量、篇幅、表格、形容词或模板命中。找不到合格 lead 就报告竞争力不足，不编造。
- Task 2.5 只能选择、编排或重开 Gate：Role/Need/Criterion/decision_paths/EvidenceLink 与 narrative/Big Idea/decision_map 只读，不得新建/改写 VP 核心语义，不得 resolved/assumed Gate，不得新增/改变 authority，不得升 committed/confirmed；已有授权对象的 proposition/scope/Metric/resource/Acceptance 等边界不可扩大。
- Big Idea 是 selected VP 的记忆与叙事伞，不替代原子 VP，也不能掩盖各自短板。

## 5. Claim、Metric 与承诺

Claim 使用三轴：

- content_kind：fact / insight / proposal / target
- epistemic_status：evidenced / inferred / assumed
- commitment_level：none / intended / committed

规则：

- fact 有直接、有效 Evidence；高风险资质/业绩/资源/价格还需可核验材料与投标人确认。
- insight 有 Evidence、推理理由和置信度；存在重要反证时不可 publishable。
- intended proposal 有执行机制与基本可行性；committed proposal 另需 Owner、资源、排期、scope、Acceptance 和 authority。
- target 有基线、测算、影响因素和 MetricContract。无可靠基线只写方向/区间；行业基准不能直接变成本项目保证值。
- committed authority 只能来自明确授权该对象/用途的标书 Requirement、verified Evidence 或 resolved `GATE-*`；authority_ref 必须真实解析且 scope 覆盖目标，任意字符串或无关条款无效。新增资源、免费增值、排他能力、关键 KPI、SLA 和 outcome guarantee 必须人工确认。
- `-auto` 不把 assumed/new capability 升 committed；assumed 默认不进正文，并阻断 submission-ready。
- Task 3 可自然改写表层表达，但不能加强/缩小/扩大核心命题、scope 或承诺；需要变化时提交 claim_change_proposal。
- 摘要只复用正文 valid realization，不新增或加强。

MetricContract 至少有：名称/定义、公式或统计对象、单位、窗口、基线值/日期/来源、目标、数据源、频率、责任方、验收/容差。无可靠基线时不得制造伪精确点目标。

## 6. Delivery、责任、资源与验收

- 只建模直接响应 Requirement、实现 selected VP/Claim、消耗需核验资源或需独立 Owner/依赖/验收的 Action；不扩成日常项目管理系统。
- Action 三轴：selection_status、readiness_status、commitment_level。Claim 承诺强度不得高于引用 Action。
- selected Action 恰有一个投标人 accountable DeliveryRole；required/committed 至少一个 responsible。CustomerRole 只能 approver/consulted/informed/dependency，不能承担我方责任。
- required/committed Action 必须有 time_window 和 bounded resource treatment；有预算上限时每个 selected Action 都须预算 demand 或获授权的 cost_not_applicable，不能只挂一个组合总价漏掉其他 Action。
- CustomerDependency 写所需输入、时点、延误影响、安全 fallback、升级路径和依据；不能成为免责或责任转嫁。
- AcceptanceContract 写对象、标准、方法、阈值/容差、周期、审核角色、记录、纠正窗口与 authority。若 authority 来自标书 Requirement，该 Requirement 必须以 `authority_uses` 和 `authorizes_refs` 显式授权此 AC 的精确对象/用途；仅有相近条款或 `acceptance_text` 不自动获得 scope。定性创意用 rubric/样稿确认，不虚构罚则或保证下限。
- ResourceEnvelope 和 demand 用同单位、同窗口 low/high 区间并按同期聚合：`demand_low > capacity_high` blocker；区间相交 needs_review；unknown 允许 intended 草案但 committed 不通过。Action predecessor 无环，excluded_scope 不得与 Requirement 冲突。
- safe draft 不为 unknown capacity、预算或工作量补造 provisional low/high。未确认时保持 `draft_ready` Claim、`intended/planned` Action、unknown Resource 和明确 truth boundary；assumed 始终阻断 submission，相关 scope 必要时收窄或转 reserve。
- 单项可行但组合超载只报一个 portfolio 根因，不按每条路径刷屏。

## 7. DecisionJob、叙事与正文

- 评分与 mandatory 决定章节骨架；DecisionJob 内嵌 Section，每个正式章节一个 primary、最多一个 secondary。Job 必须有 Role、Criterion、expected judgment、selected VP/Claim 和 transition。
- job_kind 可复用 understand / believe / value / deliver / safe / choose，但不把六类通用文案复制进正文，也不要求一阶段一章。
- 同一 VP/Claim 跨章时分别承担 introduce/prove/operationalize/measure/price/derisk 等增量；无增量重复为 redundant。
- narrative 有 presentation authority，没有 semantic authority。它可改变开篇、材料顺序、场景、温度和节奏；不得改变 Requirement、DecisionJob、VP/Claim、Evidence、Metric、Action 或 authority。报价/合规/资质固定 logic/evidence。
- 每章以客户任务/结果开篇，标题含主张，创意配动作/责任/资源/时点/验收；不以我司自夸开篇。
- 每个 lead VP 至少有一个 required `visible_output`：只定义评委要检查的目的、支持对象、必填字段、grounding 和 truth boundary，不规定版式。grounding 安全投影须含有填实必需内容，仅有风险边界摘要不足以冻结；writer 必须在正文自然填实，外部附件不能替代。
- 严格底层不进入客户稿：禁止 Role/Need/DecisionJob/Claim/Evidence ID、覆盖状态、customer-fit、状态机、RACI 机械标签和审计过程。用自然段、集中表格和顺滑过渡保护阅读体验。

### 递交稿禁项

- URL/书目、叙事策略/模式/版本/生成时间/阅读时间/内部权重、工具或模型痕迹。
- canonical ID、private 原句、未确认个人偏好和内部竞争情报。
- 销售 CTA、期待沟通/签约、分档 opt-in 报价、“排除项/不包含”。
- intended 偷写成确保/保证，无限责任，未授权 KPI/SLA/赔偿/免费资源。
- LaTeX；货币 `$` 未转义；章/子节编号混层；占位符被当成最终事实。

## 8. Context、snapshot 与 realization

- Task 只读 compile-context 生成的最小 brief；must_use 的 Requirement 原文、Claim 语义/scope/承诺、visible output、visibility 和硬边界不可裁剪。Task 2.5 还必须收到其有权完整 upsert/校验的 Claim、Metric、交付、Gate 与 Section 对象。token 超限应拆任务或显式提高预算，不能静默删约束。
- section/summary/redteam 只看到字段白名单后的 public/tender/authorized/approved anonymized 投影；Role 权力链、private Need/Criterion、内部 Resource capacity/底价、raw authority 不发送给 writer，private 只编译成禁止越界的约束。
- Task 2.5 与必要 Gate 后冻结 generation snapshot；并行章节必须同一 snapshot。当前 snapshot 绑定五份 canonical，任一 canonical 变化后全部 snapshot-bound brief/realization/summary stale 并拒绝，不能冒充局部 current。
- writer 只写 Markdown。独立 auditor 直接为 Claim/Action 给 contribution + exact quote，为 Requirement 判 addressed/partial/missing/contradicted，为 visible output 判 filled/partial/missing/contradicted，并扫描 unexpected Claim；工具核验 brief path/hash/snapshot、正文唯一 quote、Evidence scope 和 commitment 后生成 authoritative manifest。`--hints` 只兼容旧运行。
- section hash、brief hash、snapshot 或 canonical dependency 变化后 realization stale；stale/invalid 不得进摘要或最终装配。
- 模糊 model-only 语义意见不能独立升级 blocker；需确定性规则、明确 canonical-vs-text 冲突、独立复核或 Gate 确认。法律/真实性/mandatory 疑点仍保守处理。

## 9. Diagnostics 与 customer-fit

根因分类：uncovered、orphan、unsupported、unowned、unmeasured、overcommitted、contradictory、redundant。严重度随生命周期、requiredness 和影响变化；blocks 与 severity 分开。同一根因聚合 affected paths，修复回最近 canonical owner。

submission customer-fit 固定评价十个问题：need_alignment、role_decision_coverage、insight_credibility、value_strength、differentiation、evidence_quality、delivery_readiness、commitment_safety、reading_efficiency、consistency。各维表现只用 deficient/fragile/adequate/strong/distinctive/not_evaluated；overall 只用 withheld/fragile/credible/competitive/strong，不输出伪精确分数、权重或区间。

- 任一硬 gate 失败：overall withheld。
- critical dimension fragile：总体不得称 competitive/strong。
- `not_evaluated` 不得进入 competitive/strong；strong 还要求关键维度稳定且 differentiation 有明确独立判断。
- fit rating 是内部 ordinal judgment，不是评委分或中标概率；资料少扩大不确定性，不自动等于差。
- scorecard 规定修复目标，不规定唯一创意解；只比较同一标、同一规则版本的修订，不做跨标排名。

## 10. Gate 与交付

- Gate 1/2 始终一次一题并给推荐与得失；事实不问人。quick 用 integrated 红队减少调用，但若要 submission-ready 仍需 Gate 2 attestation；auto 不交互但 assumed 留痕、入待办并阻断 direct submission。
- 红队只提 root diagnostic，不改稿；相同根因合并，无最低条数。hard fatal 立即修，其余交 Gate 2。
- resolved 只能在修复后复验通过产生；false positive dismissal 记录理由/依据/处理人/规则版本；accepted risk 仅限非硬门 major/minor/expected，仍保留 fit 影响。mandatory、法律、真实性、预算、授权与 publishable path 无效不可 waive。
- 最终卷册先 staging 后原子切换，上一份成功结果进入 `.last-good`。状态归档成功后才清 TMPDIR；allow-draft 不接受 schema/source/fatal 损坏。`finalize-run` 聚合 compliance、QA、canonical、fit、todo、Gate 2 与 archive，并签发绑定 state/report hash 的 receipt；archive 的 `canonical_submission_ready` 不冒充报告级 readiness。
- `_内部研判.md`、`_人工待办.md`、`_state/` 与 `_state.last-good` 绝不递交。

---
```
proposal skill · 3.1.2 · lean policy
```
