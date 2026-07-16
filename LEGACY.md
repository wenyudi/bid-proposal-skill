# proposal 2.x explicit fallback

只在用户显式指定 `-legacy` 时加载本文件。默认、`-v3` 或旧数据输入都不能自动触发 legacy。一个 run 从开始到结束保持 legacy；不得读取 v3 customer-value/delivery-plan/brief/realization 来拼装旧章节，也不得把 legacy 产物标成 v3。

legacy 的用途是紧急回退和维护旧项目，不再新增功能。旧 schema、casebase 与历史 bundle 继续可读；如用户要转回 v3，另建目录运行 `migrate-state`，绝不覆盖旧状态。

## 流程

1. 创建 `$TMPDIR`，摄入标书/素材，解析 language、quick/standard/deep、narrative、auto。标书必需；`[notes]` 只内部使用。
2. 用 `prompts/legacy/task1_teardown.md` 生成 `requirements.json` 与 `strategy.json`，运行：

```bash
$PY {TOOLSDIR}/prop_tools.py check-requirements "$TMPDIR/requirements.json"
$PY {TOOLSDIR}/prop_tools.py check-strategy "$TMPDIR/strategy.json" --mode <mode>
```

3. 按 DECISIONS.md 执行 Gate 1 单题循环；更新答案与实际策略字段。auto 使用旧 `apply-auto-decisions`。在研究/写作前用 `check-strategy --require-settled`（auto 加 `--auto`）。
4. 用 `prompts/legacy/task2_intel.md` 调研并写旧数组格式 `intel-pool.json`。
5. 读取 strategy sections，用 `prompts/legacy/task3_section_agent.md` 并行分章；每章嵌入本章 Requirement、公开情报、叙事和决策边界。失败只重写对应章。
6. 全章完成后用 `prompts/legacy/task3b_exec_summary.md` 串行写 `section-0.md`。
7. 用 `assemble-proposal` 装配，并循环运行 `check-compliance`、`qa-proposal`、`escape-currency`；mandatory/scoring 漏项和内部泄露必须修。`self-score` 只作旧机械信号。
8. 用 `prompts/legacy/task4_redteam.md` 并行 buyer/expert/audit/rival。硬风险先修；其余按 DECISIONS.md Gate 2 单题取舍。
9. 最终重装配与复验，生成 `_人工待办.md`，把旧自评和红队结论追加 `_内部研判.md`。下划线文件均不递交。

## 旧链不变量

- mandatory/scoring、真实性、预算、政务导向、private 隔离、无 URL/内部 ID/销售 CTA 的门不降低。
- `-auto` assumed 必须进入待办，不能伪装 confirmed。
- 客户可见卷册格式与 v3 相同，但没有 `_state`、customer-fit 或 realization 保证；最终汇报明确 `engine=legacy`。
- 装配使用 staging 与 `.last-good`，失败不删除上一份成功卷册。

---
```
proposal skill · legacy 2.x fallback only
```
