# Plan 002: 补齐最终门盲区 — 人工待办漏扫卷首占位符、strategy 章节号零校验

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat b10506e..HEAD -- tools/prop_tools.py tests/`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none(与 001 同文件不同函数;若与 001 同时执行,先合并 001)
- **Category**: bug
- **Planned at**: commit `b10506e`, 2026-07-16

## Why this matters

`_人工待办.md` 是用户递交前的最后清单,「待办清零」是定稿信号。但装配器写入卷首的**投标人全称盖章**与**投标日期**占位符,以及方案综述里的任何【占位】,永远不会出现在待办里——因为占位符扫描只遍历正文章节。这两项恰是废标级格式项。另外 `check-strategy` 对 `sections[].n` 零校验:n 缺失时装配阶段以裸 TypeError 崩溃(而非可修复 issue),n 重复时合规对照、待办、自评的章节归属**静默错位**。

## Current state

相关文件:

- `tools/prop_tools.py` — `human_todo`(约 750-900 行)、`split_chapters`(667-675)、装配头部写入(444-452)、`check_strategy` 的 sections 校验(1318-1334)、`toc_label`(128-133)。
- `tests/test_prop_tools.py` — 现有测试风格参照。

问题 1 — 占位符扫描漏卷首与综述。装配头部(`tools/prop_tools.py:447-448`)写入:

```python
    info_rows.append(f"{L['bidder']}：{L['tbd_bidder']}")
    info_rows.append(f"{L['bid_date']}：{L['tbd_date']}")
```

其中 `tbd_bidder`/`tbd_date` 的文案是 `【待填写：投标人全称并加盖公章】` 与 `【待填写】`(见同文件 L 字典定义,zh 分支)。而 `human_todo` 的占位符扫描(约 782-798 行)只遍历 `split_chapters(report)`:

```python
def split_chapters(report):
    """返回 [(chapter_index_1based, text)]，按 ## 汉字、/ ## N. 切分。"""
    pat = re.compile(r'^## (?:[一二三四五六七八九十]+、|\d+\. ).+$', re.MULTILINE)
    starts = [m.start() for m in pat.finditer(report)]
```

第一个正式章标题之前的一切(项目信息头、目录、应标对照表)与 `## 方案综述`(不匹配该模式)都不在扫描范围。

问题 2 — `check_strategy` 的 sections 循环(`tools/prop_tools.py:1322-1332`)只校验 `narrative_role` 与 `addresses`,对 `n` 的存在性/整数性/唯一性零校验。下游 `toc_label`(128-133):

```python
def toc_label(lang, n, title):
    if lang == 'zh':
        num = CHINESE_NUMERALS[n - 1] if n <= len(CHINESE_NUMERALS) else str(n)
```

`n=None` 时 `n - 1` 抛 TypeError,穿透到 CLI 兜底打印 UNEXPECTED ERROR;n 重复时 `split_chapters` 按出现顺序 1..N 编号,与 `sections` 的 n 对位错乱但无任何报错。

仓库约定:纯标准库;错误以 `{"passed": bool, "issues": [...]}` 返回;测试用 `unittest` + tempfile。

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| 全部测试 | `python3 -m unittest discover -s tests` | 全部通过 |
| 语法检查 | `python3 -m py_compile tools/prop_tools.py` | exit 0 |

## Scope

**In scope**:
- `tools/prop_tools.py`(仅 `human_todo` 与 `check_strategy` 两个函数内部)
- `tests/test_prop_tools.py`(追加测试)

**Out of scope**:
- `split_chapters` 的切分规则本身(多处依赖,改动波及自评/合规;卷首扫描用独立逻辑实现)。
- `tools/prop_v3.py`、`prompts/`、装配头部文案(占位符文案是设计要求,不改)。

## Git workflow

- Branch: `advisor/002-final-gate-integrity`
- 提交说明用中文一句话概括;不 push、不开 PR,除非操作者指示。

## Steps

### Step 1: 测试先行

在 `tests/test_prop_tools.py` 追加:
1. `human_todo` 测试:构造含卷首 `投标人：【待填写：投标人全称并加盖公章】` + `## 方案综述`(内含一个 `【占位】`)+ 一个正式章的 report,断言输出的待办 Markdown 包含这两处占位符条目且归类为阻断区(blocking)。
2. `check_strategy` 测试:sections 中一项缺 `n`、另一项与他项 `n` 重复,断言 issues 各含一条(如 `sections[0] 缺 n`、`sections[2].n 重复`),`passed=False`。

**Verify**: `python3 -m unittest tests.test_prop_tools -v` → 新测试红,旧测试绿。

### Step 2: human_todo 增加卷首与综述扫描

在 `human_todo` 的占位符收集逻辑处(约 782 行前):对 `report[:第一个正式章 start]`(用与 `split_chapters` 相同的正则找第一个 start;找不到则整篇)单独运行既有 `PLACEHOLDER_RE`,命中项以章节标签「卷首/方案综述」加入 blocking 列表(卷首占位符一律按废标风险处理,不做评分权重归类)。

**Verify**: Step 1 的 human_todo 测试转绿。

### Step 3: check_strategy 校验 n

在 sections 循环(1322-1332)内追加:`n` 必须存在且为正整数,否则 issue `sections[i] 缺 n 或 n 非正整数`;循环外收集所有 n,重复时 issue 列出重复值。均为普通 issue(进入 `passed=False`),不抛异常。

**Verify**: Step 1 的 check_strategy 测试转绿;`python3 -m unittest discover -s tests` 全绿。

## Test plan

见 Step 1;结构模式参照 `tests/test_prop_tools.py` 现有 human_todo/check_strategy 测试(如有)或相邻测试的 tempfile 用法。完成后总测试数比基线多 ≥2。

## Done criteria

- [ ] `python3 -m unittest discover -s tests` exit 0
- [ ] `python3 -m py_compile tools/prop_tools.py` exit 0
- [ ] 构造性验证:对含卷首占位符的样例 report 运行 `human_todo`,输出文件包含「投标人全称」相关待办
- [ ] `git status` 只有 in-scope 文件被修改
- [ ] `plans/README.md` 状态行已更新

## STOP conditions

- 摘录与现库不符(先跑 drift check)。
- `PLACEHOLDER_RE` 常量不存在或占位符文案与摘录不符 — 报告实际形态后停。
- 修复需要改 `split_chapters` 或装配函数。

## Maintenance notes

- 未来若装配头部新增其他占位符字段,卷首扫描自动覆盖(按 PLACEHOLDER_RE);但若新增「非【】形态」的待填项,需同步扩展 PLACEHOLDER_RE。
- 审阅者核对:n 校验只加 issue、不改变既有合法 strategy 的通过状态(n 连续性不做要求,只查存在/正整数/唯一)。
