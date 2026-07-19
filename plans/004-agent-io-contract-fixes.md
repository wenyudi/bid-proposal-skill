# Plan 004: 修复 agent I/O 契约断点 — 审计字段无说明、占位变量无来源、坏输入裸崩溃、中文 token 低估

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat b10506e..HEAD -- tools/prop_v3.py prompts/ SKILL.md tests/`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `b10506e`, 2026-07-16

## Why this matters

v3 的可靠性取决于「prompt 告诉子 agent 产出什么」与「工具校验什么」严格一致。当前有四个断点:(1) 每章必经的独立审计 prompt 从未解释 `evidence_refs_presented` 该填什么,而工具对 fact/insight/target 类 Claim **硬性要求**该字段与 brief 白名单相交——照 prompt 行事(留空)会让含事实类主张的章节全部被判 invalid;(2) SKILL.md 让主 agent「替换变量」,但 `{COUNTRY}`、`{EXEC_CHARS}`、`{PER_SECTION_CHARS}` 全仓库无赋值定义,每次 run 现场发明,run 间不可复现;(3) 子 agent 手写的 JSON(changeset/proposal/hints/semantic/judgments)一旦损坏,五个入口以裸 traceback 而非可修复 issue 失败,SKILL.md:122「按工具 issue 修 proposal」的修复循环在此断档;(4) brief 的 token 估算按英文经验 `len//4`,对中文低估约 4 倍,「超限 → blocked → 拆任务」的保护在本 skill 主语种下几乎永不触发,超大 brief 静默流向写作 agent(RULES.md:101 明令禁止静默方向)。

## Current state

相关文件:

- `prompts/task3c_realization_audit.md` — 独立语义审计 prompt;第 53 行输出模板仅给 `"evidence_refs_presented": []`,全文无一句说明取值。
- `tools/prop_v3.py` — 消费端与工具逻辑。
- `SKILL.md` — 主 agent 编排;`prompts/task2_intel.md:5` 用 `{COUNTRY}`,`prompts/task3b_exec_summary.md:6` 用 `{EXEC_CHARS}`,`prompts/task3_section_agent.md:7` 用 `{PER_SECTION_CHARS}`/`{MIN_PARAGRAPHS}`;SKILL.md:159 只说「按 profiles.json 计算建议字数,替换 `{BRIEF_PATH}` 等变量」,无公式。
- `profiles.json` — 各模式的 `max_chars`(15000/28000/50000)、`min_chapters`(6/8/11)、`min_paragraphs`(4/5/6)、`v3_context_token_budget`(16000/24000/36000)。

断点 1 的消费端(`tools/prop_v3.py:3832-3835` 与 `3943-3952`):

```python
    public_evidence_by_target = {}
    for item in _as_list((brief.get("must_use") or {}).get("public_evidence")):
        if isinstance(item, dict) and item.get("target_ref") and item.get("source_ref"):
            public_evidence_by_target.setdefault(item.get("target_ref"), set()).add(item.get("source_ref"))
    ...
        presented_evidence = set(_ref_list(evaluation, "evidence_refs_presented"))
        unapproved_evidence = presented_evidence - public_evidence_by_target.get(ref, set())
        if unapproved_evidence:
            issues.append("%s presents Evidence outside its public scoped brief: %s" % (...))
        if (registry[ref]["type"] == "claim"
                and canonical.get("content_kind") in ("fact", "insight", "target")
                and semantic_status == "entailed"
                and not presented_evidence.intersection(public_evidence_by_target.get(ref, set()))):
            issues.append("%s factual/insight/target realization presents no approved scoped Evidence" % ref)
```

注意:brief 的 `public_evidence[].source_ref` 是 **Evidence 的 EV-\* id**(`_public_projection` 在 `tools/prop_v3.py:3162` 把 `evidence.get("id")` 命名为投影的 `source_ref`),不是 SRC-\* 也不是 EL-\*。

断点 3 的五个无保护入口(`tools/prop_v3.py`,均直接 `_read_json`,坏 JSON 异常穿透到 CLI 兜底 traceback):
- `apply_changeset`:2758(changeset 文件)
- `promote_research`:2877-2878(两份 proposal)
- `audit_realization`:3819(hints)、3825(brief)、3826(semantic)
- `customer_fit`:4144(judgments)
- `freeze_snapshot`:3149(已存在 snapshot)

断点 4(`tools/prop_v3.py:3686`):

```python
    estimated = max(1, len(_canonical_json(brief)) // 4)
```

