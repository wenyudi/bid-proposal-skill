# Plan 008: 项目化成果与竞争稿就绪门 — 让“说到”升级为“做出来并可检查”

> **Disposition: REJECTED. Do not execute this plan.** 原设计引入过重 proof/readiness 结构；v3.1 已用 Section 内嵌的轻量 `visible_outputs`、直接 semantic audit 和既有 submission gate 实现核心效果。本文件只保留为设计取舍记录。

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**:
>
> ```bash
> git diff --stat b10506e -- SKILL.md RULES.md TYPES.md DECISIONS.md prompts/ tools/prop_v3.py tests/test_prop_v3.py
> git status --short -- SKILL.md RULES.md TYPES.md DECISIONS.md prompts/ tools/prop_v3.py tests/test_prop_v3.py
> ```
>
> Plan 005 若已执行，`TYPES.md`、`task3_section_agent.md` 和 `SKILL.md` 出现预期变更，不是自动 STOP；先逐项比对并保留 `{NARRATIVE_GUIDE}`。除此以外，任何与本计划 Current state 不一致的在途改动均停下报告。

## Status

- **Priority**: P1（直接决定“合规骨架”能否成为“竞争稿”）
- **Effort**: L
- **Risk**: MEDIUM（扩展 strategy/brief/realization 契约与 submission gate，但不新增事实源）
- **Depends on**: Plan 004；Plan 006 的修订后前置基线（执行前必须已经保存）
- **Soft order**: 建议 Plan 005 先执行，本计划随后把叙事工艺与成果契约一起保留
- **Category**: quality contract / readiness
- **Planned at**: commit `b10506e`, 2026-07-19

## Why this matters

2026-07-18 的首个 deep 真实 shadow run 暴露了现有门的系统性盲区：正文约 4.4 万字，mandatory/scoring、Claim/Action realization、QA 和红队流程均能通过或被关闭，但三个承担核心选择理由的客户可见对象仍未出现：

1. 没有填入具体场景的订单简报；
2. 没有含主标题、核心文案、视觉锚点与多载体适配的内容母版；
3. “创意样片脚本”没有时长、具体画面、旁白/字幕与转场，只是一张六步流程表。

红队准确提出“流程可复制、没有可见证明”，修订又增加约 3,700 字的边界、责任与检查说明，但上述 3/3 缺口不变；Gate 2 仍以“递交前由真实样片证明”关闭当前正文问题。说明当前系统只验证：

```text
Requirement 被回答
Claim / Action 在正文中被蕴含
责任、时点、资源、验收没有越权
```

它没有验证：

```text
评委此刻能否看到一个已填充、项目特定、可操作的成果对象
```

Plan 005 能改善语言温度与叙事张力，但不能创造内容契约；Plan 006 能提供比较框架，但若不新增本计划的结构化 signal，仍可能把“更漂亮的空话”评为进步。本计划把“项目化可见成果”建立为 strategy 拥有、brief 传递、独立 auditor 复核、submission gate 强制的正式契约。

## Current state

- `strategy.json.sections[]` 目前只有 id/n/title/sub/addresses/DecisionJob/narrative 等字段；没有“本章必须让评委看到什么成果”的结构化要求（`prompts/task1_teardown.md:172`、`tests/test_prop_v3.py:175`）。
- `_compile_section` 只输出 `expected_realization_refs` 与 `expected_requirement_refs`（`tools/prop_v3.py:3419-3531`）。
- `task3_section_agent.md` 只要求正文兑现 Requirement、Claim 和 Action；writer hints 也只有 canonical realization。
- `task3c_realization_audit.md` 只判 Claim/Action `entailed|partial|...` 和 Requirement `addressed|partial|...`；流程表只要带责任/时点/验收就可能被判完整。
- `audit_realization` 只核验 canonical/requirement realization（`tools/prop_v3.py:3809-4058`）；authoritative manifest 没有 proof realization。
- `customer_fit` 将 `differentiation`、`reading_efficiency` 默认设为 `not_evaluated`，但 `LEVEL_RANGES.not_evaluated=(20,90)`，最终区间仍可能包含 `competitive`（`tools/prop_v3.py:4068-4255`）。
- Gate 2 没有规则禁止用未来 external artifact 关闭当前 document proof 缺失；`resolved_with_pre_submission_dependency` 可能掩盖正文仍未修复。

