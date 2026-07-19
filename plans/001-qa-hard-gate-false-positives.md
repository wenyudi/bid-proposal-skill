# Plan 001: 消除 qa-proposal 硬门误报,并建立正反语料回归测试

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
- **Effort**: M
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `b10506e`, 2026-07-16

## Why this matters

`qa-proposal` 是每份技术标递交前必经的最后硬门:任何非 warning 检查失败,主 agent 按 SKILL.md:198 必须「修复并重新装配」。当前有三处检查会把**合法正文**判为硬失败(内部 ID 泄漏、汉字编号、内部信息泄漏),而正文并无问题可修——流程会在「误报 → 改写合法文字 → 仍误报」中死循环,或迫使 agent 扭曲正文来绕过正则。同时 v3 精确 ID 检查在状态加载异常时被静默降级为「全部通过」,在最需要它的损坏场景下失效。这些检查本身价值很高(真实泄漏主要靠它们拦截),需要的是提高精度并用正反语料钉住行为,不是删除。

## Current state

相关文件:

- `tools/prop_tools.py` — 装配/合规/QA CLI;`qa_proposal` 函数内含全部涉事检查(约 1040–1212 行)。
- `tests/test_prop_tools.py` — 现有 16 个测试,风格为 `unittest.TestCase` + `tempfile` 目录,直接调用 Python 函数(不走 CLI)。QA 检查目前只有 `scope_guard` 与 v3 `no_id_leak` 的单向正例,零反例语料。

问题 1 — 内部 ID 检查(`tools/prop_tools.py:1110-1146`):

```python
    id_pattern = (r'(?<![A-Za-z0-9])(?:[SMD]\d{1,2}|'
                  r'(?:REQ|ROLE|NEED|CRIT|VP|CL|MET|EL|EV|DR|DA|RES|DEP|AC|DJ|CH|'
                  r'GATE|SRC|RN|NC|RC)-[A-Z0-9_.-]+)'
                  r'(?![A-Za-z0-9])')
    leak = re.findall(id_pattern, report, re.IGNORECASE)
```

`re.IGNORECASE` 使字符类同时匹配小写,正文出现 `role-based`、`need-driven`、`AC-3 音频`、`对象存储 S3`、`M2 芯片` 等常见词即命中;中文字符不属于 `[A-Za-z0-9]`,边界断言拦不住。且 1140-1141 行:

```python
        except Exception:
            exact_ids = set()
```

v3 state 加载失败时,精确 ID 检查静默变为空集(即「没有泄漏」),无任何提示。检查结果在 1145 行 `"warning": False` — 命中即硬失败。

问题 2 — 子节汉字编号检查(`tools/prop_tools.py:1105-1108`):

```python
    zh_sub = [i + 1 for i, l in enumerate(lines) if re.match(r'^### [一二三四五六七八九十]', l)]
```

只看子节标题第一个字。`### 一体化传播平台`、`### 一站式服务`、`### 三维可视化` 等政企标书常见标题全部误判为「用汉字编号子节」,且该检查无 `warning` 字段 → 参与 `hard_fail`(见 1206-1209 行:`hard_fail = any(not v.get('passed', True) and not v.get('warning', False) ...)`)。

问题 3 — 内部信息泄漏模式(`tools/prop_tools.py:1074-1086`):

```python
        (r'生成时间\s*[:：]', '生成时间戳'),
        ...
        (r'https?://', 'URL（投标文件不带网址书目，来源改行内标注）'),
        (r'\b(?:DecisionJob|ValueProposition|customer[- ]fit|canonical|realization manifest)\b',
         'v3 内部模型或审计术语'),
    ]:
        if re.search(pat, report, re.MULTILINE | re.IGNORECASE):
            leaks.append(why)
```

`生成时间\s*[:：]` 无锚定:数据平台章节写「日报生成时间：每日 9:00」即硬失败。`canonical`(IGNORECASE)在混排技术正文里是普通词。URL 模式本身合理(投标文件确实不应含 URL),但命中时不输出行号,定位成本高。

问题 4(低优先,顺手修)— `tools/prop_tools.py:1201-1204`:`'排除项' in report` 子串匹配,正文「已将风险排除项逐条封闭」误命中(仅 warning 级,噪音);`_clean_md`(185-198 行)删除 `|` 但保留表格分隔行的 `:---` 残留,每张表虚增少量字数。

