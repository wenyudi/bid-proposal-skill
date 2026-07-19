# Plan 005: 把叙事工艺送到写作 agent 手里 — 打通 TYPES.md 叙事库到 Task 3/3.5 的断链

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat b10506e..HEAD -- prompts/ SKILL.md TYPES.md`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2(对「方案质量上限」是第一杠杆;不阻断流程,故列 P2)
- **Effort**: M
- **Risk**: LOW(纯 prompt/文档改动,不碰工具与状态)
- **Depends on**: none
- **Category**: direction
- **Planned at**: commit `b10506e`, 2026-07-16

## Why this matters

本仓库的合规与真实性护栏非常完备,但「写得好」的工艺指导存在断链:TYPES.md 用约 54 行(N1-N4 表格)精心定义了四种叙事策略的**章内写法、语言温度、风险禁忌**,而这些内容只有 Task 1 在选型时读到。真正写正文的 Task 3 章节 agent 拿到的叙事信息只有:brief 里 `strategy.narrative` 的深拷贝(mode 一个词 + rationale + through_line,见 `tools/prop_v3.py:3351`)加上 task3 prompt 第 27 行把四套策略压缩成的一行话。写作 agent 的 prompt 中约束/禁令与「怎么写好」的比例约为 5:1,且没有任何范文。结果可预期:方案**合规但平**——每个评分点都答了,但叙事张力、认知增量、画面感这些拉开评委体感差距的东西没有稳定供给。本计划用纯 prompt 手段接通断链:主 agent 派章节/摘要 agent 时,把选定叙事的完整工艺段注入 prompt。

## Current state

相关文件:

- `TYPES.md:145-199` — 叙事策略库:N1 `logic` / N2 `story` / N3 `vision` / N4 `evidence` 四张表,每张含「一句话内核 / 适用信号 / 章内写法 / 语言温度 / 风险禁忌」;另有「选择决策」段(191-199)。这是仓库里最完整的写作工艺资产。
- `prompts/task3_section_agent.md` — 章节写作 prompt(90 行)。第 27 行是写作 agent 得到的全部叙事指导:

  ```
  - narrative 只改变开篇、材料顺序、语言温度与节奏：logic 重论证链，story 用真实客户/用户场景，vision 重合同期路线，evidence 重口径与依据。报价/合规/资质固定 logic/evidence。
  ```

- `prompts/task3b_exec_summary.md:20` — 摘要 prompt 同样只有一句「叙事语言与 `common.narrative` 同频」。
- `SKILL.md:159` — 派章节 agent 的指令:「按 profiles.json 计算建议字数,用 `prompts/task3_section_agent.md` 替换 `{BRIEF_PATH}` 等变量;并行派章节 agent」。
- `tools/prop_v3.py:3351` — brief 的 `common.narrative` 只是 `copy.deepcopy(strategy.get("narrative") or {})`,即 `{"mode", "secondary", "rationale", "through_line"}` 四字段。
- 约束:RULES.md §7「narrative 有 presentation authority,没有 semantic authority」「报价/合规/资质固定 logic/evidence」;正文硬禁「叙事手法自述」(task3:33)。本计划注入的是**工艺指导**,不改变这些边界。

设计决策(本计划采用方案 B):
- 方案 A(改 `compile-context` 把工艺文本编进 brief)被否:brief 是数据契约,混入长文档会撑大 token 估算、污染 hash 语义,且工具需要解析 TYPES.md。
- 方案 B(主 agent 派发时做 prompt 变量替换)成本最低、与现有「替换 `{BRIEF_PATH}` 等变量」机制同构、工艺文本保持 TYPES.md 单一事实源。

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| 全部测试 | `python3 -m unittest discover -s tests` | 全部通过(本计划不应改变任何测试结果) |
| 变量核对 | `grep -n "NARRATIVE_GUIDE" prompts/ SKILL.md -r` | 见各 step |

## Scope

**In scope**:
- `prompts/task3_section_agent.md`
- `prompts/task3b_exec_summary.md`
- `SKILL.md`(第 5、6 节的派发指令;若 Plan 004 已建「prompt 变量」表,在同表追加)
- `TYPES.md`(仅允许加锚点性小标题,不改变内容语义)

**Out of scope**:
- `tools/prop_v3.py`、`tools/prop_tools.py` — 不改任何代码。
- `RULES.md` 的叙事边界、task3 的「正文硬禁」清单 — 不放宽任何禁令。
- `prompts/task4_redteam.md`、`prompts/legacy/` — 红队与旧链不需要工艺注入。
- 新增范文/样例文件 — 显式遗留(见 Maintenance notes)。

## Git workflow

- Branch: `advisor/005-writer-craft-context`
- 不 push、不开 PR,除非操作者指示。

## Steps

### Step 1: task3_section_agent.md 增加 {NARRATIVE_GUIDE} 注入位

在「阅读体验」节(第 21-29 行)的 narrative 行(第 27 行)之后插入一个小节:

```markdown
## 本章叙事工艺

{NARRATIVE_GUIDE}

