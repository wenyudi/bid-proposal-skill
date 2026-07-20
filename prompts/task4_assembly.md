# Task 4 命令参考（v3.2）

权威顺序见 `SKILL.md`。本页只保留装配、红队与终验命令；所有输入属于同一 `$TMPDIR` 和 generation snapshot。

## 1. 兑现门

每个正式章和 CH-00 已由独立 auditor 产生 semantic 文件，再逐章通过：

```bash
$PY {TOOLSDIR}/prop_tools.py audit-realization --state-dir "$TMPDIR" --section-ref <CH-ID> --section <section.md> --brief <brief.json> --semantic <semantic.json>
```

auditor 直接依据正文判断，无需 writer hints。Requirement addressed、Claim/Action entailed、required visible output filled 共同构成 valid；invalid 保持原 manifest 状态，并按 diagnostic owner 回上游修复。

## 2. 预览装配

```bash
$PY {TOOLSDIR}/prop_tools.py assemble-proposal --strategy "$TMPDIR/strategy.json" --requirements "$TMPDIR/requirements.json" --intel "$TMPDIR/intel-pool.json" --sections-dir "$TMPDIR/sections" --mode <mode> --output "{SKILLDIR}/reports/<lang>" --lang <lang> $AUTO_ARG
```

每次从返回值重新绑定 `$REPORT/$BUNDLE/$BRIEF`。`$AUTO_ARG` 在 `-auto` 时取 `--auto`；最终可递交性以 receipt 为准。

## 3. 自适应红队与 Gate 2

从 `profiles.json` 读取 `redteam_roles`，逐角色执行：

```bash
$PY {TOOLSDIR}/prop_tools.py compile-context --state-dir "$TMPDIR" --target redteam --role <role>
```

用 `task4_redteam.md` 并行派发。strategy_critic / integrated 完成复述、洞察、推导、互换、逐章贡献和落地五测；相同 root cause 合并，硬门按 owner 先修，其他按 `DECISIONS.md` 一次一题。canonical 变化后重建全部 snapshot-bound 输出。全部根因经人工处置后写真实 `gate2-decision/v1` attestation；其余状态保持 open。

## 4. 聚合终验与归档

最后重装配并重新绑定路径，然后：

```bash
$PY {TOOLSDIR}/prop_tools.py validate-run --state-dir "$TMPDIR" --report "$REPORT" --mode <mode> --lang <lang> --gate2 <gate2.json> --todo-output "$BUNDLE/_人工待办.md"
$PY {TOOLSDIR}/prop_tools.py finalize-run --state-dir "$TMPDIR" --report "$REPORT" --bundle-dir "$BUNDLE" --mode <mode> --lang <lang> --gate2 <gate2.json> --todo-output "$BUNDLE/_人工待办.md"
```

`finalize-run` 复用一次 canonical submission check，聚合 compliance、QA、ordinal fit、todo、Gate 2 和 archive，并签发 state/report-bound receipt。草案加 `--allow-draft`，receipt 显示 `draft_only`；fatal/schema/source 损坏返回修复诊断。归档成功后清理 TMPDIR，并保留 last-good。

## 验收

- Requirement 映射与正文响应零遗漏；所有 section/summary realization valid。
- lead 的 required visible output 已填实，正文成果具备项目实值和当前可检查性。
- Claim/Evidence/Metric/authority 与 Action/Owner/Resource/Acceptance 均在真实边界内。
- receipt 为 `submission_ready`，或首句明确“草案，不可直接递交”。
- 客户卷册与内部附件分离；`_内部研判.md`、`_人工待办.md`、`_acceptance-receipt.json`、`_state/` 保持内部，last-good 可恢复。
