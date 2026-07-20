# 命令行参考

所有命令从仓库根目录调用：

```bash
python3 tools/prop_tools.py <command> [arguments]
```

本页描述底层工具接口。日常使用通常只需在宿主会话中调用 `/proposal`；CLI 主要由 skill 调度、恢复流程和维护者使用。

## v3 状态命令

### `init-state`

```text
init-state --state-dir DIR [--mode quick|standard|deep] [--lang LANG]
```

在不存在 canonical 的目录中创建空 v3 状态、目录布局、source manifest 和 run manifest。已有任一 canonical 时拒绝覆盖。Task 1 正常流程通常使用 `bootstrap-state`，而不是手工填充空状态。

### `scaffold-bootstrap`

```text
scaffold-bootstrap --output-dir DIR
                   [--mode quick|standard|deep] [--lang LANG]
```

在 `DIR/task1.components/` 生成五份确定性 canonical 空骨架，并写 `DIR/task1.bootstrap.json` 索引。Task 1 直接填充这些文件，不再手写整套 schema。任一目标已存在时拒绝覆盖；安装中途失败会回滚本轮 scaffold。

### `bootstrap-state`

```text
bootstrap-state --state-dir DIR --proposal FILE
                [--mode quick|standard|deep] [--lang LANG]
```

从 Task 1 的 bootstrap proposal 原子建立五份 canonical。v2 proposal 用 `canonical_files` 引用索引同目录内的五个相对 JSON 组件，便于同一 Task 1 agent 逐份落盘和校验；绝对路径、越出 proposal 目录或重用组件路径都会拒绝。工具仍可读只含内联 `canonical` 的 v1 历史 proposal。两种形式都要读齐五域、通过整体 draft 校验后才一次安装，不会产生部分 canonical。

### `migrate-state`

```text
migrate-state --source-dir DIR --output-dir DIR
              [--mode quick|standard|deep] [--lang LANG]
```

把 legacy 状态保守迁移到新的 v3 目录。源目录不修改；目标已存在 canonical 时拒绝覆盖。输出包括 `legacy-to-v3-map.json`。

### `check-canonical`

```text
check-canonical --state-dir DIR
                [--stage draft|generation|submission]
                [--realization-dir DIR] [--write-derived]
```

校验 schema、manifest、引用、生命周期、客户价值路径、交付、资源、预算和阶段硬门。

- 默认 `--stage draft`。
- submission 未指定 `--realization-dir` 时，默认使用 `STATE/derived/realization`。
- `--write-derived` 写入 `derived/coverage.json` 和 `derived/diagnostics.json`。
- JSON 结果包含 `passed`、`issues`、`diagnostics`、`counts`、`coverage`、`safe_draft_ready`、`submission_ready`、`readiness` 和 `state_hash`。

### `apply-changeset`

```text
apply-changeset --state-dir DIR --changeset FILE
```

应用 `changeset/v1`。工具先检查 producer 权限和 touched files 的 base revision，在临时目录验证完整候选状态，再原子替换 canonical。stale 或任何校验失败都会拒绝整组操作；成功时写 change receipt，并删除可复用 snapshot/final receipt。旧 brief/realization 由自身 hash 自动判 stale。

支持的 operation 是 JSON Pointer `add`、`replace`、`remove`、`test`，以及实体级 `transition`、`upsert`。

### `promote-research`

```text
promote-research --state-dir DIR
                 --intel-proposal FILE --links-proposal FILE
```

校验并提升 Task 2 产物。intel proposal 必须是 `research-evidence/v1`，links proposal 必须是 `research-links/v1`。通过后以 Task 2 ChangeSet 添加 Evidence、EvidenceLink、gap 和 contradiction；有 Evidence refs 的 `strategy_signals` 与 `reopen_required` 会写入 research manifest，供 Task 2.5 判断是否重新打开 VP 候选。

### `apply-auto-state`

```text
apply-auto-state --state-dir DIR
```

把 v3 的 open 决策转为可追溯 `assumed`。Task 2.5 后再次运行时，也会把 ready-for-review 且 pending 的一页纸策略写成 `assumed`，只解锁安全草案；明确 `changes_requested` 不会被自动覆盖。运行前 `not_yet_specified` 必须已经归位；依赖 Gate 的 committed、confirmed 或发布授权会被同步降级。

### `freeze-snapshot`

```text
freeze-snapshot --state-dir DIR [--force]
```

在 generation gate 通过后冻结五份 canonical 及 source/run 的 revision/hash，写入 `derived/manifests/generation-snapshot.json`。相同 authority fingerprint 默认复用已有快照；`--force` 重新写入。

### `compile-context`