`_canonical_json` 用 `ensure_ascii=False`(151-152 行),中文 1 字符≈1 token,`//4` 低估约 4 倍;默认预算 24000 实际放行 ~96k token 的 brief。

另一处小崩溃(同批修复):`tools/prop_v3.py:239-249` `_evidence_is_current` 中 `calendar.monthrange(year, month)`(243 行)在 `try:`(244 行)之外,`valid_until` 形如 `"2026-13"`(有月无日、月份非法)时抛 `IllegalMonthError` 崩溃;而 `"2026-13-01"` 会被 try 内 `datetime.date` 正确按 False 处理,行为不对称。

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| 全部测试 | `python3 -m unittest discover -s tests` | 全部通过 |
| 语法检查 | `python3 -m py_compile tools/prop_v3.py` | exit 0 |

## Scope

**In scope**:
- `prompts/task3c_realization_audit.md`(补字段说明)
- `SKILL.md`(补变量赋值表与 Task 1 二次失败出路)
- `tools/prop_v3.py`(`_read_json_or_issue` helper、`_evidence_is_current`、token 估算)
- `tests/test_prop_v3.py`(追加测试)

**Out of scope**:
- `audit_realization` 的判定语义(哪些 status 算通过)不变。
- 其他 prompt 文件;`prompts/legacy/`。
- `profiles.json` 数值不改。
- brief 的 must_use 内容与投影规则(SEC-01 另行处理,见 plans/README.md backlog)。

## Git workflow

- Branch: `advisor/004-agent-io-contract-fixes`
- 不 push、不开 PR,除非操作者指示。

## Steps

### Step 1: task3c prompt 补 evidence_refs_presented 说明

在 `prompts/task3c_realization_audit.md` 的输出说明区(第 53 行模板附近,「每个 expected Claim/Action 和 Requirement ref 恰好一条对应 evaluation」段落处)加入一条规则,措辞要点:

- 对每条 evaluation,把**正文实际呈现了的证据**对应的 brief `must_use.public_evidence[].source_ref`(EV-\* 形态,且该条目的 `target_ref` 等于本 evaluation 的 `canonical_ref`)列入 `evidence_refs_presented`;正文未呈现任何证据时留空数组。
- 明确告知:fact/insight/target 类 Claim 判 `entailed` 时该数组必须至少含一个上述 `source_ref`,否则工具会判 invalid;不得填 EL-\*、SRC-\* 或 brief 外的任何 id。

**Verify**: `grep -n "source_ref" prompts/task3c_realization_audit.md` → 有命中;`grep -c "evidence_refs_presented" prompts/task3c_realization_audit.md` → ≥2(模板 + 说明)。

### Step 2: SKILL.md 补变量赋值表与 Task 1 兜底

1. 在 SKILL.md「参数」节之后(第 55 行 `$PY` 段附近)加一小节「prompt 变量」,用表格明确每个替换变量的来源(执行者按下述公式写入,勿改动数值来源):
   - `{LANG}`/`{MODE}`/`{TMPDIR}`/`{NARRATIVE}`:运行参数。
   - `{CURRENT_YEAR}`:运行时系统年份。
   - `{COUNTRY}`:默认「中国大陆」,标书明确境外项目时按标书。
   - `{MIN_PARAGRAPHS}`:profiles.json 当前模式的 `min_paragraphs`。
   - `{PER_SECTION_CHARS}`:`round(max_chars / 正式章节数)`(max_chars 取 profiles.json 当前模式;正式章节数 = strategy.sections 长度)。
   - `{EXEC_CHARS}`:`round(max_chars * 0.06)`,且不低于 800(约一页)。
   - `{SEMANTIC_OUTPUT}`:`$TMPDIR/derived/realization/section-N.semantic.json`(与 SKILL.md:163 的现有命名一致)。
2. 在 SKILL.md:87「失败只重派 Task 1 一次」句后补一句出路:两次失败即停止 run,向用户报告两轮 diagnostics 与最小复现输入,不得手改 canonical 或降级为 legacy。

**Verify**: `grep -n "PER_SECTION_CHARS" SKILL.md` → 有命中;`grep -n "重派 Task 1" SKILL.md` 所在段含两次失败的出路描述。

### Step 3: 健壮 JSON 读取

在 `tools/prop_v3.py` 增加 helper(放在 `_read_json` 定义后):

```python
def _read_json_or_issue(path, label):
    try:
        return _read_json(path), None
    except (OSError, ValueError) as exc:
        return None, {"passed": False, "issues": ["%s unreadable: %s" % (label, exc)]}
```

