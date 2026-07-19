# 投标决策地图与单题追问

本文件是 `proposal` 的内生流程，不调用外部 skill，也不使用 issue tracker。v3 把问题与答案保存在 `strategy.json`，但答案产生的实际影响通过跨 canonical ChangeSet 同步到 customer-value、delivery-plan 与 strategy，保证能追溯“为什么这样写、它改变了什么”。

## 核心原则

1. **先定终点，再动笔**：Task1 先写清本标的可验证终点；决策路线未清，不启动 Task2/3。
2. **事实不问人，决策才问人**：标书、文件、本地素材能查到的事实由 agent 自己查；公开信息放进 `intel_needs` 交 Task2；只有投标人本人能决定的事项才进入 `open_questions`。
3. **稳定 ID + 可读名称**：每题用不可变 `GATE-*` 作为 authority 身份，用简短 `title` 供人阅读和 `depends_on` 引用；不用 D1/Q1 等裸编号。
4. **一次只解决一个**：Gate 1/2 每轮只问一个决策，并给出推荐答案及理由；等待用户答复后再进入下一题。
5. **前沿清零才执行**：当前可回答的决策叫“前沿”。前沿、被阻塞决策和决策迷雾全部清零后，才进入调研与撰写。
6. **范围外就明确排除**：不属于本次技术标终点的事项放入 `out_of_scope`，不让它们反复回流。
7. **一次确认，一次事务**：用户答案、decision 状态和全部受影响对象必须在一个 Gate ChangeSet 中原子提交；不能出现“问题显示已解决，但 Claim/Action 仍是旧边界”。

## v3 Gate ChangeSet

主 agent 是 canonical 逻辑单写者。Gate 本身不直接散改 JSON，而是写 `changeset/v1` 后调用 `apply-changeset`。最低结构：

```json
{
  "schema_version": "changeset/v1",
  "changeset_id": "CS-G1-CAPABILITY-01",
  "producer": "gate1",
  "base_revisions": {
    "customer-value.json": 2,
    "delivery-plan.json": 1,
    "strategy.json": 1
  },
  "rationale": "保存用户原意及其对价值与承诺边界的影响",
  "validate_stage": "draft",
  "operations": [],
  "affected_refs": [],
  "human_required": false
}
```

每次 Gate operation 至少包含：

- 把对应 open question 的完整对象更新为 `resolved`（或 explicit `-auto` 生成的 `assumed`）。
- 根据答案同步 VP 可行性/状态、Claim scope/commitment/authority、Action readiness/commitment、ResourceEnvelope、Acceptance 或 budget strategy。
- 若答案否定某项能力，优先降级、缩小或转 reserve，不靠改软文隐藏。
- private 答案只改变内部优先级/约束，不能把来源 visibility 改为 public。
- 记录 affected refs。当前 v3 canonical 使用全局 generation snapshot，任一 canonical 改动都会使所有 snapshot-bound brief、realization 与 summary 失效；不能沿用旧审计。后续实际运行稳定后再细化依赖级局部失效。

Task 3、Task 3.5 与红队无 canonical 写权限。它们发现边界问题时只提交 observation/change proposal，由有权限 owner 生成 ChangeSet。

## `strategy.json` schema

`decision_map` 只保存低分辨率地图；具体决策只在 `open_questions` 出现一次，避免两份真相。对象 ID 可列入 `affected_refs`/decision 的影响说明，但不要把 VP/Claim/Action 内容复制进 decision。

```json
{
  "decision_map": {
    "destination": "本次投标抵达终点时的可验证状态，一至两句",
    "not_yet_specified": [
      {
        "name": "尚不能精确提问的决策区域",
        "blocked_by": ["它依赖的决策 title"],
        "promotion_signal": "出现什么信息后，就能把它改写成一个具体问题"
      }
    ],
    "out_of_scope": [
      {
        "item": "明确不属于本次技术标的工作",
        "reason": "为什么排除",
        "forbidden_terms": ["正文中出现即应触发 QA 提示的词；可为空"]
      }
    ]
  },
  "open_questions": [
    {
      "id": "GATE-CAPABILITY-TEAM",
      "title": "可读、唯一的决策名称",
      "q": "需要投标人本人拍板的问题",
      "why_matters": "不确认会造成的废标、丢分、成本或策略后果",
      "ai_assumption": "AI 推荐答案；-auto 时采用的保守假设",
      "depends_on": ["必须先解决的决策 title"],
      "status": "open|resolved|assumed",
      "resolved": null,
      "assumption_risk": false,
      "visibility": "internal|private",
      "safe_constraint": "可发送给写作 agent 的脱敏边界，不含原始私密答案",
      "affected_refs": ["VP/CL/DA/RES/AC 等受影响 ID"]
    }
  ]
}
```