## Design decisions

### 1. 不新增第六份 canonical

`proof_requirements` 是“本章如何让评委形成判断”的呈现与兑现契约，不是客户事实、投标人能力或 Evidence。它由 `strategy.json.sections[]` 拥有，与 strategy 当前拥有 Section/DecisionJob 的边界一致。不得建立 `proof-contracts.json`，也不得把实际正文或敏感素材复制进 strategy。

### 2. 区分正文证明与外部递交物

- `surface=document`：必须在技术方案正文中已填充；缺失阻断 `technical_plan_ready` 和 canonical submission。
- `surface=external_attachment`：MP4、样稿文件等外部递交物；在本计划无法核验二进制内容，因此始终作为待人工闭合的 full-bid dependency 进入待办，不能替代同一选择理由所需的 document proof（例如真正分镜），也不使 canonical technical-plan gate 失败。

### 3. 示意提案不是历史能力证据

允许 writer 基于 tender/public/authorized facts 写 `illustrative_proposal`，例如为虚构 fixture 填一张内容母版或分镜；必须明确它是本项目拟议成果，不得借此声称“我方过去做过”或支持 bidder capability Claim。历史能力仍只能由 verified/scoped Evidence 支撑。

### 4. 不设固定亮点数量，不用关键词硬判

硬门检查“被选择的 lead 与高权重 proof obligation 是否有具体证明路径”，而不是检查表格数、字数、标题或出现“样例”两个字。正文完整性由结构化 proof hints + 独立 semantic proof evaluation 确认，工具只验证契约、引用、字段覆盖和 lineage。

### 5. 两类 readiness 不混写

`technical_plan_ready=true` 必须满足全部 required document proof；外部附件 pending 时只允许 `full_bid_submission_ready=false`。任何“以后由附件证明”的决定，都不能把当前缺失的 document proof 标成 resolved。

## Proof requirement contract

在每个 `strategy.sections[]` 中允许新增：

```json
{
  "proof_requirements": [
    {
      "id": "PRF-CH05-STORYBOARD",
      "kind": "storyboard",
      "surface": "document",
      "requiredness": "required",
      "target_refs": ["VP-SCENE-STORY", "REQ-S-PITCH-SAMPLE"],
      "purpose": "让评委直接判断创意是否可拍、产品事实边界是否清楚",
      "required_fields": [
        "timecode",
        "visual_action",
        "voiceover_or_subtitle",
        "fact_boundary",
        "transition"
      ],
      "grounding_modes": ["tender_grounded", "public_grounded", "illustrative_proposal"],
      "truth_boundary": "创意场景是本项目拟议表达；产品名称、参数与效果只使用获授权事实",
      "defer_policy": "blocks_technical_plan"
    }
  ]
}
```

固定枚举：

- `kind`: `filled_template|worked_example|storyboard|sample_copy|visual_system|calculation|operating_scenario|evidence_exhibit`
- `surface`: `document|external_attachment`
- `requiredness`: `required|expected`
- `grounding_modes`: `tender_grounded|public_grounded|authorized_evidence|illustrative_proposal`
- `defer_policy`: `blocks_technical_plan|blocks_full_bid|todo_only`

每种 kind 的最低字段由工具常量拥有，section 可以增加、不能删减：

| kind | 最低 required_fields |
|:---|:---|
| `filled_template` | `scenario, inputs, filled_values, owner, acceptance` |
| `worked_example` | `scenario, decision, application, output, validation` |
| `storyboard` | `timecode, visual_action, voiceover_or_subtitle, fact_boundary, transition` |
| `sample_copy` | `audience, headline, body_or_script, close, fact_boundary` |
| `visual_system` | `visual_anchor, layout_or_components, format_adaptations, vi_boundary` |
| `calculation` | `inputs, formula, assumptions, output, sensitivity` |
| `operating_scenario` | `trigger, roles, sequence, resource, record, acceptance` |
| `evidence_exhibit` | `claim, evidence_scope, source_label, limitation` |

关系规则：

