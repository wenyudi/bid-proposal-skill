---
name: proposal
description: "政企传媒技术标 v3 生成：拆标书硬要求，建立多角色客户价值与交付 canonical，单题确认真实能力边界，联网补 Evidence，研究后选择客户亮点，并行写作与独立兑现审计，红队和硬门定稿。Use when 用户要写投标方案、应标文件、政企客户提案，提供标书要求出方案，或输入 /proposal。"
---

# proposal v3

为广告/传媒公司生成给政企客户的技术标。最终目标不是“写得多”，而是让关键评委能形成一条可辩护判断：方案懂客户、价值值得、证据可信、交付可验、风险妥帖，同时 mandatory 与评分项零遗漏。

v3 是默认引擎：无标志和兼容 `-v3` 都运行本流程；只有用户显式写 `-legacy` 才加载 `LEGACY.md`。不得在同一 run 混用两套 canonical、章节或 Gate 结果，v3 失败也不得静默改称 legacy 成功。

## 输入与输出

- 必需：标书路径（PDF/DOCX/MD/TXT）或粘贴全文。
- 可选：资质、报价、团队、案例、品牌资料；沟通/踏勘/售前纪要标 `[notes]`，只作 private 校准。
- 自动读取 `casebase/` 中非 `_` 开头案例。
- 输出卷册保持不变：`技术方案-完整版.md`、`分册/`、`_内部研判.md`、`_人工待办.md`。
- v3 另归档 `BUNDLE/_state/`，绝不递交；包含 canonical、sections、快照、诊断与 realization，用于恢复和安全重编译。
- 范围只到技术标。投标函、授权书、承诺函、法定报价表等按标书模板另行套用。

## 五个事实来源

| 文件 | 唯一拥有 |
|:---|:---|
| `requirements.json` | Requirement、mandatory、scoring、预算、标书交付物 |
| `customer-value.json` | CustomerRole、Need、Criterion、ValueProposition、Claim、Metric、EvidenceLink、RoleConflict |
| `delivery-plan.json` | DeliveryRole、Action、ResourceEnvelope、CustomerDependency、AcceptanceContract |
| `strategy.json` | narrative、DecisionJob、章节与人工决策地图 |
| `intel-pool.json` | 本标 Evidence 原记录；不拥有“它证明什么” |

主 agent 是 canonical 逻辑单写者。Task/Gate 只产出带 base revision 的 proposal/ChangeSet；`apply-changeset` 校验全部文件后原子提交，stale 或任一硬门失败则整组回滚。Task 3、摘要和红队无 canonical 写权限。

## 不可降级的门

以下失败不能被客户适配度软分、叙事或红队意见抵消：

- mandatory/scoring/格式/法律/政务导向、预算上限与负偏离。
- 资质、业绩、团队、案例、数字和来源真实性；Evidence 必须有正文用途授权、相关 scope/reason 和风险相称的质量/强度；第三方案例不能证明我方能力。
- private 原句、URL、内部 ID/权重/策略/工具痕迹不得进递交稿。
- selected VP 必须连通 Role + Need + Criterion + 能力/Action 边界。
- publishable Claim 不得 assumed；Evidence、scope、Metric、authority 与措辞强度满足政策。
- committed/confirmed/匿名公开的 authority 必须解析到 scoped Requirement、verified Evidence 或真实 resolved Gate，任意 `GATE-*` 字符串无效；Task 2.5 无权自批。
- required/committed Action 有唯一 accountable、责任/资源/时点、authority 和 Acceptance；每个 selected Action 显式预算 treatment，组合容量与总价不漏算、不超载。
- 每章一个 primary DecisionJob、最多一个 secondary；叙事只有表达权，没有语义裁剪权。
- 分章正文逐条通过 Requirement addressed + Claim/Action realization 独立审计；综述只使用所有正式章的 valid realization 白名单。
- `-auto` 假设只能生成保守草案并进入待办，不能成为 submission-ready。

## 参数

- 深度：`-quick` / 默认 standard / `-deep`。
- 叙事：`-logic` / `-story` / `-vision` / `-evidence`；未指定由 Task 1 按 TYPES.md 判定。
- 关卡：默认 Gate 1 + Gate 2；quick 只停 Gate 1；`-auto` 不交互但保留 assumed 与递交阻断。
- 引擎：默认 v3；`-v3` 是兼容 no-op；`-legacy` 才走旧链。

运行前选择可用 Python 3 解释器并记为 `$PY`（优先 `python3`，Windows 可用 `python`/`py -3`）。所有 JSON/Markdown 使用 UTF-8 无 BOM。