以上工艺只约束表达:开篇方式、材料顺序、语言温度、节奏与「风险禁忌」。它不得改变 Requirement 响应、Claim 语义/scope/承诺强度、Evidence 边界或 Action 责任;与 brief/硬禁冲突时以 brief 与硬禁为准。报价、合规、资质内容无论主叙事为何,一律 logic/evidence 呈现。不得在正文自述叙事手法。
```

保留第 27 行原句不动(作为无注入时的兜底)。

**Verify**: `grep -n "{NARRATIVE_GUIDE}" prompts/task3_section_agent.md` → 恰 1 处命中。

### Step 2: task3b_exec_summary.md 同样注入

在「结构」节之前(第 11 行附近)插入相同小节(措辞可减半:摘要只需「语言温度 + 一句话内核 + 风险禁忌」三要素的提醒,同样以 `{NARRATIVE_GUIDE}` 占位)。

**Verify**: `grep -n "{NARRATIVE_GUIDE}" prompts/task3b_exec_summary.md` → 恰 1 处命中。

### Step 3: SKILL.md 定义 {NARRATIVE_GUIDE} 的取值

在 SKILL.md 第 5 节(Task 3)第 159 行的派发指令处,把「替换 `{BRIEF_PATH}` 等变量」扩写为明确清单,新增:

- `{NARRATIVE_GUIDE}`:从 TYPES.md 叙事策略库中**逐字复制**当前 `strategy.narrative.mode` 对应的整张表(N1/N2/N3/N4 之一,含一句话内核、适用信号、章内写法、语言温度、风险禁忌五行);`mode=custom` 时改为复制 strategy.narrative.rationale 并附 TYPES.md:199「主叙事全案唯一」铁律句;若章节 `narrative_role` 或 RULES 规定该章固定 logic/evidence(报价/合规/资质),则按固定模式取表。secondary 存在时在表后附一行「辅助叙事:<secondary> 仅用于 <适用章节>」。

第 6 节(Task 3.5)派发处加同样一句(引用同一定义)。

**Verify**: `grep -n "NARRATIVE_GUIDE" SKILL.md` → ≥2 处命中(定义 + Task 3.5 引用)。

### Step 4: TYPES.md 加稳定锚点

给 N1-N4 四个小节标题确认现有形态(`### N1 \`logic\` — 逻辑征服` 等)已可被主 agent 按 mode 定位;若小节标题不含反引号 mode 名,补上(只改标题行,不改表格内容)。

**Verify**: `grep -nE '^### N[1-4] .(logic|story|vision|evidence).' TYPES.md` → 4 处命中。

### Step 5: 一致性回归

**Verify**:
- `python3 -m unittest discover -s tests` → 全部通过(本计划不触碰代码,结果应与基线一致)。
- 人工检查:通读修改后的 task3_section_agent.md 全文,确认新增小节没有与「正文硬禁」清单(第 31-38 行)冲突的表述。

## Test plan

本计划为纯 prompt/文档改动,无代码测试。验证手段:
- 各 step 的 grep 断言(占位符存在且唯一)。
- 回归:`python3 -m unittest discover -s tests` 结果与基线一致。
- 建议(非阻塞):维护者在下一次真实 run 中对比同一标书注入前后的任一章初稿,观察开篇、语言温度与「认知增量」的差异,并把结论记入 `.scratch/` 校准笔记。

## Done criteria

- [ ] `grep -c "{NARRATIVE_GUIDE}" prompts/task3_section_agent.md` = 1
- [ ] `grep -c "{NARRATIVE_GUIDE}" prompts/task3b_exec_summary.md` = 1
- [ ] `grep -n "NARRATIVE_GUIDE" SKILL.md` ≥ 2 处,含取值定义(逐字复制 TYPES.md 对应表)
- [ ] `python3 -m unittest discover -s tests` exit 0
- [ ] `git status` 只有 in-scope 文件被修改
- [ ] `plans/README.md` 状态行已更新

## STOP conditions

- 摘录与现库不符(尤其 task3 第 27 行、TYPES.md 小节标题形态)。
- 发现 SKILL.md 已存在其他机制向写作 agent 传递叙事工艺(说明断链判断失效)— 报告后停。
- 新增文本与「正文硬禁」或 RULES §7 出现无法调和的措辞冲突。

## Maintenance notes

- 这是「质量上限」轨道的第一步。显式遗留给后续计划/维护者:
  1. **范文机制**:当前零 exemplar。建议未来在 `casebase/` 或新目录放 1-2 段脱敏「好段落」(每叙事一段),作为 `{NARRATIVE_GUIDE}` 的附加注入;需先解决样例的授权与虚构化(与 CONTRIBUTING「示例必须虚构」一致)。
  2. **brief `may_use` 恒为空**(`tools/prop_v3.py:3527`):若未来想经 brief 传工艺文本,可用 may_use 通道并配合 token 剪裁语义,那时才需要动工具。
- 审阅者应核对:注入文本是否可能被写作 agent 误当成「可写进正文的内容」——Step 1 的边界句是防线,措辞不可删。
- TYPES.md 是工艺唯一事实源;未来修订叙事表时无需改任何 prompt。
