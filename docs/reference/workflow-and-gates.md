# v3 流程与硬门参考

v3 是默认引擎。无引擎标志和 `-v3` 都进入本流程；只有显式 `-legacy` 才加载旧链。一个 run 内不得混用两套状态、章节或 Gate 结果。

## 完整阶段

| 阶段 | 主要输入 | 主要产物 | canonical 写权限 | 通过条件 |
|:---|:---|:---|:---|:---|
| 摄入 | 标书、素材、`[notes]`、casebase | source manifest、临时 run | 主 agent | 必须有标书；来源可追溯 |
| Task 1 | 标书与规则、标型先验 | `task1.bootstrap.json`、五域初态 | 通过 bootstrap / 主 agent | draft schema、引用和策略结构有效 |
| Gate 1 | 只有投标人能决定的边界 | gate1 ChangeSet | `gate1` / 主 agent | open、blocked、fog 清零；答案同步真实对象 |
| Task 2 | research brief、公开源、案例 proof task | Evidence、EvidenceLink、gap、反证 | `task2` 仅 Evidence 与 link | public 原文有 URL；用途、scope、强度可校验 |
| Task 2.5 | value-selection brief | lead/supporting/reserve、Claim、Action、DecisionJob | `task2.5` 的窄权限 | 不自批 Gate、不扩 authority 或已授权语义 |
| generation checkpoint | 五份 canonical | diagnostics、fit strategy、snapshot | 工具派生 | generation gate 通过 |
| Task 3 | 每章 compiled brief、同一 snapshot | `section-N.md`、writer hints | 无 canonical 权限 | 文件齐全、snapshot 一致 |
| 独立兑现审计 | 当前正文、brief、hints、semantic audit | authoritative realization | 只写 derived | Requirement addressed；Claim/Action entailed |
| Task 3.5 | 全部正式章 valid whitelist | `section-0.md` 与 realization | 无 canonical 权限 | 综述只复用已兑现内容 |
| Task 4 | 装配稿、canonical、realization | report、compliance、QA、fit | 无 canonical 权限 | 客户稿硬检通过 |
| 四视角红队 | 最小 redteam brief、全文 | root diagnostics | 无 canonical 权限 | 相同根因合并，不直接改稿 |
| Gate 2 | 非自动修复的红队根因 | 取舍记录或 gate2 ChangeSet | `gate2` / 主 agent | 根因逐项处理并复验 |
| 最终归档 | 当前 report 和 state | 待办、内部研判、`_state/` | 工具归档 | 同一 report 完成最终全套验收 |

## 三个 canonical 检查阶段

| stage | 失败条件 | 用途 |
|:---|:---|:---|
| `draft` | 任一 `fatal` | 确认状态结构、schema、来源和引用未损坏 |
| `generation` | `fatal`，或 `blocks` 含 `compile` / `task3` | 决定是否允许冻结快照和写章节 |
| `submission` | 任一 `fatal` 或 `blocker` | 决定 canonical 与 realization 是否达到递交硬门 |

`check-canonical --stage submission` 的 `submission_ready=true` 只表示这次 canonical/realization 检查通过。整份报告仍需同一版本的 compliance、QA、customer-fit 和 Gate 2，详见[输出与就绪状态](outputs-and-readiness.md)。

## Gate 1

Gate 1 只处理 AI 无法从标书、材料或公开来源查明的真实决策：

- 投标人能力与团队可用性；
- 资源容量和预算取舍；
- 新增成本、免费增值和排他能力；
- 关键 KPI、SLA、结果保证与验收边界；
- 案例名称、Logo、评价、金额和数字发布授权；
- 未公开履约关系、内部偏好和其他 private 边界。

标书事实不问人；公开缺口交 Task 2；尚不能精确提问的事项先留在 `not_yet_specified`。每轮只问当前前沿的一题，给出推荐和得失。用户只有明确说“其余按推荐”时，才可批量处理。

一个 Gate 回答必须在同一 ChangeSet 内同时：

- 更新 decision 的完整状态与原意；
- 更新受影响的 VP、Claim、Action、Resource、Acceptance 和 strategy；
- 保留原 visibility；private 回答只能形成脱敏约束；
- 降级或撤回被否定、未确认的能力与承诺。

只把 `decision.status` 改为 resolved 不算完整解决。

## Task 2.5 权限边界

Task 2.5 可以选择、组合、编排或要求重开 Gate，但不能：

- 改写 Role、Need、Criterion、EvidenceLink 或 narrative / Big Idea / decision map；
- 新建或改写 ValueProposition 核心语义；
- 把 Gate 标为 resolved / assumed；
- 新增或改变 authority；
- 把 Claim / Action 升为 committed / confirmed；
- 扩大已授权的 proposition、scope、Metric、资源或验收边界。

选择以窄硬门、关键短板、Pareto 和组合充分性为准，不按亮点数量、表格或篇幅评分。

## Snapshot 与写作

Task 2.5 和必要 Gate 完成后才能冻结 generation snapshot。section、exec-summary 和 redteam brief 都绑定该 snapshot。当前实现把五份 canonical 作为整体依赖：任一份发生变化，所有 snapshot-bound brief、章节、摘要和 realization 都必须重编译与复验。

Task 3 writer 只读取 compiled brief，不读取完整 canonical。Task 3、Task 3.5 和红队都没有 canonical 写权限；它们只能报告 observation、diagnostic 或 change proposal。

## Gate 2

四个红队视角固定为：

- `buyer`：是否真的解决业务问题、是否省心、是否有人负责；
- `expert`：逻辑、方法、数据、案例可比性和可落地性；
- `audit`：mandatory、真实性、预算、政务导向和审计风险；
- `rival`：差异化是否可复制、承诺和资源的最弱环。

明确硬门的 fatal 先按 owner 修复。其余聚合根因在 Gate 2 一次处理一条，处置为“采纳修改 / 保留并补证据 / 不采纳”。不采纳必须有依据；mandatory、法律、真实性、预算、授权和无效 publishable path 不可 accepted risk。

## 模式对关卡的影响

| 模式 | Gate 行为 |
|:---|:---|
| standard / deep | 停 Gate 1 和 Gate 2 |
| quick | 只停 Gate 1；后续硬检和红队仍执行 |
| `-auto` | 不交互；保守 assumed 留痕并阻断直接递交 |

## 最终顺序

最终必须基于最新一次装配重新绑定 `$REPORT`、`$BUNDLE` 和内部文件路径，然后依次复跑 compliance、QA、canonical submission 和 customer-fit，生成待办与内部研判，最后归档 state。状态归档成功后才可清理临时目录。