## 主流程（主 agent）

### 1. 摄入与初始化

1. 创建带时间戳 `$TMPDIR`，并建立 `proposals/`、`sections/`；记录开始时间和语言。
2. 标书路径写 `tender_paths.txt`，粘贴文本写 `tender.txt`；素材写 `materials.txt`，沟通纪要加 `[notes]`，casebase 加 `[casebase]`。
3. 读取本文件、RULES.md、TYPES.md；Task 1 前再读 DECISIONS.md。
4. 若没有标书，向用户索要后停止；不要凭项目名猜标书。

如果用户明确要继续旧项目：原目录只读，执行

```bash
$PY {TOOLSDIR}/prop_tools.py migrate-state --source-dir <旧状态目录> --output-dir "$TMPDIR" --mode <mode> --lang <lang>
```

迁移不得修改旧源、旧 casebase 或历史 bundle；unknown/inferred 不得自动升级为 verified/committed/publishable。

若继续的是 v3 `BUNDLE/_state/`：把它作为只读恢复源复制到新 `$TMPDIR`，canonical 与 `sections/` 可恢复，但旧 artifacts/realization 的绝对路径与 brief attestation 不跨目录续用。恢复后必须在新目录重新 freeze/compile-context，并对全部正式章节和摘要复跑独立 realization；不得因 archive 曾经 canonical-ready 就跳过本轮审计。

### 2. Task 1 — v3 bootstrap 与 Gate 1

1. 用 `prompts/task1_teardown.md` 替换变量，派一个高推理 agent。它只写 `proposals/task1.bootstrap.json`。
2. 原子建立状态并校验：

```bash
$PY {TOOLSDIR}/prop_tools.py bootstrap-state --state-dir "$TMPDIR" --proposal "$TMPDIR/proposals/task1.bootstrap.json" --mode <mode> --lang <lang>
$PY {TOOLSDIR}/prop_tools.py check-canonical --state-dir "$TMPDIR" --stage draft --write-derived
$PY {TOOLSDIR}/prop_tools.py check-strategy "$TMPDIR/strategy.json" --mode <mode>
```

失败只重派 Task 1 一次，并把具体 diagnostics 作为修复输入；不要手工绕过 schema/ref 错误。

3. Gate 1 严格按 DECISIONS.md 单题循环。首次只展示一次：终点、最高优先级角色/需求/标准、Big Idea/narrative、候选 VP（不是已定亮点）、预算/交付边界、章节和地图计数。
4. 每轮只问当前前沿的一题，给推荐与得失。回答后由主 agent 写一个 `changeset/v1`（producer=`gate1`），在同一事务中更新 decision 状态及所有受影响 Need/VP/Claim/Action/Resource/Acceptance/strategy 字段，再执行：

```bash
$PY {TOOLSDIR}/prop_tools.py apply-changeset --state-dir "$TMPDIR" --changeset <gate changeset>
```

不能只把 decision 标 resolved 而漏改真实对象；不能把 private 改名成 public。用户说“其余按推荐”才可批量处理。

5. `-auto`：先把迷雾归为明确决策、research gap 或 out_of_scope，再执行：

```bash
$PY {TOOLSDIR}/prop_tools.py apply-auto-state --state-dir "$TMPDIR"
```

assumed 只解锁安全草案，新增能力/KPI/资源/免费增值仍 intended，最终必须明确“不可直接递交”。

### 3. Task 2 — Evidence 研究

1. 编译最小研究 brief：

```bash
$PY {TOOLSDIR}/prop_tools.py compile-context --state-dir "$TMPDIR" --target research
```

2. 用 `prompts/task2_intel.md` 派研究 agent。它读取 brief，只写 `proposals/task2.intel.json` 与 `proposals/task2.links.json`，不改客户语义。
3. 抓取原文，不用搜索摘要充数据；public Evidence 必须有 URL；失败显式 gap，不能覆盖 last-good。
4. 校验并原子提升：

```bash
$PY {TOOLSDIR}/prop_tools.py promote-research --state-dir "$TMPDIR" --intel-proposal "$TMPDIR/proposals/task2.intel.json" --links-proposal "$TMPDIR/proposals/task2.links.json"
```

失败按工具 issue 修 proposal；禁止主 agent 自行补造来源。

### 4. Task 2.5 — 研究后价值选择

1. 编译 selection brief，派 `prompts/task2b_value_selection.md`：

```bash
$PY {TOOLSDIR}/prop_tools.py compile-context --state-dir "$TMPDIR" --target value-selection
```