- proof id 在全体 sections 中唯一，建议 `PRF-<CH>-<NAME>`。
- `target_refs` 至少一个，且只能指向本 Section 的 Requirement、selected VP、publishable Claim 或 selected Action。
- 每个 `portfolio_role=lead` 的 VP 必须至少被一个 `required + document + blocks_technical_plan` proof 覆盖。
- `surface=document + required` 必须 `defer_policy=blocks_technical_plan`。
- `surface=external_attachment + required` 必须 `defer_policy=blocks_full_bid`，不能被算作 document proof coverage；本计划只产生非 technical blocker 的 full-bid diagnostic/todo，不声称附件已通过内容核验。
- proof requirement 只保存结构、目的和安全边界，不保存真实案例原文、private 内容、URL、正文草稿或附件路径。

## Commands you will need

| Purpose | Command | Expected on success |
|:---|:---|:---|
| 定向测试 | `python3 -m unittest tests.test_prop_v3.ProposalV3Tests.test_lead_vp_requires_document_proof_contract tests.test_prop_v3.ProposalV3Tests.test_required_document_proof_must_be_filled tests.test_prop_v3.ProposalV3Tests.test_external_attachment_cannot_satisfy_document_proof tests.test_prop_v3.ProposalV3Tests.test_partial_fit_cannot_claim_competitive` | 4 tests pass |
| 全部测试 | `python3 -m unittest discover -s tests` | 全部通过 |
| 契约检索 | `rg -n "proof_requirements|proof_realizations|proof_evaluations" SKILL.md RULES.md DECISIONS.md prompts tools tests` | policy/prompt/tool/test 均有命中 |
| 私密泄漏回归 | `python3 -m unittest tests.test_prop_v3.ProposalV3Tests.test_generation_gate_and_section_context_use_canonical_public_projection` | pass |

## Scope

**In scope**:

- `SKILL.md`, `RULES.md`, `TYPES.md`, `DECISIONS.md`
- `prompts/task1_teardown.md`
- `prompts/task2b_value_selection.md`
- `prompts/task3_section_agent.md`
- `prompts/task3c_realization_audit.md`
- `prompts/task4_redteam.md`
- `tools/prop_v3.py`
- `tests/test_prop_v3.py`

**Out of scope**:

- 生成真实图片、PPT、MP4 或检查二进制附件内容。
- 用正文关键词、字数、表格数或“拟/后补”词频作为单独硬门。
- 改 Evidence/authority 真值规则，或让 illustrative proposal 证明 bidder capability。
- 新建第六 canonical、修改 legacy 引擎、引入第三方依赖。
- 自动宣称 proof 已有差异化；`filled` 只证明“可见且完整”，不证明“独特”。

## Git workflow

- Branch: `advisor/008-projectized-proof-readiness`
- 不 push、不开 PR，除非操作者指示。

## Steps

### Step 0: 先建立会失败的回归测试

在 `tests/test_prop_v3.py` 扩展 `_valid_documents()` 的 CH-01，加入一个最小 `filled_template` proof contract；同步更新现有成功路径的 writer hints 与 semantic audit，使原测试表达新契约。

然后先写并运行以下反例测试，确认修复前至少前三个为红：

1. `test_lead_vp_requires_document_proof_contract`：删除 CH-01 proof，generation gate 必须报 `proof.lead_uncovered`。
2. `test_required_document_proof_must_be_filled`：正文只有“我们将建立订单简报”的流程句，canonical/Requirement 均 entailed/addressed，但没有 proof hint/evaluation；audit 必须 invalid。
3. `test_external_attachment_cannot_satisfy_document_proof`：只有 external MP4 proof，lead document coverage 仍失败。
4. `test_partial_fit_cannot_claim_competitive`：differentiation 或 reading_efficiency 为 `not_evaluated` 时 band 不含 `competitive|strong`。

不得使用当前真实报告作仓库 fixture；它只作外部 shadow 对照，避免把客户内容或内部研判提交进 git。

**Verify before implementation**: 定向测试命令 exit non-zero，失败原因对应缺失功能而非 fixture/schema 拼写错误。

### Step 1: 在 policy 与 Task 1 定义 proof contract

