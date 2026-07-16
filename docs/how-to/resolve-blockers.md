# 解除失败、stale 和 blocker

先修根因所属的上游事实，再重新生成下游产物。不要直接编辑 `derived/`、realization manifest 或内部研判来把失败改成通过。

## 1. 重新生成当前诊断

选择与你所处阶段一致的检查：

```bash
# Task 1 / Gate 1 期间
python3 tools/prop_tools.py check-canonical --state-dir "$STATE" --stage draft --write-derived

# Task 3 写作前
python3 tools/prop_tools.py check-canonical --state-dir "$STATE" --stage generation --write-derived

# 最终装配与审计后
python3 tools/prop_tools.py check-canonical --state-dir "$STATE" --stage submission \
  --realization-dir "$STATE/derived/realization" --write-derived
```

命令会返回 JSON，并把完整诊断写入 `$STATE/derived/diagnostics.json`。优先看：

- `rule_id` 和 `root_cause_key`：是哪条规则、哪个聚合根因；
- `severity` 与 `blocks`：严重程度和阻断阶段；
- `subject_refs`：受影响对象；
- `owner`：应回到哪个 Task 或 Gate；
- `observed`、`expected`、`repair_options`：现状、目标和建议修法。

字段完整定义见[诊断参考](../reference/diagnostics.md)。

## 2. 按 owner 回到最近事实源

| owner / 现象 | 返回位置 | 常见处理 |
|:---|:---|:---|
| `main`、schema、source、dangling ref | 初始化或 Task 1 | 恢复五份 canonical、原始来源和正确引用；损坏时重建新 run |
| `task1`、Requirement、Role、Need、Section 映射 | Task 1 | 补拆标书、客户结果或章节映射 |
| `gate1`、能力、资源、预算、authority、assumed | Gate 1 | 由投标人确认、缩小范围、降级承诺或撤回 |
| `task2`、Evidence、private-only、质量不足 | Task 2 | 抓取原文、补 scoped link、保留 gap 或降低 Claim 强度 |
| `task2.5`、lead、VP、Claim、Action、DecisionJob | Task 2.5 | 重新选择组合、补完整执行链或退回候选 |
| `task3`、Requirement 未回答、正文遗漏 | 对应章节 writer | 用当前 brief 重写该章，再独立审计 |
| `task3.5`、summary 白名单或过度表述 | 方案综述 | 只复用 valid realization，删除新增主张 |
| realization stale / invalid | 独立 auditor | 重新编译 brief，对当前正文重新审计 |

canonical 变更必须由有权限的 producer 生成 ChangeSet；Task 3、摘要和红队不能直接改事实源。

## 3. 处理常见故障

### `stale changeset`

这表示 base revision 已落后。重新读取当前 canonical revision，基于当前事实重新生成整份 ChangeSet。不要只把 `base_revisions` 数字改大后重放旧 operation。

### `source hash mismatch` 或 source changed

原标书、素材或 source manifest 指向的文件在建档后发生变化。恢复被记录的原文件，或以新材料启动新的 bootstrap / migration。不要修改 manifest hash 伪装未变化。

### `required context exceeds token budget`

`must_use` 不会被静默裁剪。拆分任务，或显式提高预算：

```bash
python3 tools/prop_tools.py compile-context --state-dir "$STATE" \
  --target section --id CH-03 --token-budget 36000
```

### `decision.open`、`decision.fog` 或 `decision.assumed`

把能查的事实交研究，把范围外事项明确排除；只有投标人能决定的边界进入 Gate 1。`assumed` 必须由人工确认并同步修改实际对象，不能在 submission 阶段豁免。

### Evidence / authority blocker

检查 Evidence 是否 active/current、正文用途获授权、scope/reason 完整、质量与 Claim 风险相称。第三方案例不能支持 bidder capability。committed authority 只能解析到有范围授权的 Requirement、verified Evidence 或已解决 Gate。

### resource / budget / acceptance blocker

给 selected Action 明确 accountable、responsible、时点、资源区间、预算 treatment 和 Acceptance。组合负载按同单位、同窗口聚合；必要时减少范围、错峰或补已确认容量，而不是用客户依赖转嫁责任。

### realization stale

canonical、brief、正文或 snapshot 任一变化都会让旧审计失效。用当前状态重新 `compile-context`，让独立 auditor 针对当前文本生成 semantic 结果，再运行 `audit-realization`。

### QA 失败

根据 `qa-proposal` 的具体 check 修客户稿。URL、内部 ID、private 原句、策略/版本/工具痕迹属于硬失败；buyer focus、LaTeX、综述等带 `warning=true` 的信号仍需人工判断，但不会单独伪装成 canonical blocker。

## 4. 复跑正确范围

只改客户表层表达且 canonical 未变时，可重审对应正文。只要任一 canonical 发生变化，当前实现就要求重建所有 snapshot-bound brief、正式章节 realization 和 summary，再重新装配。

最终至少复跑：

```bash
python3 tools/prop_tools.py check-compliance \
  --requirements "$STATE/requirements.json" --strategy "$STATE/strategy.json" --report "$REPORT"
python3 tools/prop_tools.py qa-proposal "$REPORT" --mode standard \
  --strategy "$STATE/strategy.json" --requirements "$STATE/requirements.json" --state-dir "$STATE" --lang zh
python3 tools/prop_tools.py check-canonical --state-dir "$STATE" --stage submission \
  --realization-dir "$STATE/derived/realization" --write-derived
python3 tools/prop_tools.py customer-fit --state-dir "$STATE" --checkpoint submission
```

如果 archive 失败，保留临时状态并排查；工具会尽力保留上一份 `_state` 或 last-good。`--allow-draft` 也不能绕过 schema、source 或 fatal 损坏。
