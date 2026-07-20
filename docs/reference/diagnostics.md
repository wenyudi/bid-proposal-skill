# 诊断参考

`check-canonical --write-derived` 会把结构化结果写入 `STATE/derived/diagnostics.json`。诊断用于把问题路由回最近的事实 owner，不是让下游正文绕过根因。

## Diagnostic 对象

| 字段 | 含义 |
|:---|:---|
| `rule_id` | 稳定规则名，例如 `claim.evidence_quality` |
| `kind` | 根因类别 |
| `severity` | `fatal`、`blocker`、`major`、`minor` 或 `info` |
| `blocks` | 被阻断的阶段，如 `compile`、`task3`、`submission` |
| `subject_refs` | 直接受影响的 canonical ID |
| `root_cause_key` | `rule_id` 与排序后 refs 组成的聚合键 |
| `observed` | 当前检测到的事实 |
| `expected` | 通过规则所需状态 |
| `confidence` | 诊断置信度，默认 high |
| `owner` | 应负责修复的 Task、Gate 或文件 owner |
| `repair_options` | 建议修复动作；可能为空 |
| `secondary_tags` | 便于归组的辅助标签，不改变严重度 |

相同 `root_cause_key` 应合并处理，不按每条路径重复制造红队问题。

## 严重度

| 严重度 | 含义 | 典型处理 |
|:---|:---|:---|
| `fatal` | 状态本身不可安全解释，如 schema、manifest、来源或引用损坏 | 立即停止编译，修状态或新建 run |
| `blocker` | 事实可读，但不满足当前硬门 | 回 owner 修复；submission 不可豁免 |
| `major` | 重要短板或不确定性，当前规则未把它设为硬阻断 | 纳入短板、红队或 Gate 2；保留 fit 影响 |
| `minor` | 局部改进项 | 在不引入新风险时修复 |
| `info` | 说明性信号 | 用于追踪，不单独阻断 |

`blocks` 与 severity 分开。例如某个 blocker 可明确阻断 `task3` 和 `submission`；major 可能没有 `blocks`，但仍应处理。

## stage 判定

| `check-canonical` stage | 使 `passed=false` 的诊断 |
|:---|:---|
| `draft` | severity 为 `fatal` |
| `generation` | `fatal`，或 `blocks` 包含 `compile` / `task3` |
| `submission` | `fatal` 或 `blocker` |

因此 draft 通过不表示能写作，generation 通过也不表示能递交。

## 根因 kind

| kind | 问题类型 |
|:---|:---|
| `schema` | 文件、字段、manifest、版本或对象形状无效 |
| `uncovered` | Requirement 或客户价值路径没有下游覆盖/兑现 |
| `orphan` | 对象缺少必要上游或下游连接 |
| `unsupported` | Evidence、授权、投影或验收依据不足 |
| `unowned` | 动作或承诺没有有效责任角色 |
| `unmeasured` | Metric、资源、预算、时点或验收边界不完整 |
| `overcommitted` | 承诺强于证据、authority、Action 或容量 |
| `contradictory` | 引用、状态、scope、资源窗口或正文互相矛盾 |
| `redundant` | 无增量重复、过多 secondary job 等结构浪费 |

## 常见 rule family

| 前缀 | 检查范围 | 常见 owner |
|:---|:---|:---|
| `state.*`、`schema.*`、`ref.*`、`manifest.*` | 五文件、版本、全局 ID、source/run manifest | `main` 或对应文件 |
| `decision.*` | Gate ID、状态、open、fog、assumed | `gate1` |
| `strategy.*` | 一页纸完整性、互换测试、rubric、批准与 Section spine | `task2.5` / `human` |
| `need.*`、`vp.*`、`portfolio.*` | 客户结果、价值路径、lead 选择 | `task1` / `task2.5` |
| `evidence.*`、`claim.evidence*` | 用途、第三方边界、匿名投影、证据质量 | `task2` |
| `claim.*`、`metric.*` | Claim 三轴、scope、测量、authority、Action 强度 | `task2.5` / `gate1` |
| `action.*`、`acceptance.*`、`dependency.*` | 责任、ready、资源 treatment、验收和客户依赖 | `task2.5` / `gate1` |
| `resource.*`、`budget.*`、`delivery.*` | 单位、窗口、容量、组合负载、预算上限、先后关系 | `gate1` / `task1` |
| `job.*`、`section.*`、`coverage.*`、`decision_path.*` | 内嵌 DecisionJob、章节映射、Role×Need×Criterion 路径 | `task1` / `task2.5` |
| `visible_output.*` | lead 成果契约缺失、字段未填或 truth boundary 冲突 | `task2.5` / `task3` |
| `realization.*` | brief lineage、snapshot、正文 hash、语义状态、摘要 | `task3` / `task3.5` |

