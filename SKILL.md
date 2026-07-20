---
name: proposal
description: "政企传媒技术标 v3.2：拆硬要求，先收敛评委可复述的一页纸策略，再以同一主线生成客户亮点与可兑现正文，独立审计、策略批评、红队和一键终验。Use when 用户要写投标方案、应标文件、政企客户提案，提供标书要求出方案，或输入 /proposal。"
---

# proposal v3.2

为广告/传媒公司生成政企技术标。目标不是让每章分别合格，而是让关键评委记住一个有据的核心主张，并沿同一推导链相信：方案懂客户、亮点值得选、正文有可检查成果、证据可信、交付可验、风险妥帖，同时 mandatory/scoring 零遗漏。

v3.2 是默认引擎；`-v3` 是兼容 no-op，只有显式 `-legacy` 才读 `LEGACY.md`。失败不得静默降级或把草案称为可递交稿。

## 交付与底层状态

- 输入：标书路径或全文；可附资质、报价、团队、案例和品牌资料。沟通/踏勘纪要标 `[notes]`，只作 private 校准。
- 自动读取 `casebase/` 中非 `_` 开头案例。
- 客户卷册：`技术方案-完整版.md`、`分册/`。内部文件：`_内部研判.md`、`_人工待办.md`、`_state/`、`_acceptance-receipt.json`，均不递交。
- 范围只到技术标；投标函、授权书、承诺函和法定报价表按标书模板另行套用。

五份 canonical 是唯一事实源：

| 文件 | 拥有 |
|:---|:---|
| `requirements.json` | Requirement、mandatory/scoring、预算与标书交付物 |
| `customer-value.json` | Role、Need、Criterion、`decision_paths`、VP、Claim、Metric、EvidenceLink |
| `delivery-plan.json` | DeliveryRole、Action、Resource、Dependency、Acceptance |
| `strategy.json` | 一页纸策略、narrative、人工决策、Section；DecisionJob、`strategy_role` 与轻量 `visible_outputs` 内嵌在 Section |
| `intel-pool.json` | Evidence 原记录；不拥有“它证明什么” |

主 agent 是 canonical 逻辑单写者。Task/Gate 只产 proposal/ChangeSet；`apply-changeset` 按 base revision 校验五文件并原子提交，stale 或任一硬门失败整组回滚。writer、summary、auditor、redteam 都无 canonical 写权限。

## 两级 readiness

- `safe_draft_ready`：允许 selected VP、`draft_ready` Claim、`intended/planned` Action 和 unknown 资源进入安全草案；正文必须保持拟议/待确认边界。不得用虚构 provisional low/high、容量、报价或 authority 解锁。
- `submission_ready`：所有 assumed/open、真实性、授权、资源预算、realization、正文 QA、客户适配与 Gate 2 均闭合。

`-auto` 最多到 safe draft；任何 assumed 都进入待办并阻断直接递交。

## 不可降级的门

详细政策只以 `RULES.md` 为准。以下类别不能被叙事、fit 或红队软意见抵消：

- mandatory/scoring/法律/格式/政务导向、预算上限、负偏离和客户责任转嫁。
- 资质、业绩、团队、案例、数字与来源真实性；第三方案例不能证明我方能力，private/raw/URL/内部 ID 与策略痕迹不得外泄。
- publishable/committed/confirmed/匿名公开必须有用途、scope、Evidence/Metric 和真实 scoped authority；任意 `GATE-*` 字符串不构成授权。
- 每个 committed Action 有唯一 accountable、责任、时点、资源、预算 treatment 与 Acceptance；组合不漏算、不超载。
- 每章一个内嵌 primary DecisionJob、最多一个 secondary；每个 lead VP 至少一个 required customer-visible output。required fields 未填实则 realization invalid。
- `strategy/v5` 写作前必须有 research-informed 一页纸：尖锐洞察、记忆句、推导链、互换测试、落地可信度和逐章 spine；人工只批准一次。`-auto` 可 assumed 生成安全草案，但阻断递交。
- 每章 Requirement + Claim/Action + visible output 由未参与写作的 auditor 独立复核；综述只用 valid 白名单。

这些约束只在底层出现。客户正文不显示模型名、ID、状态、覆盖标签、fit 或审计过程；不为严谨堆限定语，也不把 reserve 候选塞进正文。

## 参数与运行变量

- 深度：`-quick` / standard（默认）/ `-deep`。
- 叙事：`-logic` / `-story` / `-vision` / `-evidence`；未指定由 Task 1 按 `TYPES.md` 选择，短 guide 从 `narratives.json` 编译。
- `profiles.json` 决定 token、字数、`redteam_roles` 和 `audit_batch_size`。v3 章节数完全等于 `strategy.sections`；profile 固定章数只用于 legacy。
- Python 记为 `$PY`；JSON/Markdown 使用 UTF-8 无 BOM。