仓库约定:纯标准库、Python 3.8+;测试用 `unittest`;错误以 `{"passed": bool, "issues"/"checks": ...}` 结构返回而非异常。

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| 全部测试 | `python3 -m unittest discover -s tests` | 全部通过(基线 40 个,完成后 ≥44 个) |
| 语法检查 | `python3 -m py_compile tools/prop_tools.py tools/prop_v3.py` | exit 0,无输出 |
| 单独跑新测试 | `python3 -m unittest tests.test_qa_gates -v` | 全部通过 |

## Scope

**In scope**(只允许修改这些文件):
- `tools/prop_tools.py`(仅 `qa_proposal`、`_clean_md` 两个函数内部)
- `tests/test_qa_gates.py`(新建)

**Out of scope**(不要动,即使看起来相关):
- `tools/prop_v3.py` — v3 引擎,其 `load_state` 的行为不改;本计划只改 QA 侧对加载失败的呈现。
- `prompts/`、`SKILL.md`、`RULES.md` — 正文禁项政策不变,只修检测精度。
- `no_private_raw_leak`、`scope_guard`、`buyer_focus` 等其他检查 — 未发现误报,不动。

## Git workflow

- Branch: `advisor/001-qa-gate-false-positives`
- Commit 风格参照仓库(中文一句话概括行为变化,如 `git log` 中「v3.0.0：默认启用客户价值、交付与兑现审计底座」)。
- 不要 push、不要开 PR,除非操作者明确指示。

## Steps

### Step 1: 建立正反语料测试(先写反例,预期先红)

新建 `tests/test_qa_gates.py`,结构仿照 `tests/test_prop_tools.py`(unittest + tempfile 写入 report 文件后调用 `prop_tools.qa_proposal`)。最小 report 骨架:一个 `## 一、项目理解` 章 + 若干段落,保证 `structure`/`chapter_count` 之外的检查可独立观察(qa_proposal 返回 `{"passed": ..., "checks": {...}}`,断言只看目标 check 键,不看整体 passed)。

反例语料(合法正文,断言对应 check 的 `passed=True`,当前实现下会失败):
- `no_id_leak`:含 `role-based 权限模型`、`need-driven 运营`、`AC-3 音频标准`、`对象存储 S3`、`M2 芯片`。
- `subsection_numbering`:含 `### 一体化传播平台`、`### 三维可视化大屏`。
- `no_internal_leak`:含 `日报生成时间：每日 9:00`、`平台支持 canonical 数据格式`(英文词混排)。
- `no_sales_cta`:含 `已将风险排除项逐条封闭管理`。

正例语料(真实泄漏,断言 `passed=False`,当前实现应已通过,防修复矫枉过正):
- `no_id_leak`:含 `REQ-M-QUALIFICATION`、`VP-CLOSED-LOOP`、`GATE-CAPABILITY-TEAM`、独立成词的 `S1`(legacy 编号,前后空格)。
- `subsection_numbering`:含 `### 一、核心主张`、`### 二. 执行路径`。
- `no_internal_leak`:含 `> **投标方案** · 生成时间：2026-07-01`、`详见 https://example.com/report`、`叙事：story`。

**Verify**: `python3 -m unittest tests.test_qa_gates -v` → 反例测试失败(红)、正例测试通过。这是预期状态,证明语料钉住了现存 bug。

### Step 2: 修复 no_id_leak

在 `tools/prop_tools.py:1110-1115`:
- 去掉 `re.IGNORECASE`,改为大小写敏感(canonical ID 约定全大写,见 `prompts/task1_teardown.md` 的 ID 前缀表)。
- legacy `[SMD]\d{1,2}` 单独成模式并要求前后为空白、标点或行首尾(收紧为独立 token,排除 `S3`/`M2` 这类前后紧贴中文的场景可保留——但必须与正例语料中独立 `S1` 的检出兼容;若两者冲突,以「典型 legacy 自评编号出现在括号或行尾」为准,允许 `S3 对象存储` 不命中)。
- 1140-1141 行 `except Exception` 分支:改为在 `checks['no_id_leak']` 结果中加入 `"degraded": True` 与提示文案,并让该检查 `passed=False`(fail-closed,但给出「state 加载失败」的明确原因),不再静默清空。