```text
compile-context --state-dir DIR
                --target research|value-selection|strategy-review|section|exec-summary|presentation|redteam
                [--id ID] [--role ROLE] [--output FILE]
                [--token-budget N]
```

为指定 Task 编译最小 context brief。

| target | 额外参数 | 默认输出 |
|:---|:---|:---|
| `research` | 无 | `derived/briefs/research.json` |
| `value-selection` | 无 | `derived/briefs/value-selection.json` |
| `strategy-review` | 无；非 snapshot-bound | `derived/briefs/strategy-review.json` |
| `section` | 必须 `--id CH-*` | `derived/briefs/sections/<section-ref>.json` |
| `exec-summary` | 无 | `derived/briefs/exec-summary.json` |
| `presentation` | 无；要求正式章节 realization valid | `derived/briefs/presentation.json` |
| `redteam` | 必须 `--role`；profile 可取 integrated / strategy_critic / audit_rival / buyer / audit / rival | `derived/briefs/redteam/<role>.json` |

`--token-budget` 的 CLI 默认值为 24000。proposal 主流程对 `value-selection` 显式使用当前模式 `v3_context_token_budget` 的 1.5 倍（quick / standard / deep 为 24000 / 36000 / 54000），因为 Task 2.5 必须接收可完整 upsert 和交叉校验的 canonical 对象；超限时仍 fail-closed，不会静默删 must_use。

默认 token budget 是 `24000`。超限时只允许裁掉 `may_use`；`must_use` 仍超限则 brief 状态为 `blocked`，需要拆任务或显式提高预算。

section / exec-summary / presentation / redteam 属于 snapshot-bound brief；即使指定 `--output`，路径也必须位于本 run 的 `STATE/derived/briefs/` 下，避免跨 run lineage 混用。

### `audit-realization`

```text
audit-realization --state-dir DIR --section-ref ID
                  --section FILE --brief FILE
                  [--hints FILE]
                  [--semantic FILE] [--output FILE]
```

核验当前章节、compiled brief 和独立 semantic audit 的 path/hash/snapshot lineage、唯一正文 quote、Evidence scope、承诺强度、Requirement 与 visible output 字段。新流程不需要 writer hints；`--hints` 只兼容 v3.0。未提供 `--semantic` 时会产出 `needs_semantic_review`，不会通过。默认 authoritative manifest 写入 `derived/realization/<section-ref>.json`。

### `customer-fit`

```text
customer-fit --state-dir DIR
             [--checkpoint strategy|submission]
             [--judgments FILE] [--realization-dir DIR]
             [--output FILE]
```

生成十维客户适配度内部诊断。默认 checkpoint 是 `strategy`；submission 会检查 realization。可选 judgments 必须为各维度提供有效 level、reason 和 source refs，否则使用确定性锚点或标为 `not_evaluated`。filled visible output 证明成果完整，不推断 reading efficiency；阅读判断需要 report-anchored semantic judgment。overall 只输出 withheld / fragile / credible / competitive / strong；不输出数字分、权重或区间。

### `validate-presentation`

```text
validate-presentation --state-dir DIR --brief FILE --blueprint FILE
                      [--output-dir DIR]
```

校验 `presentation-blueprint/v1` 的 snapshot/brief lineage、页序、story arc、required refs、唯一 signature/sample 页、上屏文案、视觉任务、素材路径和 truth boundary。通过后写 `deck-blueprint.json`、确定性 `outline.md` 与 `presentation-validation.json`；状态为 `ready_for_outline_review`，不生成图片或 PPTX。完整字段见 [Presentation blueprint 参考](presentation-blueprint.md)。

### `archive-state`

```text
archive-state --state-dir DIR --bundle-dir DIR [--allow-draft]
```

把 canonical、manifests、realization、sections、state 内 presentation 生产包和关键 derived 结果原子归档到 bundle 的 `_state/`。默认要求 canonical submission gate 通过。`--allow-draft` 可归档结构完好的草案，但不能绕过 schema、source 或 fatal 损坏。

### `validate-run`

```text
validate-run --state-dir DIR --report FILE
             [--mode quick|standard|deep] [--lang LANG]
             [--judgments FILE] [--gate2 FILE]
             [--todo-output FILE] [--validation-output FILE]
```

报告级只读终验。未显式提供 `--judgments` 时，先从 `STATE/redteam/` 选择当前 snapshot 的 strategy_critic/integrated 输出，只把能在当前 report 定位 exact quote 的 insight、differentiation 和 reading efficiency 观察编译为 judgments；再一次聚合 compliance、QA、canonical submission、customer-fit、human todo 和 Gate 2，并把结果写为 `run-validation/v1`。没有 resolved Gate 2 attestation 时 `submission_ready=false`；canonical 结果会被 fit/todo 复用，不重复校验。