渐进加载参考，避免质量门压缩发散：Task 1 只读 `references/strategy-patterns.md`；Task 2.5 再读 rubric、合成对照与反模式；writer 只读对照/反模式；策略红队只读 rubric/反模式。合成样例绝不是 Evidence。真实失败按 `casebase/_quality-lessons/_template.md` 复盘，人工确认后才提升为共享样例。

派 agent 前由主 agent赋值：`{LANG}`、`{MODE}`、`{TMPDIR}`、`{CURRENT_YEAR}`、`{COUNTRY}`、`{BRIEF_PATH}`、`{PER_SECTION_CHARS}=round(max_chars/正式章数)`、`{MIN_PARAGRAPHS}`。auditor 的 `{AUDIT_ITEMS}` 是 2–3 章列表，每项含 section ref、brief/section/semantic output 路径。

## 主流程

### 1. 摄入、bootstrap 与 Gate 1

1. 建时间戳 `$TMPDIR` 与 `proposals/task1.components/`；保存标书/素材清单。没有标书就向用户索要并停止，不能凭项目名猜。
2. 主 agent 读本文件、`RULES.md`、`TYPES.md`、`DECISIONS.md`。用 `prompts/task1_teardown.md` 派一个高推理 Task 1 agent，逐份写五个组件和小索引 `proposals/task1.bootstrap.json`；一页纸此时只是 candidate，替代命题留在池中。
3. 建状态并校验：

```bash
$PY {TOOLSDIR}/prop_tools.py bootstrap-state --state-dir "$TMPDIR" --proposal "$TMPDIR/proposals/task1.bootstrap.json" --mode <mode> --lang <lang>
$PY {TOOLSDIR}/prop_tools.py check-canonical --state-dir "$TMPDIR" --stage draft --write-derived
```

schema/ref 失败只把 diagnostics 回给 Task 1 修一次；再次失败就报告并停止，不手改、不切 legacy。

4. Gate 1 按 `DECISIONS.md` 一次问当前前沿一题，给推荐与得失。回答后主 agent 写 `producer=gate1` 的 ChangeSet，一次更新 decision 与所有受影响对象，再 `apply-changeset`。用户说“其余按推荐”才可批量。
5. `-auto` 用 `apply-auto-state`；assumed 只解锁安全草案。

继续旧项目使用 `migrate-state --source-dir <旧目录> --output-dir "$TMPDIR"`，原目录只读。恢复 `_state/` 也复制到新 `$TMPDIR`；路径绑定不跨目录，必须重新 freeze、compile 和独立 audit。

### 2. Evidence 研究与价值选择

```bash
$PY {TOOLSDIR}/prop_tools.py compile-context --state-dir "$TMPDIR" --target research
```

用 `prompts/task2_intel.md` 派研究 agent，只写 intel/links proposal；抓原文，不用搜索摘要充数，失败写 gap。然后 `promote-research` 原子提升。

编译 selection brief，派 `prompts/task2b_value_selection.md`：

```bash
$PY {TOOLSDIR}/prop_tools.py compile-context --state-dir "$TMPDIR" --target value-selection --token-budget <profile budget × 1.5>
$PY {TOOLSDIR}/prop_tools.py apply-changeset --state-dir "$TMPDIR" --changeset "$TMPDIR/proposals/task2.5.selection.json"
$PY {TOOLSDIR}/prop_tools.py compile-context --state-dir "$TMPDIR" --target strategy-review
# 人工 approval ChangeSet；-auto 则再次 apply-auto-state
$PY {TOOLSDIR}/prop_tools.py check-canonical --state-dir "$TMPDIR" --stage generation --write-derived
$PY {TOOLSDIR}/prop_tools.py freeze-snapshot --state-dir "$TMPDIR"
```

Task 2.5 用短板、Pareto 和组合充分性选 lead/supporting/reserve，不按数量或模板词评分；同时收敛 `one_page_strategy` 与每章 `strategy_role`，为 lead 收敛最小 visible output。它只可写 `approval=pending`，ChangeSet 用 draft gate。

主 agent 从 `strategy-review` 只展示张力、洞察、核心主张/记忆句、推导链、互换测试、落地逻辑、逐章贡献和五维弱项，然后只问一次“是否按这一页进入写作？”确认后用 `producer=human` ChangeSet 写 `approval=approved` 和 reviewer；要求修改则只回 Task 2.5 修根因。`-auto` 在 Task 2.5 后再次运行 `apply-auto-state` 写 `approval=assumed`。随后才运行 generation gate 与 freeze。新增能力/成本/权限边界才回 Gate 1；同一 assumed 不重复开题。

