# 兑现审计与快照

canonical 里有正确的 Requirement、Claim 和 Action，并不代表最终文字真的表达了它们。writer 可能漏写、改弱、改强、扩大 scope，也可能在方案综述中加入正文没有的新承诺。realization 用来验证“事实模型是否在当前文本中得到准确兑现”。

## 为什么需要 compiled context

直接把五份 canonical 全量交给每个 writer，会产生三个问题：

- private、底价、内部权力链和无关 Evidence 暴露给不需要它们的 agent；
- 上下文过大，关键 Requirement 和承诺边界容易被稀释；
- 不同章节可能从不同版本状态写作。

`compile-context` 因此按 target 生成最小 brief：

- `must_use`：本任务不能裁剪的 Requirement、Claim 语义、scope、承诺和边界；
- `may_use`：相关但可在 token 紧张时移除的材料；
- `forbidden`：private、越界表达和不可使用内容；
- expected refs：本章必须兑现或评估的对象。

如果 `must_use` 仍超过 token budget，brief 会 blocked。系统不会为了塞进上下文而静默删硬要求。

## Generation snapshot

generation gate 通过后，`freeze-snapshot` 对五份 canonical 的 revision 和内容 hash 生成 `GS-*` 快照。section、exec-summary 和 redteam brief 都记录同一个 snapshot ID。

当前 v3 采用全局失效策略：任一 canonical 发生变化，所有 snapshot-bound artifact 都视为 stale。它比依赖级局部重编译更昂贵，但在实际依赖图尚未充分验证时更安全，能避免“只改了一个 Claim，却漏掉另一个章节中的强化表达”。

简单修改 Markdown 标点不会改变 canonical，但正文 hash 改变后，对应 realization 仍需复审。

## Writer hints 不是审计结论

writer 在交付章节时同时给出 `realization-hints/v1`，标明：

- 它认为兑现了哪个 canonical ref；
- 本章贡献是 introduce、prove、operationalize、measure、price、derisk 等哪一种；
- 对应 heading 和 exact quote。

这些 hints 只帮助定位，不能自证通过。否则 writer 可以用自己写的标签证明自己的文字正确。

## 独立 semantic audit

未参与该章写作的 auditor 读取当前正文和同一 brief，产生 `semantic-realization/v1`：

对 Requirement 判断：

- `addressed`；
- `partial`；
- `missing`；
- `contradicted`。

对 Claim / Action 判断：

- `entailed`；
- `partial`；
- `contradicted`；
- `overstated`；
- `not_found`。

auditor 还扫描 unexpected Claim，并给出正文 quote、reason 和 confidence。工具随后核对 brief lineage、snapshot、hash、expected refs、证据 scope 和 metadata，才写 authoritative `realization/v1` manifest。

没有 independent semantic 文件时，状态只能是 `needs_semantic_review`；有缺项、夸大、意外主张、stale 或 Requirement 未 addressed 时是 `invalid`；全部通过才是 `valid`。

## 为什么摘要最后写

方案综述最容易为了有冲击力而比正文说得更大。v3 在全部正式章节 valid 后，才编译 exec-summary brief；它的白名单来自正式章 authoritative realization。

摘要可以压缩、重组和改善表达，不能：

- 新增 Claim、数字、案例或承诺；
- 把 intended 改成保证；
- 扩大 scope；
- 使用未在正式章有效呈现的 Evidence。

`section-0.md` 本身也要由独立 auditor 复验。submission gate 要求正式章和摘要都拥有当前 snapshot、当前正文 hash 的 valid authoritative manifest。

## Artifact registry 防止“手改通过”

compiled brief 和 authoritative realization 都注册在 `derived/manifests/artifacts.json`，记录绝对路径、输出 hash、依赖文件、snapshot 和 policy version。

submission 会检查：

- manifest 是否由 `audit-realization` 注册；
- authoritative 文件与 registry hash 是否一致；
- brief 是否位于本 run 的 registry 中；
- brief、snapshot、section text 是否漂移；
- 是否每章只有一个 authoritative manifest。

把 `.proposed.json` 或 `.semantic.json` 改名、手改 status，不能冒充工具生成的 authoritative realization。

## 变更后的重编译范围

| 变更 | 必须重做 |
|:---|:---|
| canonical 任一文件 | generation gate、snapshot-bound briefs、全部正式章审计、摘要、装配与最终检查 |
| 某章正文但 canonical 未变 | 该章 realization；若摘要引用其内容，再重编译/复审摘要 |
| 方案综述正文 | 综述 realization |
| report 装配路径或内容 | compliance、QA、customer-fit 与最终路径绑定 |

恢复 `_state/` 到新目录时，旧 artifact 和 realization 的绝对路径也不跨目录有效；必须在新目录重新编译和审计。

## 它保证什么，不保证什么

realization 能证明当前正文在当前快照下实质回答了预期 Requirement，并没有把预期 Claim / Action 明显改写或夸大。它不证明客户一定认可创意，也不替代真实资质、报价审批、法律审核或最终人工校对。

这正是 customer-fit、红队、Gate 2 和人工签字仍然存在的原因：兑现审计守住语义一致性，其他环节分别处理竞争力、对手质疑和真实授权。