字段约束：

- `destination` 必须具体、可验证，并同时体现合规、评分覆盖和投标人真实能力边界。
- `not_yet_specified` 只放“尚不能把问题说清”的在范围事项；能精确提问的必须立刻进入 `open_questions`。
- `out_of_scope` 是终止区，不会自动回到流程。每项写 `item/reason`；能机械识别的越界内容写进 `forbidden_terms`，其余交红队语义检查。若用户重画终点，再显式移回。
- 两个数组都允许为空；不要为了“地图看起来完整”虚构迷雾或范围外事项。
- `open_questions` **没有数量下限**。路线本来就清晰时允许 `[]`；禁止为了模式配额凑问题。
- 每个 open question 必须有全局唯一、不可变的 `GATE-*` id；只有 producer=gate1/human/main 能把它 resolved。作为 authority 时，`affected_refs` 必须明确包含被授权对象，任意虚构字符串不能解锁承诺。
- `depends_on` 只引用同一数组中的 `title`；不得自依赖、循环依赖或引用不存在的名称。
- `resolved` 保存用户原意，不只写“已确认”。答案还要同步回 `buyer_insight`、`differentiators`、`budget_strategy`、`narrative`、`sections` 等真正受影响字段。
- v3 的 `resolved` 原文留在内部 canonical；section brief 只编译 `safe_constraint` 和受影响对象的 approved projection。涉及底价、关系、个人偏好或内部争议时 `visibility=private`，不得把原答复发送给写作/红队或写进正文。

## 状态与决策前沿

- `open`：仍需人拍板。
- `resolved`：用户已明确回答；`resolved` 字段写入答案。
- `assumed`：仅限 `-auto`；v3 由 `apply-auto-state`、legacy 由 `apply-auto-decisions` 生成。`resolved` 必须严格等于 `ai_assumption`，且 `assumption_risk=true`；v3 同时撤销/降级依赖该 Gate 的 committed/confirmed/匿名公开授权。它只能解锁仍然安全的草案路径，必须进入 `_内部研判.md` 和 `_人工待办.md`。

当前决策前沿 = `status=open` 且其全部 `depends_on` 已解决的决策。交互模式只有 `resolved` 算解决；`-auto` 模式才允许 `assumed` 解锁依赖。其余 open 决策为“被阻塞”。

legacy 回退可直接运行：

```bash
$PY {TOOLSDIR}/prop_tools.py check-strategy {TMPDIR}/strategy.json --mode {depth_mode}
```

v3 同样可用它显示前沿；`check-canonical --stage generation` 只证明 `safe_draft_ready`，canonical 递交门是 `--stage submission`，报告级结论由 `finalize-run` receipt 给出。交互式 Gate 1 结束前，legacy 运行：

```bash
$PY {TOOLSDIR}/prop_tools.py check-strategy {TMPDIR}/strategy.json --mode {depth_mode} --require-settled
```

此时任何 open 决策或 `not_yet_specified` 都会失败。

## Gate 1：策略决策循环

1. 首次进入时只展示一次策略总览：终点、甲方洞察、Big Idea、叙事、差异化、报价、章节，以及“已定 / 前沿 / 被阻塞 / 迷雾 / 范围外”数量。
2. 若用户已在标书附言或素材中明确给出答案，直接标 `resolved`，不要重复问。
3. 若前沿为空且无迷雾，不虚构问题，直接进入最终策略确认。否则从当前前沿中只取一个问题，优先级为：废标/真实性风险 → 高权重评分与能力边界 → 报价边界 → 差异化与叙事 → 未公开的关系和偏好。
4. 每轮严格使用以下结构，只问一个问题：

   ```text
   决策：<title>
   问题：<q>
   为什么现在要定：<why_matters>
   AI 推荐：<ai_assumption>（给出一行理由）
   ```