### 3. 分章、批量独立 audit 与综述

1. 对每个 Section 运行 `compile-context --target section --id <CH-ID>`；brief 始终带已批准一页纸、完整 section spine、本章贡献和前序 canonical 骨架摘要。匹配当前 state/source/run 的 snapshot 会复用，不重复完整 generation 校验。
2. 用 `prompts/task3_section_agent.md` 并行派 writer。每个 writer 只写自己的 `sections/section-N.md`，引用同一 snapshot；缺文件只重派对应章。
3. 按 profile 的 `audit_batch_size` 把 2–3 章交给未参与写作的 auditor，使用 `prompts/task3c_realization_audit.md`。同一 auditor 可批量读，但每章独立 semantic 文件，禁止跨章引用。逐章执行：

```bash
$PY {TOOLSDIR}/prop_tools.py audit-realization --state-dir "$TMPDIR" --section-ref <CH-ID> --section <section.md> --brief <brief.json> --semantic <semantic.json>
```

`--hints` 仅兼容 v3.0 旧运行，新 writer 不生成 sidecar。invalid 按最近 owner 返回：表达/Requirement/成果字段→Task 3，Evidence→Task 2，VP/Claim/Action→Task 2.5，能力/资源/授权→Gate 1。

4. 全部正式章 valid 后 `compile-context --target exec-summary`，用 `task3b_exec_summary.md` 串行写 `section-0.md`，再由独立 auditor 和同一工具复验。任一 canonical 改动使全局 snapshot 失效，所有绑定输出重编译/复验。

### 4. 装配、适应性红队与 Gate 2

1. `assemble-proposal` 生成预览并从结果重新绑定 `$REPORT/$BUNDLE/$BRIEF`。
2. 从 `profiles.json` 取角色：quick=`integrated`；standard=`strategy_critic,audit_rival`；deep=`buyer,strategy_critic,audit,rival`。逐角色 `compile-context --target redteam --role <role>`，用 `task4_redteam.md` 并行攻击。strategy critic 必做一句话复述、推导、名称互换、逐章贡献和通用 exact quote；红队只交 root diagnostic，不改稿、不凑条数。
3. 硬门问题立即按 owner 修；其余按 `DECISIONS.md` Gate 2 一次处理一个根因。accepted canonical 改动走 ChangeSet，并重做 snapshot-bound 输出、装配和审计。不满意先只归入 `strategy_hollow / throughline_break / cliche_style` 一个主失败：前两类回 Task 2.5/Section spine，第三类回 Task 3。经真实反馈确认的好坏对照再沉淀到 `_quality-lessons/`，不能把客户私密原文写回 skill。
4. Gate 2 收口写内部 JSON：

```json
{"schema_version":"gate2-decision/v1","status":"resolved","open_root_causes":[]}
```

未人工处置或仍有根因时不得伪造 resolved；`-auto` 保持 draft-only。

### 5. 一键终验、归档与 receipt

最终重装配后只调用聚合入口；它一次完成 compliance、QA、submission canonical、ordinal customer-fit、human todo，并复用同一 checked result：

```bash
$PY {TOOLSDIR}/prop_tools.py validate-run --state-dir "$TMPDIR" --report "$REPORT" --mode <mode> --lang <lang> --gate2 <gate2.json> --todo-output "$BUNDLE/_人工待办.md"
$PY {TOOLSDIR}/prop_tools.py finalize-run --state-dir "$TMPDIR" --report "$REPORT" --bundle-dir "$BUNDLE" --mode <mode> --lang <lang> --gate2 <gate2.json> --todo-output "$BUNDLE/_人工待办.md"
```

明确草案交付给 `finalize-run` 加 `--allow-draft`；它不豁免 fatal/schema/source 损坏。归档原子替换 `_state`，旧状态保留 `_state.last-good`；失败不得删除 TMPDIR/上一成功卷。receipt 绑定 `state_hash + report_hash`，其 `delivery_status` 才是报告级结论，archive manifest 不冒充 submission-ready。

把 fit 的十维 ordinal、top gaps、红队/Gate 取舍和 readiness 写入 `_内部研判.md`，不要写入递交稿。归档成功并读取开始时间后才清理 TMPDIR。

## 最终汇报

用用户语言简洁给出：标题/标型/章数/叙事，lead/supporting 的客户结果，mandatory/scoring 与 `submission_ready`，fit rating 和 1–3 个 top gaps（明确不是评委分或中标概率），红队与待办计数，卷册/递交稿/receipt 路径。

只要不是 submission-ready，首句必须写“已生成草案，不可直接递交”，不能用“方案完成”掩盖风险。

---
`proposal skill · 3.2.0 · strategy-led lean default`