五个入口改用它并在 issue 非空时直接 return issue(逐一:`apply_changeset:2758`、`promote_research:2877-2878`、`audit_realization:3819/3825/3826`、`customer_fit:4144`、`freeze_snapshot:3149`——freeze 的场景是已存在 snapshot 损坏,按 issue 返回而非崩溃)。注意 `json.JSONDecodeError` 是 `ValueError` 子类,无需单列。

**Verify**: 新增测试(Step 5)转绿;`python3 -m py_compile tools/prop_v3.py` exit 0。

### Step 4: 修 _evidence_is_current 与 token 估算

1. `tools/prop_v3.py:239-249`:把 `month`/`day` 解析与 `calendar.monthrange` 一并移入 `try` 块(与现有 `except ValueError: return False` 合用),使 `"2026-13"` 与 `"2026-13-01"` 行为一致(均按 False,即不 current)。
2. `tools/prop_v3.py:3686` 及同函数内第二次估算处(3692-3694):抽出 helper `_estimate_tokens(text)`,按字符分类加权:CJK 及全角字符计 1,其余计 0.25(`len(ascii_part)//4` 等价),向上取整。两处调用统一走 helper。**注意**:该改动会让中文 brief 的估算值上升约 4 倍,可能使存量流程在默认 24000 预算下触发 blocked——这是预期行为(fail-loud);profiles.json 已提供 `v3_context_token_budget` 供各模式显式配置,不要为了「让测试过」而调低权重。

**Verify**: Step 5 测试转绿。

### Step 5: 测试

在 `tests/test_prop_v3.py` 追加(模仿现有测试的 state 构造):
1. `apply_changeset` 传入一个内容为 `{invalid` 的文件路径 → 返回 `passed=False` 且 issues 含 "unreadable",不抛异常。
2. `audit_realization` 的 hints 路径指向坏 JSON → 同上。
3. `_evidence_is_current({"status": "active", "valid_until": "2026-13"})` → 返回 False,不抛异常(按该函数实际签名调用)。
4. `_estimate_tokens("中文" * 100)` ≥ 200 的量级断言,与 `_estimate_tokens("a" * 400)` ≈ 100 对照。

**Verify**: `python3 -m unittest discover -s tests` → 全部通过,总数比基线多 ≥4。

## Test plan

见 Step 5;结构模式参照 `tests/test_prop_v3.py` 现有 `apply_changeset` / `audit_realization` 测试的 fixture 构造。prompt/SKILL 的文字改动无自动测试,以 grep 验证 + 人工读一遍为准。

## Done criteria

- [ ] `python3 -m unittest discover -s tests` exit 0,总数比基线多 ≥4
- [ ] `python3 -m py_compile tools/prop_v3.py` exit 0
- [ ] `grep -c "evidence_refs_presented" prompts/task3c_realization_audit.md` ≥ 2
- [ ] `grep -n "PER_SECTION_CHARS" SKILL.md` 有命中
- [ ] 五个入口不再直接 `_read_json`(`grep -n "_read_json(" tools/prop_v3.py` 核对 2758/2877/3819/3825/3826/4144/3149 原位置均已改走 helper;其余调用点不动)
- [ ] `git status` 只有 in-scope 文件被修改
- [ ] `plans/README.md` 状态行已更新

## STOP conditions

- 摘录与现库不符。
- Step 1 中发现 brief `public_evidence` 的实际字段名不是 `source_ref`(对照 `tools/prop_v3.py:3156-3172` `_public_projection`)— 以代码为准修正 prompt 措辞,若代码里也不一致则报告后停。
- Step 4.2 导致大量现有测试因 blocked 失败(说明测试 fixture 的 brief 超新估算)— 优先在测试 fixture 显式提高 token_budget 参数,而不是回调权重;若仍纠缠,报告后停。

## Maintenance notes

- 任何未来给子 agent prompt 增加输出字段时,必须同步写「取值来源 + 工具校验后果」两句——CONTRACT-01 的教训。
- `{EXEC_CHARS}` 的 0.06 系数是建议默认,维护者可在 SKILL.md 调整;重要的是有唯一明确定义。
- 显式遗留(见 plans/README.md backlog):`-auto` 模式下 VP/量化 Claim 不随 Gate assume 降级导致的 generation 死锁(CONTRACT-02)需要产品决策(自动降级会连带组合结构),不在本计划内。