5. 等用户答复。v3 生成一个 Gate ChangeSet，把答案写入 `resolved`、设 `status=resolved`，并同步修改真正受影响的客户价值、交付和策略对象；legacy 才直接更新 strategy。
6. 重新检查 `not_yet_specified`：
   - 已能精确提问 → 新增为 open 决策；
   - 只是待查公开事实 → 移入对应章节 `intel_needs`；
   - 已证明不影响终点 → 移入 `out_of_scope`；
   - 仍不够清楚 → 留在迷雾，继续解决它依赖的前沿。
7. 重新计算前沿，下一轮仍只问一个。用户主动说“其余全部按推荐”时，可按其明确授权批量标记，不强迫逐题确认。
8. 前沿、被阻塞和迷雾均清零后，给出“已确认决策摘要”，最后只问一次“是否按这版策略继续”。v3 应用最终确认 ChangeSet 并运行 `check-canonical --stage draft`；legacy 运行 `--require-settled`。Task 2 可在决策已清后开始，写作还须 Task 2.5 后的 generation gate。

### `-auto` 行为

`-auto` 不弹 Gate，但也不得把假设伪装成用户确认：

1. 将迷雾逐项归位：可保守假设的升格为 open 决策；可研究的移入 `intel_needs`；范围外的移入 `out_of_scope`。
2. v3 运行 `$PY {TOOLSDIR}/prop_tools.py apply-auto-state --state-dir {TMPDIR}`；legacy 才运行 `apply-auto-decisions strategy.json`。不要手改三个状态字段。
3. v3 在 Task 2.5 后运行 generation gate；legacy 运行 `check-strategy ... --auto --require-settled`。
4. Task 2.5 不得仅因同一边界仍未人工确认而把 assumed 重开为 open；它应按 safe_constraint 形成收窄的 draft_ready/intended/planned 草案。unknown resource/budget 继续保持 unknown，禁止为通过 generation 编造 provisional low/high。
5. 新 Evidence 确实改变边界而需要重开时，完整 Gate 对象必须同步设为 `status=open`、`resolved=null`、`assumption_risk=false`；不得留下 assumed/resolved 残值。auto 再由 `apply-auto-state` 原子转换，不能手改回 assumed。
6. 所有 assumed 决策必须随卷册进入内部研判和人工待办，递交前由投标人复核。
7. v3 assumed 决策是 submission blocker。它可以解锁安全草案，但不能用 soft score、auto 标志或 accepted risk 豁免成可直接递交。

## Gate 2：红队定稿循环

Gate 2 沿用相同的单题原则，不再建立第二套地图。v3 每轮处理的是聚合后的 root diagnostic，而不是逐条关键词警告：

1. 先展示一次当前 profile 的红队总览、机械信号、最强点和对手打法；quick/standard 可合并相邻视角，但硬门不降级。
2. 致命项仍按主流程先自动修复；其余质疑按“预计丢分/对手可利用程度/修改成本”排序。
3. 每轮只处理一条质疑，给出主 agent 的推荐处置：`采纳修改`、`保留并补证据` 或 `不采纳`，说明得失。
4. 等用户回答后，在对应 challenge 写入 `decision` 与 `decision_reason`。若只改表达且 canonical snapshot 未变，可改对应稿并复审；若涉及 Need/VP/Claim/Action/资源/授权，先由真正 owner 提交 ChangeSet，再按当前全局 snapshot 重编译全部 snapshot-bound 章节与摘要、装配并**重新绑定最新 `$REPORT/$BUNDLE/$BRIEF`**，重跑合规、QA、canonical submission 和 customer-fit，再问下一条。
5. 用户可明确授权“其余按推荐处理”。全部处理完后只问一次定稿确认。
6. Gate 2 完成后写 `gate2-decision/v1` attestation（`status=resolved` 且 `open_root_causes=[]`）。最后装配一次，用 `validate-run`/`finalize-run` 聚合合规、QA、canonical submission、ordinal fit、待办与归档，并签发 state/report hash receipt；成功后才清理 TMPDIR。
