# Task 4 命令参考（v3）

权威顺序见 SKILL.md。本文件只列主 agent 的最终审计/装配命令；所有命令使用同一 `$TMPDIR` 和当前 generation snapshot。

## 1. 写作与摘要兑现门

每章和 section-0 都应已通过：

```bash
$PY {TOOLSDIR}/prop_tools.py audit-realization --state-dir "$TMPDIR" --section-ref <CH-ID> --section <section.md> --hints <proposed.json> --brief <brief.json> --semantic <semantic.json>
```

任一 manifest 非 valid 不进入装配。表达问题回 Task 3；Evidence 回 Task 2；VP/Claim/Action 回 Task 2.5；能力/资源/授权回 Gate 1。

## 2. 预览装配

`$AUTO_ARG` 仅 `-auto` 时为 `--auto`：

```bash
$PY {TOOLSDIR}/prop_tools.py assemble-proposal --strategy "$TMPDIR/strategy.json" --requirements "$TMPDIR/requirements.json" --intel "$TMPDIR/intel-pool.json" --sections-dir "$TMPDIR/sections" --mode <mode> --output "{SKILLDIR}/reports/<lang>" --lang <lang> $AUTO_ARG
```

解析并重新绑定 `Proposal assembled` → `$REPORT`、`BundleDir` → `$BUNDLE`、`InternalBrief` → `$BRIEF`。每次重装配都重绑。装配在 staging 完成，上一份成功卷册进入报告目录 `.last-good/`。

## 3. 四类硬检

```bash
$PY {TOOLSDIR}/prop_tools.py check-compliance --requirements "$TMPDIR/requirements.json" --strategy "$TMPDIR/strategy.json" --report "$REPORT"
$PY {TOOLSDIR}/prop_tools.py qa-proposal "$REPORT" --mode <mode> --strategy "$TMPDIR/strategy.json" --requirements "$TMPDIR/requirements.json" --state-dir "$TMPDIR" --lang <lang>
$PY {TOOLSDIR}/prop_tools.py check-canonical --state-dir "$TMPDIR" --stage submission --realization-dir "$TMPDIR/derived/realization" --write-derived
$PY {TOOLSDIR}/prop_tools.py customer-fit --state-dir "$TMPDIR" --checkpoint submission
```

- compliance：mandatory/scoring 实质遗漏必须补。
- QA：structure、no_internal_leak、no_private_raw_leak 等硬项必须过；URL、internal ID/策略/模式/工具痕迹，以及 private/internal/匿名批准前 raw 原句都不能进递交稿，只能使用 approved projection。
- canonical：Claim/Evidence/Metric/authority、Action/Owner/Resource/Acceptance、coverage、snapshot/realization 和 assumed 状态均受检。
- customer-fit：硬门失败 overall withheld；区间不是评委分或中标概率。
- `self-score` 只保留 legacy 兼容，不作为 v3 headline；固定 differentiator 数量不再是门。

修改后从受影响 canonical owner/brief/section 开始重跑，不能只改最终 Markdown 掩盖根因。

## 4. 红队与 Gate 2

四个角色分别编译：

```bash
$PY {TOOLSDIR}/prop_tools.py compile-context --state-dir "$TMPDIR" --target redteam --role buyer
$PY {TOOLSDIR}/prop_tools.py compile-context --state-dir "$TMPDIR" --target redteam --role expert
$PY {TOOLSDIR}/prop_tools.py compile-context --state-dir "$TMPDIR" --target redteam --role audit
$PY {TOOLSDIR}/prop_tools.py compile-context --state-dir "$TMPDIR" --target redteam --role rival
```

用 task4_redteam.md 并行派发。相同 root_cause 合并；确定硬门致命项先按 owner 修，模型独有低置信度只 needs_review。其余按 DECISIONS.md Gate 2 一次一题；canonical 变化走 ChangeSet，并按当前全局 snapshot 重编译/realization 全部绑定输出后再装配复验。

## 5. 最终待办、内部研判与状态

最终重装配和四类硬检通过后：

```bash
$PY {TOOLSDIR}/prop_tools.py human-todo --requirements "$TMPDIR/requirements.json" --strategy "$TMPDIR/strategy.json" --intel "$TMPDIR/intel-pool.json" --state-dir "$TMPDIR" --report "$REPORT" --mode <mode> --output "$BUNDLE/_人工待办.md" --lang <lang>
$PY {TOOLSDIR}/prop_tools.py archive-state --state-dir "$TMPDIR" --bundle-dir "$BUNDLE"
```

把最终 fit、红队、Gate 取舍和报告级 submission_ready 追加 `$BRIEF`。auto/明确草案使用 `archive-state --allow-draft`，并醒目标“不直接递交”；archive 返回的 `canonical_submission_ready` 不替代本轮 report 的 compliance/QA/fit/Gate 2。归档成功、开始时间已读取后才删除 TMPDIR。

## 验收

- [ ] Requirement 映射与正文实质响应零遗漏
- [ ] 所有正式 section 与 summary realization valid、snapshot fresh
- [ ] publishable Claim 均有合法 Evidence/Metric/authority，private 不泄露
- [ ] selected/committed Action 的 Owner/资源/依赖/验收与组合容量有效
- [ ] compliance、QA、canonical submission 全过；fit 未被误称中标分
- [ ] 红队根因已处理或按权限记录，不存在硬门 waiver
- [ ] `_人工待办.md`、`_内部研判.md`、`_state/` 明确不递交
- [ ] last-good 仍可恢复

---
```
proposal skill · 3.0.0 · v3 assembly
```