### `finalize-run`

```text
finalize-run --state-dir DIR --report FILE --bundle-dir DIR
             [--mode quick|standard|deep] [--lang LANG]
             [--judgments FILE] [--gate2 FILE]
             [--todo-output FILE] [--validation-output FILE]
             [--receipt-output FILE] [--allow-draft]
```

运行 `validate-run`、复用同一 checked result 原子归档，并签发 `acceptance-receipt/v1`。receipt 绑定 `state_hash`、`report_hash` 与 validation hash；只有 `delivery_status=submission_ready` 才是报告级可递交结论。`--allow-draft` 可签发 `draft_only` receipt，但不豁免 canonical 损坏。

## 装配、合规与 QA

### `assemble-proposal`

```text
assemble-proposal --strategy FILE --requirements FILE --intel FILE
                  --sections-dir DIR
                  [--mode quick|standard|deep]
                  [--output DIR] [--lang LANG] [--auto]
```

从 `section-0.md` 和 `section-N.md` 装配时间戳卷册。默认输出基目录是 `reports`。`--auto` 只允许装配已留痕的 assumed 草案，不代表可递交。成功输出实际 report、bundle、分册和内部研判路径。

### `check-compliance`

```text
check-compliance --requirements FILE --strategy FILE --report FILE
```

检查 mandatory、scoring、deliverables 是否映射到章节，以及报告章数和应标对照表是否存在。它不替代正文 realization 语义审计。

### `qa-proposal`

```text
qa-proposal REPORT [--mode quick|standard|deep]
            [--strategy FILE] [--requirements FILE]
            [--lang LANG] [--state-dir DIR]
```

检查编码、卷册结构、章/子节层级、内部模型泄露、private raw 泄露、内部 ID、编号、篇幅、范围守卫和客户稿禁项。提供 `--state-dir` 才能扫描 canonical private 原句和完整实体 ID。

### `human-todo`

```text
human-todo --requirements FILE --strategy FILE --report FILE
           --output FILE [--mode quick|standard|deep]
           [--lang LANG] [--intel FILE] [--state-dir DIR]
```

汇总占位符、open/assumed 决策、Evidence gap、机械薄弱项和 v3 major/blocker，写 `_人工待办.md`。该命令生成清单，即使清单非空也会正常返回；清单存在不等于流程失败已被豁免。

### `escape-currency`

```text
escape-currency REPORT
```

原地转义正文中未转义、后接数字的 `$`。代码块、行内代码、链接、URL 和标签受保护。

### `self-score`

```text
self-score --requirements FILE --strategy FILE --report FILE
           [--mode quick|standard|deep]
```

保留的 legacy 机械信号。v3 不把固定差异化数量、篇幅或 estimated score 当作竞争力结论；请使用 canonical gate、realization 和 customer-fit。

## 兼容与实用命令

| 命令 | 签名 | 说明 |
|:---|:---|:---|
| `check-encoding` | `check-encoding FILE` | 检查 UTF-8 等文本编码问题 |
| `word-count` | `word-count FILE` | 输出中英文字符统计值 |
| `json-validate` | `json-validate FILE` | 检查 JSON 是否可解析 |
| `json-get` | `json-get FILE KEY_PATH` | 以点路径读取 JSON；数组段使用数字索引 |
| `check-requirements` | `check-requirements FILE` | legacy 兼容的 requirements 结构检查 |
| `check-strategy` | `check-strategy FILE [--mode ...] [--require-settled] [--auto]` | 校验 strategy 和决策前沿；`--auto` 允许 assumed |
| `apply-auto-decisions` | `apply-auto-decisions FILE` | legacy 原地转换 open 决策；v3 使用 `apply-auto-state` |
| `detect-engine` | `detect-engine` | 默认不外呼；设置 `PROPOSAL_SEARCH_PROBE_URL` 后向该用户自选地址发起探测请求，可用性仅作信息 |

## 退出码与输出

- v3 状态命令输出 JSON；`passed=true` 返回 `0`，否则返回 `1`。
- `check-encoding`、`json-validate`、`check-requirements`、`check-strategy`、`apply-auto-decisions`、`assemble-proposal`、`check-compliance`、`qa-proposal`、`validate-run` 和 `finalize-run` 失败返回 `1`。
- `word-count`、`json-get`、`detect-engine`、`escape-currency`、`self-score` 和 `human-todo` 在命令成功执行时返回 `0`；其中 `human-todo` 非空、`self-score` 偏低都只是结果，不改变退出码。
- 未捕获异常返回 `1`；键盘中断返回 `130`。

随时运行 `python3 tools/prop_tools.py <command> --help` 以核对当前参数。