2. Task 2.5 用窄硬门、短板、Pareto 和组合充分性选择 lead/supporting/reserve，不按亮点数量、篇幅或模板词评分；未选候选继续保留。
3. 应用 `proposals/task2.5.selection.json`：

```bash
$PY {TOOLSDIR}/prop_tools.py apply-changeset --state-dir "$TMPDIR" --changeset "$TMPDIR/proposals/task2.5.selection.json"
```

若 `human_required=true` 或新增能力/成本/授权边界，只重新打开受影响 Gate 1 单题；解决后重跑 Task 2.5，不增第三道固定 Gate。

4. 写作前门与策略 checkpoint：

```bash
$PY {TOOLSDIR}/prop_tools.py check-canonical --state-dir "$TMPDIR" --stage generation --write-derived
$PY {TOOLSDIR}/prop_tools.py customer-fit --state-dir "$TMPDIR" --checkpoint strategy
$PY {TOOLSDIR}/prop_tools.py freeze-snapshot --state-dir "$TMPDIR"
```

generation 失败时按 diagnostic owner 回到 Task 1 / Task 2 / Task 2.5 / Gate 1；不能用下游文案掩盖根因。customer-fit 是内部敏感性区间，不是评委分或中标概率；不反向规定唯一创意解。

### 5. Task 3 — 并行分章 + 独立兑现审计

1. 对每个 `strategy.sections[].id` 编译 brief：

```bash
$PY {TOOLSDIR}/prop_tools.py compile-context --state-dir "$TMPDIR" --target section --id <CH-ID>
```

2. 按 profiles.json 计算建议字数，用 `prompts/task3_section_agent.md` 替换 `{BRIEF_PATH}` 等变量；并行派章节 agent。所有 agent 必须引用同一 snapshot。输出 `sections/section-N.md` 和 `derived/realization/section-N.proposed.json`。
3. 缺文件只重派对应章。若 agent 报 stale/blocked，重新编译 brief；不得把不同 snapshot 的章节拼在一起。
4. 每章另派一个没有参与写作的审计 agent，使用 `prompts/task3c_realization_audit.md`，输出 `section-N.semantic.json`；再执行：

```bash
$PY {TOOLSDIR}/prop_tools.py audit-realization --state-dir "$TMPDIR" --section-ref <CH-ID> --section "$TMPDIR/sections/section-N.md" --hints "$TMPDIR/derived/realization/section-N.proposed.json" --brief <brief path> --semantic <semantic path>
```

`valid` 才进入摘要。纯表达/Requirement 遗漏回 Task 3；Evidence 回 Task 2；VP/Claim/Action 回 Task 2.5；能力/资源/授权回 Gate 1。当前 v3 snapshot 绑定五份 canonical：任一 canonical 改动后，所有 snapshot-bound brief/章节/摘要都必须重新编译与复验，不能把旧 manifest 盖成 current；后续实际使用稳定后再细化依赖级局部失效。

### 6. Task 3.5 — realized-only 方案综述

全部正式章节 valid 后：

```bash
$PY {TOOLSDIR}/prop_tools.py compile-context --state-dir "$TMPDIR" --target exec-summary
```

用 `prompts/task3b_exec_summary.md` 串行写 `section-0.md` 与 hints。再用独立 auditor 和 `audit-realization`（`--section-ref CH-00`）复验。摘要白名单外主张、数字、案例和强化承诺必须删除或走上游 ChangeSet；综述不创造覆盖。

### 7. Task 4 — 预览装配、硬检与红队

1. 装配仍保持客户可见格式。非 auto 的 `$AUTO_ARG` 为空；auto 为 `--auto`：

```bash
$PY {TOOLSDIR}/prop_tools.py assemble-proposal --strategy "$TMPDIR/strategy.json" --requirements "$TMPDIR/requirements.json" --intel "$TMPDIR/intel-pool.json" --sections-dir "$TMPDIR/sections" --mode <mode> --output "{SKILLDIR}/reports/<lang>" --lang <lang> $AUTO_ARG
```

每次从输出重新绑定 `$REPORT/$BUNDLE/$BRIEF`，不要沿用旧路径。

2. 依次运行：