具体修复以诊断对象的 `owner`、`observed`、`expected` 和 `repair_options` 为准；同一前缀的不同规则可能回到不同 owner。

红队另用 `failure_class` 做质量归因：`strategy_hollow`、`throughline_break`、`cliche_style` 或 `none`。它不是新的 canonical kind；一次质疑只选一个主失败，用于决定回 Task 2.5/Section spine 还是 Task 3 表达层。

`acceptance.authority_scope` 是 bootstrap/draft 的前置完整性门：AcceptanceContract 一旦填写 `authority_ref`，该 authority 必须已经对 AC 的精确对象与 `commitment_authority` 用途具备 scope。若标书 Requirement 确实规定了该交付/验收，由 Task 1 在 Requirement 上补齐 `authority_uses` 与 `authorizes_refs`；若没有，就清空伪 authority 并将新增边界交给 Gate，不能等 Task 2.5 通过舍弃交付路径来绕过。

## QA checks

`qa-proposal` 返回独立的 `checks`，不使用上面的 Diagnostic schema：

| check | 类型 | 内容 |
|:---|:---|:---|
| `encoding` | 硬项 | 文件编码 |
| `structure` | 硬项 | 标题、项目信息、目录和对照表 |
| `heading_hierarchy` | 硬项 | 章为 H2，子节为 H3 `N.x`，子子节为 H4 `(x)`；章内不得出现同级 H2 |
| `no_internal_leak` | 硬项 | 叙事、模式、版本、时间、URL、内部模型词 |
| `no_private_raw_leak` | 硬项 | private/internal/匿名前 canonical 原句 |
| `chapter_count` | 硬项 | v3 必须精确等于 `strategy.sections`；profile 最低章数仅 legacy |
| `subsection_numbering` | 硬项 | 子节编号不使用汉字章编号 |
| `no_id_leak` | 硬项 | legacy 与 v3 内部实体 ID |
| `word_count` | 信息 | 当前字数和 profile limit；超限记录在 `exceeded` |
| `differentiators` | v3 deprecated warning | v3 不检查固定亮点数量 |
| `scope_guard` | warning | out-of-scope 禁用词与待语义复核项 |
| `no_latex` | warning | 未转义 `$` 数字模式 |
| `exec_summary` | warning | 是否有方案综述 |
| `buyer_focus` | warning | 中文稿甲方/我方提及启发式比例 |
| `no_sales_cta` | warning | CTA、“排除项/不包含”等措辞 |

`qa-proposal.passed` 只由 `warning` 不为 true 的失败项决定。warning 不等于可忽略；它应进入人工复核或红队，但不会冒充 canonical blocker。

## customer-fit 与诊断的关系

customer-fit 固定十维：need alignment、role decision coverage、insight credibility、value strength、differentiation、evidence quality、delivery readiness、commitment safety、reading efficiency、consistency。

overall 只用 withheld / fragile / credible / competitive / strong；不输出数字权重或区间，任一 `not_evaluated` 都不能进入 competitive/strong。

只要 checkpoint 对应的 hard gate 有失败，overall 就是 `withheld`。ordinal rating 不是评委分或中标概率，也不能抵消任何 diagnostic hard gate。

## 查看与处理

```bash
python3 tools/prop_tools.py check-canonical --state-dir "$STATE" \
  --stage generation --write-derived
python3 tools/prop_tools.py json-get "$STATE/derived/diagnostics.json" diagnostics
```

处理步骤见[解除失败、stale 和 blocker](../how-to/resolve-blockers.md)。