1. `RULES.md` 在“DecisionJob、叙事与正文”后新增“项目化可见成果”小节，写入本计划 Design decisions 和 readiness 区分。
2. `TYPES.md` 为六标型增加非事实先验表，只给 proof kind 建议，不规定固定数量：
   - IMC：filled insight/creative master + sample copy/visual system；
   - 活动：worked experience slice + operating scenario；
   - 数字运营：filled content calendar + sample post + dashboard/optimization example；
   - 政务宣传：narrative sample + content matrix；
   - 影视：storyboard + visual system；
   - 媒介：calculation + monitoring evidence exhibit。
3. `prompts/task1_teardown.md` 的 strategy 示例给 section 加 `proof_requirements:[]`，并要求 Task 1 只提出 candidate proof burden；不要因为缺素材虚构成品。
4. 更新 `SKILL.md` Task 1/2.5/3/4/最终汇报：说明 proof 由 Task 2.5 收敛、Task 3 实现、auditor 复核，required document proof 未满时首句必须写“已生成合规草案，不是竞争稿”。

**Verify**: `rg -n "proof_requirements" RULES.md TYPES.md prompts/task1_teardown.md SKILL.md` 均有命中。

### Step 2: 由 Task 2.5 收敛 proof obligations

修改 `prompts/task2b_value_selection.md`：

- 选择 lead 时必须同时给出至少一个 required document proof contract；没有安全 grounding 时保持 `human_required/gap`，不能把通用流程直接选成已充分证明的 lead。
- supporting VP 只有在它承担高权重评分或选择理由时才需要 required proof；基础合规响应不凑 proof 数量。
- proof 可引用 tender/public/authorized grounding；`illustrative_proposal` 只表示本项目拟议样例，不是 Evidence。
- Task 2.5 通过完整 upsert Section 写入 proof requirements；不得修改 Requirement/VP 核心语义，也不得把正文内容写入 canonical。

在 `tools/prop_v3.py` 的 generation lifecycle validation 增加：schema/enum/最低字段、target relation、proof id 唯一、lead document coverage 和 defer policy diagnostics。owner 为 `task2.5`；缺失 required proof 阻断 `task3/submission`。

迁移兼容：draft stage 允许旧 strategy 暂无 `proof_requirements`；generation/submission 对 selected lead 强制。legacy migration 的 section 默认 `proof_requirements:[]`，不会静默获得 ready 状态。

**Verify**: `test_lead_vp_requires_document_proof_contract` 与 `test_external_attachment_cannot_satisfy_document_proof` 通过。

### Step 3: 安全编译 section brief

1. `_safe_section()` 白名单加入 `proof_requirements`，但先由专用 `_safe_proof_requirement()` 只投影结构字段；禁止未来新增的 raw/private 字段顺带泄漏。
2. `_compile_section()` 输出：

   ```json
   {
     "must_use": {"proof_requirements": []},
     "expected_proof_refs": ["PRF-..."]
   }
   ```

   `must_use.proof_requirements` 可包含本章 document 与 external contract，以便 writer 明确边界；`expected_proof_refs` 只列 required document proof，external attachment 不走 Markdown realization。

3. compile-context 顶层 payload/brief hash 必须包含 `expected_proof_refs`；snapshot/brief lineage 沿用当前机制。
4. 扩展现有 public projection 测试：private Evidence、Role power、capacity 仍不出现；proof truth_boundary 只能是 approved safe wording。

**Verify**: section brief 精确含预期 proof，且私密泄漏回归通过。

### Step 4: writer 输出 proof hints，正文必须填值而非贴标签

修改 `prompts/task3_section_agent.md`：

- 对每个 required document proof 生成一个正文对象；表格/清单可用，但每个 required field 都必须填入当前项目场景的实质内容。
- “我们将建立/后续形成/递交前补充”不能算 filled；缺安全事实时使用被允许的 illustrative proposal 并显式保留 truth boundary，或提交 `missing_context` observation。
- 说明案例 Evidence、示意提案与外部附件三者边界。
- writer hints 新增：

  ```json
  "proof_realizations": [
    {
      "proof_ref": "PRF-CH05-STORYBOARD",
      "heading": "5.3 可拍摄分镜",
      "quote": "正文中唯一定位整张成果对象的短句",
      "field_quotes": [
        {"field": "timecode", "quote": "00:00—00:05"}
      ]
    }
  ]
  ```