```bash
$PY {TOOLSDIR}/prop_tools.py check-compliance --requirements "$TMPDIR/requirements.json" --strategy "$TMPDIR/strategy.json" --report "$REPORT"
$PY {TOOLSDIR}/prop_tools.py qa-proposal "$REPORT" --mode <mode> --strategy "$TMPDIR/strategy.json" --requirements "$TMPDIR/requirements.json" --state-dir "$TMPDIR" --lang <lang>
$PY {TOOLSDIR}/prop_tools.py check-canonical --state-dir "$TMPDIR" --stage submission --realization-dir "$TMPDIR/derived/realization" --write-derived
$PY {TOOLSDIR}/prop_tools.py customer-fit --state-dir "$TMPDIR" --checkpoint submission
```

`check-compliance` 的 mandatory/scoring 实质遗漏、QA 内部 ID/策略/private raw 泄露或结构错误，以及 canonical submission blocker 都必须修复并重新装配/审计。`self-score` 仅是 legacy 机械兼容信号，v3 不把固定 differentiator 数量或篇幅估分作为 headline。

3. 给 buyer/expert/audit/rival 分别编译 redteam brief：

```bash
$PY {TOOLSDIR}/prop_tools.py compile-context --state-dir "$TMPDIR" --target redteam --role <role>
```

使用 `prompts/task4_redteam.md` 和 TYPES.md 角色说明并行红队。它们读全文与最小审计 brief，提交 root diagnostic，不读 private raw graph、不直接改稿。相同根因合并；没有条数配额。

4. 明确硬门的致命问题立即按 owner 修复；其余进入 Gate 2。Gate 2 按 DECISIONS.md 一次处理一个根因，给出“采纳修改 / 保留并补证据 / 不采纳”的推荐与得失。任何 accepted canonical 修改都走 ChangeSet，并按当前 snapshot 重编译全部绑定 brief/章节/摘要，再 realization、装配、合规、QA、fit。用户明确“其余按推荐”才批量执行。

### 8. 最终归档与交付

1. 最终再装配一次并重绑路径，重跑 compliance、QA、submission canonical 和 customer-fit。正常模式任一硬门失败不得标完成；auto 可交付 draft，但必须醒目标 `submission_ready=false`。
2. 生成最终待办：

```bash
$PY {TOOLSDIR}/prop_tools.py human-todo --requirements "$TMPDIR/requirements.json" --strategy "$TMPDIR/strategy.json" --intel "$TMPDIR/intel-pool.json" --state-dir "$TMPDIR" --report "$REPORT" --mode <mode> --output "$BUNDLE/_人工待办.md" --lang <lang>
```

3. 把 customer-fit（gates、十维等级/区间、短板、uncertainty）、最终红队结论、Gate 取舍和 `submission_ready` 追加进 `_内部研判.md`。不要把 URL、内部诊断或适配度写进递交稿。
4. 状态归档成功后才可删除 TMPDIR：

```bash
$PY {TOOLSDIR}/prop_tools.py archive-state --state-dir "$TMPDIR" --bundle-dir "$BUNDLE"
```

auto/明确草案交付使用 `--allow-draft`，并说明它不是可递交豁免；fatal/schema/source 损坏即使 allow-draft 也拒绝归档。`archive-state` 会连同 sections 原子替换 `_state`，旧状态保留为 `_state.last-good`；失败不得删除 TMPDIR 或上一份成功卷册。archive 只证明 canonical/realization 状态，manifest 使用 `canonical_submission_ready`；最终 `submission_ready` 必须由本轮 report 的 compliance、QA、customer-fit 与 Gate 2 共同判定，archive 不冒充报告级验收。
5. 读取开始时间后再清理临时目录。`_内部研判.md`、`_人工待办.md`、`_state/` 均不递交。

## 最终汇报

用用户语言简洁汇报：

- 方案标题、标型、章数、主叙事与 Big Idea。
- lead/supporting 客户价值（客户结果，而非内部 ID/数量炫耀）。
- mandatory/scoring 覆盖与 submission_ready。
- customer-fit band/range 及 1–3 个最重要短板；明确不是评委分/中标概率。
- 红队致命/重要处理状态，人工待办计数。
- `$BUNDLE` 和递交稿路径；明确三个下划线内部内容不递交。
- `-auto` 或任何硬门未清时，首句写“已生成草案，不可直接递交”，不要用“方案生成完成”掩盖风险。

## 阅读体验原则

严格模型只在底层工作。客户可见正文不显示 Role/Need/DecisionJob/Claim/Evidence ID、覆盖标签、适配度、状态机或审计过程；用自然标题、集中表格、清楚口径和顺滑过渡表达。不要为了显得严谨让每句都带限定语，也不要为了发散而把 reserve 候选塞进正文。候选阶段开放，研究后收敛，最终只呈现少而强、能兑现的组合。

---
```
proposal skill · 3.0.0 · v3 direct-default
```