**Verify**: `python3 -m unittest tests.test_qa_gates -v` → no_id_leak 相关测试全绿。

### Step 3: 修复 subsection_numbering

`tools/prop_tools.py:1106` 模式改为要求编号后跟分隔符:`r'^### [一二三四五六七八九十]+\s*[、.．)）]'`。

**Verify**: `python3 -m unittest tests.test_qa_gates -v` → subsection 相关测试全绿。

### Step 4: 修复 no_internal_leak 精度

`tools/prop_tools.py:1074-1086`:
- `生成时间` 模式锚定为装配器元数据形态:仅匹配行首列表/引用块形态(装配器写入的是 `> **投标方案** ·` 元数据块与 `生成时间：` 行首形态),如 `r'^[>\-*\s]*生成时间\s*[:：]'` 且要求同行含日期数字或紧邻元数据块;普通句中「XX生成时间：每日」不命中。实现时以 Step 1 的正反语料同时通过为准。
- 英文术语模式:`canonical` 单词过于通用,收紧为仅当以内部术语组合出现(如 `canonical state`、`canonical-ready`、五个内部词保留 `DecisionJob|ValueProposition|customer[- ]fit|realization manifest` 不变)。
- URL 模式保持硬失败,但把命中改为逐行扫描并在 `leaks` 文案中带上行号(如 `URL（第 123 行）`),便于定位。

**Verify**: `python3 -m unittest tests.test_qa_gates -v` → internal_leak 相关测试全绿。

### Step 5: 顺手修 no_sales_cta 与 _clean_md

- `tools/prop_tools.py:1201`:`排除项` 与 `不包含以下服务` 改为要求出现在标题或列表项开头(`re.MULTILINE` 下 `^[\s#>*\-]*排除项`),句中引用不命中。此检查保持 warning 级不变。
- `_clean_md`(185-198 行):追加删除表格分隔行(形如 `^\|?[\s:|-]+\|[\s:|-]*$` 的整行)。

**Verify**: `python3 -m unittest tests.test_qa_gates -v` → 全绿。

### Step 6: 全量回归

**Verify**:
- `python3 -m unittest discover -s tests` → 全部通过(≥44 个)。
- `python3 -m py_compile tools/prop_tools.py tools/prop_v3.py` → exit 0。

## Test plan

- 新测试文件 `tests/test_qa_gates.py`,按 check 键组织为参数化正反语料矩阵(每个 check 至少 1 反例 + 1 正例;见 Step 1 清单)。
- 结构模式参照 `tests/test_prop_tools.py` 现有 QA 测试(tempfile 写 report → 调 `qa_proposal` → 断言 `checks[key]`)。
- 完成后测试总数 ≥44,且 Step 1 的反例语料从红转绿、正例语料始终绿。

## Done criteria

- [ ] `python3 -m unittest discover -s tests` exit 0,总数 ≥44
- [ ] `python3 -m py_compile tools/prop_tools.py tools/prop_v3.py` exit 0
- [ ] `grep -n "re.IGNORECASE" tools/prop_tools.py` 在 no_id_leak 的 `id_pattern` 段(约 1110-1115 行)无命中
- [ ] `grep -n "except Exception" tools/prop_tools.py` 在 1135-1145 区域的分支不再把 `exact_ids` 静默置空(改为 degraded 呈现)
- [ ] `git status` 显示只有 in-scope 文件被修改
- [ ] `plans/README.md` 状态行已更新

## STOP conditions

- "Current state" 的行号/摘录与现库不符(代码已漂移)。
- 反例与正例语料对同一模式提出不可同时满足的要求超过一处(说明检测策略需要产品决策,报告后停)。
- 修复需要触碰 `tools/prop_v3.py` 或政策文件。
- 某一步验证在一次合理修正后仍失败两次。

## Maintenance notes

- 未来任何向 `qa_proposal` 新增检查时,必须同步向 `tests/test_qa_gates.py` 添加正反语料——反例缺失正是本批误报存活至今的原因。
- 审阅者应重点核对 Step 2 的 `[SMD]\d` 收紧没有放过真实 legacy 编号(对照正例语料)。
- 显式遗留:`no_internal_leak` 的 URL 检测对「协议格式说明」类合法技术表述仍会硬失败;若真实 run 中出现该场景,再评估降为 warning + 人工复核(本计划不做该降级,避免放松真泄漏拦截)。
