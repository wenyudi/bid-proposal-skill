# 为什么需要快照与兑现审计

canonical 正确，不代表最终文字真的表达了它。writer 可能漏写 Requirement、把 intended 写成保证、扩大 scope，或用流程名词替代客户真正想看到的成果。v3.1 用 snapshot 固定输入，用独立 realization 审计固定“当前正文究竟兑现了什么”。

## Snapshot 解决版本混用

generation gate 达到 `safe_draft_ready` 后，`freeze-snapshot` 绑定：

- 五份 canonical 的 revision 与内容 hash；
- `source-manifest.json` 与 `run-manifest.json` hash；
- 当前 policy version。

结果是一个 `GS-*`。section、exec-summary 和 redteam brief 都记录它；fingerprint 不变时，各章 `compile-context` 直接复用已通过的 snapshot，避免重复做完整 generation 校验。

当前仍采用全局失效：任一 canonical 或 authority manifest 改变，所有 snapshot-bound brief/章节/摘要/realization 都需重编译和复验。它比局部依赖图昂贵，但在投标承诺相互影响时更安全。

正文变化不改变 canonical，却会改变 section hash，因此对应 realization 仍会 stale。

## Writer 为什么只写 Markdown

v3.0 让 writer 同时写 `realization-hints`，再让 auditor 校验。这产生两份 sidecar、重复定位和额外出错面，而且 writer 的自我定位不能替代独立证据。

v3.1 中 writer 只写客户正文。未参与写作的 auditor 直接从全文为每条预期对象给出唯一逐字 quote：

- Claim/Action：contribution、entailed/partial/contradicted/overstated/not_found、实际 scope/commitment 和 Evidence；
- Requirement：addressed/partial/missing/contradicted；
- required visible output：filled/partial/missing/contradicted，并为每个 required field 给唯一正文 quote；
- brief 外新增事实、数字、能力或承诺：unexpected claims。

一名 auditor 可按 profile 批量审 2–3 章，但每章使用自己的 brief/正文、写自己的 semantic 文件，禁止跨章借 quote 或 Evidence。

## Visible output 审计守住“合规但空”

Requirement addressed 和 Claim entailed 仍可能只得到一段正确但抽象的文字。Section 的轻量 `visible_outputs` 只规定：评委要检查什么、必须填哪些字段、依据来自哪里、什么事实不能扩大。

它不规定版式。writer 可以自然交出内容样例、分镜、节奏表、看板或应急卡；内部 OUT-* 与审计标签不进入客户稿。冻结前，grounding 的安全投影就必须保留填实必需的事实、数值和口径；只写“可用于演示”或风险边界会让 writer 无内容可写。只有所有 required fields 有项目实值、唯一 quote 且不越过 truth boundary，auditor 才能判 `filled`。外部附件不能替代正文成果。

`filled` 只证明“有可评材料”，不自动证明独特、有创意或必胜；差异化仍由 customer-fit judgment、红队和客户反馈判断。

## 工具如何形成 authoritative manifest

`audit-realization` 不信任模型自报的 `overall`。它重新核对：

1. brief 位于本 run 的 `derived/briefs`，`compiled_path` 与传入路径一致；
2. brief hash、canonical revisions/hashes 与当前 state 一致；
3. snapshot 仍匹配 source/run/canonical fingerprint；
4. semantic ref 完整、无重复，quote 在当前正文唯一存在；
5. Claim/Action scope、commitment 和 scoped Evidence 没有越权；
6. Requirement addressed，required visible output 全部 filled；
7. section hash 与当前正文一致。

全部通过才写 authoritative `realization/v1`，并为 manifest 内容生成 `attestation_hash`，任何手改都会在 submission loader 中被拒绝。brief 和 realization 自带 lineage，因此不再维护 `artifacts.json`；少一个可变 registry，也少一处“登记状态与实际文件漂移”的风险。`--hints` 仅用于恢复 v3.0 旧运行。

把 semantic 文件改名、手改 manifest status 或复制旧 path，都不能通过上述复算。

## 综述为何最后写

综述最容易比正文说得更大。只有全部正式章 valid 后，工具才编译 exec-summary brief；白名单来自正式章 authoritative realization。综述可以压缩和重组已兑现内容，不能创造新 Claim、数字、案例、visible output 或强化承诺，并且仍需独立 audit。

## 什么变化需要重做什么

| 变化 | 必须重做 |
|:---|:---|
| canonical / source / run | generation gate、snapshot、全部绑定 brief/正文/audit、摘要、装配与终验 |
| 某章正文（canonical 未变） | 该章 audit；若摘要引用，再重编译/复审摘要 |
| 方案综述正文 | 综述 audit |
| report 内容或路径 | `validate-run`；归档前再 `finalize-run` |
| 恢复到新目录 | 重新 freeze/compile/audit；旧 compiled path 不跨目录有效 |

## 它不证明什么

Realization 证明当前正文在当前快照下实质回答了预期对象且没有明显越权。它不证明客户一定喜欢创意，也不替代真实资质、报价审批、法律审核或法定模板签章。

因此 customer-fit、adaptive redteam、Gate 2 和最终 state/report-bound receipt 仍然存在：分别处理竞争力、对手质疑、真实取舍和报告级验收。