`field_quotes` 每个 required field 恰一条；quote 必须能在正文唯一定位。writer 不自判 filled。

若 Plan 005 已加入 `{NARRATIVE_GUIDE}`，原样保留；proof contract 决定“必须交出什么”，narrative guide 决定“怎么写得好”，二者不得互相覆盖。

### Step 5: 独立 auditor 判 filled/partial/missing

修改 `prompts/task3c_realization_audit.md`，新增 `proof_evaluations`：

```json
{
  "proof_ref": "PRF-CH05-STORYBOARD",
  "status": "filled|partial|missing|contradicted|needs_review",
  "field_evidence": [
    {"field": "timecode", "quote": "00:00—00:05", "reason": "给出可执行时间段"}
  ],
  "grounding_modes_observed": ["illustrative_proposal"],
  "reason": "为何该对象已足以被评委检查，或具体缺什么",
  "confidence": "high|medium|low"
}
```

判定口径：

- `filled`：全部 required fields 有实值且彼此组成一个项目特定、可操作的对象；不能只是字段标签、流程名称、责任分工或未来计划。
- `partial`：对象存在但缺字段、仍是泛化文本，或场景/输出未填。
- `missing`：没有对象。
- `contradicted`：与 truth boundary/canonical 冲突或把示意稿冒充历史事实。
- `needs_review`：只有低置信度审美争议；required proof 仍不能通过。

Task 3 auditor 仍不润色、不新增 canonical；proof 缺失按最近 owner 返回 Task 3，grounding 缺口返回 Task 2/Gate 1。

### Step 6: authoritative realization 强制 proof 完整

扩展 `audit_realization()`：

- 读取 brief `expected_proof_refs`、writer `proof_realizations`、semantic `proof_evaluations`。
- 每个 expected proof 恰好一条 hint 和 evaluation；拒绝重复/未知 ref。
- 对 proof anchor 与每个 `field_quote` 复用唯一 quote 定位与 hash lineage。
- required field 集合必须完全覆盖，semantic status 必须 `filled`；`partial/missing/contradicted/needs_review` 均使 manifest invalid。
- authoritative manifest 新增 `proof_realizations`、`missing_expected_proofs`、`invalid_proofs`。
- `_realization_diagnostics()` 在 submission 检查每个 required document proof 的 manifest 状态；缺失报 `proof.realization_missing|proof.realization_invalid` blocker。
- exec-summary 只在全部 required document proof valid 后编译；summary 可以复述已实现 Claim，不新增 proof requirement。
- required external attachment 产生 `proof.external_pending` major diagnostic，`blocks=["full_bid_submission"]` 并进入人工待办；它不改变 canonical technical-plan passed，但最终汇报必须保持 `full_bid_submission_ready=false`，直到独立的人工/未来附件核验闭合。

不要把 model-only “是否有创意”判断变成 deterministic hard gate；硬门只针对结构契约和明确缺字段。独特性仍由 customer-fit/redteam 语义判断。

**Verify**: `test_required_document_proof_must_be_filled` 通过；现有 stale/brief hash/requirement realization 测试仍通过。

### Step 7: 修正 fit 与 Gate 2 的就绪语义

1. `customer_fit()`：
   - required document proof 全部 filled 只能说明 `value_strength/reading_efficiency` 有可评材料，不自动给 `strong/distinctive`；
   - `differentiation` 或 `reading_efficiency` 仍为 `not_evaluated` 时，overall 保持 `partial`，band 上界不得进入 `competitive|strong`（数值上限 74，或等价的不含这些标签实现）；
   - proof blocker 出现时 overall `withheld`。
2. `DECISIONS.md` Gate 2：
   - future external attachment 不能关闭 current document proof；
   - `resolved_with_pre_submission_dependency` 只允许 external/full-bid 依赖，不允许 `blocks_technical_plan`；
   - 只有新 authoritative realization 为 filled 后，document proof challenge 才能 resolved。
3. `prompts/task4_redteam.md`：明确攻击“流程名词替代已填成果”“外部附件替代正文证明”“通用表格无项目值”。
4. `SKILL.md` 最终汇报区分 `technical_plan_ready` 与 `full_bid_submission_ready`，不得以 canonical coverage 冒充竞争稿就绪。

