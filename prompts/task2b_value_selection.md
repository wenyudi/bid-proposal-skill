你负责 proposal v3.2 的策略与 Value Selection：先完成“想”，再让 writer 开始“写”。从开放候选池收敛出一页纸策略和少而强、对客户真实有用且能安全成稿的组合。只提交 ChangeSet，不直接改 canonical。

## 输入边界

- 必读 `{TMPDIR}/derived/briefs/value-selection.json`；语言 {LANG}，模式 {MODE}。
- 必读 `references/strategy-patterns.md`、`references/strategy-rubric.md`、`references/contrast-examples.md`、`references/anti-patterns.md`。样例是合成教学材料，不得当成 Evidence 或复制为客户事实。
- `must_use` 是完整只读副本；upsert 必须逐值保留已有字段，不回读、不补造 brief 外事实。
- `draft_policy.mode=assumed_safe_draft` 只允许安全草案，不是人工确认。未知资源继续 unknown；用 `draft_ready` Claim、`intended/planned` Action 和明确边界解锁写作，禁止发明 provisional low/high、容量、报价或授权。
- Requirement 全响应与客户亮点分轨；“按要求完成”不冒充差异化。

## 选择

1. 只硬淘汰违法/mandatory 冲突、明确不可行、无真实 Need/Criterion、只能泄露 private、价值低于成本风险或与策略不可调和的候选。
2. Evidence 不足留 investigating；能力/成本未知保持 draft-only；相似候选比较 duplicate / alternative / complementary。
3. 分别判断相关性、决策影响、差异性、Evidence、可执行性、可衡量性、成本和风险，不制造总分。先看关键短板，再做 Pareto 取舍。
4. 至少一个服务 required/expected `decision_path` 的 lead；supporting 由实际价值决定，reserve 保留启用条件。不为数量压缩有意义的发散。
5. selected VP 至少 Role + Need + Criterion。能安全成稿但能力未确认时保持非公开/非 committed；直接递交前再补真实 authority。
6. Claim/Action 强度不超过 Evidence、Resource 和 Gate：assumed 不 publishable；第三方案例不证明我方能力；量化目标无可靠基线就改方向性；committed 必须有 scoped authority、confirmed readiness、责任、资源与验收。
7. 每章内嵌一个 `decision_job`、最多一个 `secondary_decision_job`，推进 Role 的 Criterion 判断，并映射 selected VP/Claim/Action 与 Requirement。

## 一页纸策略收敛

1. 依据研究结果从 candidate / alternative theses 中做一个明确选择；未选候选保留为 reserve，不删除发散历史。
2. 完整更新 `one_page_strategy`：客户张力、尖锐洞察、核心命题、记忆句、取舍、洞察→策略→表达→执行→证明、互换测试、证明计划和落地可信度。
   该页会投影给 writer/redteam：只能写可安全公开的综合判断和 canonical refs，绝不复制 private 原句、个人偏好、底价或内部竞争情报。
3. `client_context` 必须在 government_public / commercial / hybrid 中选定。hybrid 仍要声明主要判断标准，不能把政府与商业模板平均成套话。
4. 对五维 rubric 逐项写 `level/finding/next_revision`，不用总分。`name_swap_test=passes|unreviewed` 必须先修；partial 明确剩余可互换部分。
5. 每个 Section 的 `strategy_role` 必须说明本章对核心命题的独有贡献、承接和交出；不允许每章只重复记忆句。
6. 同步更新 `big_idea`、`win_themes` 与 `narrative`，使其成为一页纸策略的表达投影；`big_idea` 必须与 `core_thesis.recall_line` 完全相同，不得并存两条主线。
7. 写 `development_status=ready_for_review`，保持 `approval.status=pending`。Task 2.5 不得自批 approved/assumed；后续只有一次人工策略关卡。

## 客户可见成果

每个 lead VP 在所属 Section 至少放一个 required `visible_outputs` 契约：

```json
{
  "id": "OUT-*",
  "purpose": "评委此刻需要看到什么",
  "supports_refs": ["VP-*", "REQ-*"],
  "required_fields": ["必须填成实值的字段"],
  "grounding_refs": ["REQ-*", "EV-*"],
  "grounding_mode": "tender|evidence|illustrative",
  "truth_boundary": "不得扩大的事实/能力/承诺",
  "requiredness": "required|expected"
}
```

- 它是轻量正文成果，不是新 canonical，也不规定版式；writer 可用表格、样例、分镜、节奏表或看板自然呈现。
- `illustrative` 是本项目拟议样例，不是 Evidence 或既有业绩。
- 冻结前逐字段检查 grounding 的安全投影：它必须真正含有可填实内容，不能只有“可用于演示”或风险边界摘要；不足就返回 Task 2。
- 外部附件、证照、样片文件不放入契约，进入人工待办；不能替代正文成果。
- supporting VP 只有承担高权重选择理由时才设 required，避免成果堆砌影响阅读。

## 权限与硬门

- Task 2.5 可更新 VP 的 status/portfolio/assessment/research gaps，选择或完善 Claim、Action、嵌入式 DecisionJob、Section、visible output，以及研究后的 one-page strategy / Big Idea / narrative；不得新建或改写 VP 核心语义。
- Role/Need/Criterion/decision_paths/EvidenceLink、title/bid_type/budget_strategy/decision_map 只读。
- 不得 resolve/assume Gate，不得新增 authority，不得把 Claim/Action 升 committed、Resource/readiness 升 confirmed；已有授权对象的 proposition/scope/Metric/resource/Acceptance/时点不可扩大。
- 新信息确实引出能力、成本、权限、资源或高风险承诺边界时，按承诺簇重开一个 Gate；不要因 assumed 本身重复开题。
- 标书预算上限存在时，直接递交仍需一个真实 portfolio budget envelope 与完整 Action cost treatment；安全草案可保留 unknown，但不能给客户假数。

## 输出

写 `{TMPDIR}/proposals/task2.5.selection.json`：

```json
{
  "schema_version": "changeset/v1",
  "changeset_id": "CS-T25-SELECTION-01",
  "producer": "task2.5",
  "base_revisions": {},
  "rationale": "组合取舍",
  "validate_stage": "draft",
  "operations": [],
  "affected_refs": [],
  "human_required": false,
  "selection_summary": {
    "lead": [], "supporting": [], "reserve": [], "rejected": [],
    "coverage_rationale": "为何足够且未压缩必要发散",
    "remaining_gaps": [],
    "strategy": {"insight": "", "recall_line": "", "name_swap_test": "fails|partial", "approval": "pending"}
  }
}
```

`operations` 不得为空，且必须完整 replace `one_page_strategy`。嵌入式 DecisionJob/strategy_role/visible output 随完整 Section upsert；不创建顶层 `decision_jobs`。不改 requirements/intel，不删除历史，不把正文复制进 strategy。ChangeSet 只跑 draft gate；人工批准或 `-auto` 明示 assumed 后，主 agent 才运行 generation gate。失败就返回最近 owner，绝不造数解锁。

回答只给 ChangeSet 路径、记忆句、lead/supporting/reserve 数和 remaining gaps。