**Verify**: `test_partial_fit_cannot_claim_competitive` 通过。

### Step 8: 回归与 shadow 对比

1. 运行全部单测。
2. 按修订后的 Plan 006 对两个虚构 fixture 重跑 post-change baseline。
3. 与 pre-change 比较：
   - mandatory/真实性/泄漏/预算硬门不得回退；
   - required document proof coverage 从缺失转为 filled；
   - 内容/视频 fixture 至少出现已填内容母版与含 timecode/画面/旁白或字幕的分镜；
   - 若 differentiation 未经语义评估，fit 不再宣称 competitive。
4. 可选 shadow：在仓库外对 2026-07-18 真实标恢复运行，禁止把卷册或客户信息加入 git。原 3/3 缺口必须变为 0/3，或明确以 `technical_plan_ready=false` 停止；不能再“通过但空”。

## Test plan

除 Step 0 四个核心测试外，至少补：

- malformed proof enum / duplicate proof id / unknown target ref 被 generation gate 拒绝；
- required_fields 少于 kind minimum 被拒绝；
- illustrative proposal 不进入 `evidence_refs_presented`、不支持 bidder capability；
- private truth boundary 不进入 section brief；
- proof hint/evaluation 缺失、重复、stale brief、非唯一 field quote 均 invalid；
- expected proof 改动使旧 realization stale；
- expected-only proof 可进入待办但不阻断 technical plan；
- external required proof 不冒充 document proof；
- proof missing 阻止 exec summary 与 submission；
- all proof filled 后现有 canonical/summary/fit 成功路径仍成立；
- `not_evaluated` fit 永不出现 competitive/strong。

所有测试使用完全虚构内容；不得读取 `reports/` 或本机用户上传目录。

## Done criteria

- [ ] strategy section proof contract 有 schema/enum/ref/lead coverage 验证
- [ ] section brief 安全投影 `proof_requirements` 与 `expected_proof_refs`
- [ ] writer hints 和 semantic audit 分别输出 proof realizations/evaluations
- [ ] authoritative manifest 缺/残 required document proof 时 invalid
- [ ] submission/exec-summary 对 required document proof fail-closed
- [ ] illustrative proposal 与 bidder Evidence 边界有测试
- [ ] differentiation/reading 未评价时 fit 不含 competitive/strong
- [ ] DECISIONS/Gate 2 不允许未来附件关闭当前 document proof
- [ ] Plan 006 两份 fixture 已保存 pre/post 对比，质量清单记录 proof coverage
- [ ] `python3 -m unittest discover -s tests` exit 0
- [ ] `git status` 只有 in-scope 文件和计划索引发生预期变化
- [ ] `plans/README.md` 状态行已更新

## STOP conditions

- 需要把 proof 实际内容复制进 strategy，或需要新增第六 canonical 才能继续。
- 任何实现用关键词、字数、表格数、正则命中直接代替 semantic filled 审计。
- illustrative proposal 被当成历史案例、既有能力或 Evidence。
- external attachment 被用于满足 required document proof。
- proof 字段可能把 private/raw Evidence、客户个人偏好、底价或 URL 投影给 writer。
- 为提高“具体性”必须发明产品参数、客户事实、案例结果、KPI 或资源承诺。
- Plan 004 的最终 prompt I/O 契约与本文字段命名冲突；先报告并统一契约，不双轨兼容。
- Plan 006 前置基线尚未实际保存；没有红线就不得开始质量修复。

## Maintenance notes

- proof `filled` 不是“有创意”或“必胜”；它只保证评委看到足以判断的对象。差异化仍需要 blind comparison、红队与真实投标复盘。
- kind minimum fields 应保持小而稳定；新增行业类型优先由 section 的 `required_fields` 扩展，不轻易扩大全局枚举。
- binary attachment verification、视觉文件解析和 PPT/MP4 内容审计是后续独立能力，不塞进本计划。
- 真实 shadow run 的报告和评估记录放仓库外；仓库只保留虚构 fixture 与聚合结论。
- 若实际运行证明 proof contract 过重，优先把 supporting/expected 降为 todo-only，不放宽 lead/required document proof。
