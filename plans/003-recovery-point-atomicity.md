# Plan 003: 让 last-good 恢复点在所有失败路径下真正不可丢失(assemble-proposal 与 archive-state)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat b10506e..HEAD -- tools/prop_tools.py tools/prop_v3.py tests/`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: MED(改原子替换序列;必须先落失败注入测试再改实现)
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `b10506e`, 2026-07-16

## Why this matters

「上一份成功卷册/状态永远可恢复」是本仓库反复承诺的安全不变式(SKILL.md:226「失败不得删除 TMPDIR 或上一份成功卷册」;RULES.md §10「最终卷册先 staging 后原子切换,上一份成功结果进入 .last-good」)。当前两处实现都采用「先删旧备份、再顶上新备份」的顺序:单点失败(os.replace 抛错、进程被杀)会把恢复点清空,而 `archive-state` 的失败消息还会谎称 "last-good preserved",误导主 agent 做出「旧状态还在」的错误判断。这些异常分支目前零测试——修复必须由失败注入测试钉住。

## Current state

相关文件:

- `tools/prop_tools.py` — `assemble_proposal` 内的晋升逻辑(约 570-599 行)与 staging 构建(约 468-568 行)。
- `tools/prop_v3.py` — `archive_state`(约 4285-4345 行)。
- `tests/test_prop_tools.py:365-438` — 现有 assemble 测试:只覆盖成功晋升、同秒重装配、last-good 生成;失败路径零覆盖。
- `tests/test_prop_v3.py:818,843` — archive 测试:只覆盖成功链与前置拒绝。

问题 1 — `assemble_proposal` 晋升(`tools/prop_tools.py:579-599`):

```python
    try:
        if previous_path:
            os.makedirs(last_good_root, exist_ok=True)
            if os.path.exists(last_good_dir):
                shutil.rmtree(last_good_dir, ignore_errors=True)   # ← 先毁旧备份
            os.replace(previous_path, last_good_dir)
            moved_previous = True
        os.replace(staging_dir, bundle_dir)                        # ← 此处失败时…
        staging_dir = None
        ...
    except Exception:
        if moved_previous and previous_path and not os.path.exists(previous_path):
            try:
                os.replace(last_good_dir, previous_path)           # ← 新备份被搬走
            except Exception:
                pass
```

若 `os.replace(staging_dir, bundle_dir)` 失败(目标目录非空、权限/IO 错误),恢复分支把 previous 从 last-good 搬回原位——previous 卷册本体安全,但 `.last-good/<title>` 变空:旧备份已在 583 行删除,新备份又被搬走。另外 staging 构建段(468-557)无 try/finally:构建中途抛异常时 `.proposal-bundle-staging-*` 目录永久遗留在输出目录(仅 562-568 的 issues 路径有清理)。

问题 2 — `archive_state`(`tools/prop_v3.py:4329-4345`):

```python
        if os.path.exists(last_good): shutil.rmtree(last_good, ignore_errors=True)  # ← 先毁旧备份
        if os.path.exists(target): os.replace(target, last_good)
        os.replace(staging, target)
        ...
    except Exception as exc:
        if not os.path.exists(target) and os.path.exists(last_good):
            try: os.replace(last_good, target)
            except Exception: pass
        return {"passed": False, "issues": ["archive failed; last-good preserved: %s" % exc]}
```

同型问题,且失败消息固定为 "last-good preserved",与实际(旧 last-good 已被 rmtree)不符。`rmtree(ignore_errors=True)` 部分失败导致 last_good 残留非空时,后续 `os.replace(target, last_good)` 在部分平台直接失败,触发上述路径。

仓库约定:纯标准库;`os.replace` 是既有原子原语;测试用 `unittest` + `unittest.mock`。

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| 全部测试 | `python3 -m unittest discover -s tests` | 全部通过 |
| 定向测试 | `python3 -m unittest tests.test_prop_tools -v` / `tests.test_prop_v3 -v` | 全部通过 |
| 语法检查 | `python3 -m py_compile tools/prop_tools.py tools/prop_v3.py` | exit 0 |

## Scope

**In scope**:
- `tools/prop_tools.py`(仅 `assemble_proposal` 的 staging 构建包裹与晋升序列)
- `tools/prop_v3.py`(仅 `archive_state` 的替换序列与失败消息)
- `tests/test_prop_tools.py`、`tests/test_prop_v3.py`(追加失败注入测试)

**Out of scope**:
- 装配的内容生成逻辑(章节拼装、L 字典、目录)。
- `_write_json_atomic`/`_write_text_atomic` — 已验证原子性成立。
- 卷册目录命名、`.last-good` 的目录布局约定(只改顺序,不改布局)。

## Git workflow

- Branch: `advisor/003-recovery-point-atomicity`
- 不 push、不开 PR,除非操作者指示。

## Steps

### Step 1: 失败注入测试(先红)

在 `tests/test_prop_tools.py` 追加(模仿 365-438 行现有 assemble 测试的目录构造):
1. **promote 失败保备份**:先成功装配两次(形成 bundle + `.last-good/<title>`),第三次装配时用 `unittest.mock.patch("os.replace")` 让**第二次调用**(staging→bundle)抛 `OSError`,第一次调用(previous→last-good)放行(side_effect 按调用顺序区分)。断言:装配调用抛出或返回失败后,(a) 上一份 bundle 目录仍存在且内容完好;(b) `.last-good/<title>` 目录**非空**;(c) 输出目录无 `.proposal-bundle-staging-*` 残留。
2. **构建中途失败清 staging**:patch `prop_tools.write_text`(或构建段实际使用的写文件函数,以现码为准)在写「技术方案-完整版.md」时抛 `OSError`,断言异常向上抛出后输出目录无 staging 残留、原有 bundle 与 last-good 完好。

在 `tests/test_prop_v3.py` 追加(模仿 818/843 行 archive 测试的 state 构造):
3. **archive 失败不清恢复点**:先成功 archive 两次(形成 `_state` + `_state.last-good`),第三次 patch `os.replace` 使 staging→target 调用抛 `OSError`。断言:(a) `_state` 目录仍存在(被恢复);(b) `_state.last-good` **非空**;(c) 返回 `passed=False` 且 issues 文案与实际保留状态一致(不得在 last-good 已丢失时声称 preserved)。

**Verify**: 三个新测试红(a/b 项在现实现下失败),其余测试绿。

### Step 2: 修复 assemble_proposal 晋升序列

改为「退役改名,成功后再删」:
1. 若 `last_good_dir` 已存在,先 `os.replace(last_good_dir, last_good_dir + ".retiring")`(同目录改名,原子)而非 rmtree。
2. `os.replace(previous_path, last_good_dir)` → `os.replace(staging_dir, bundle_dir)` 全部成功后,再 `shutil.rmtree(last_good_dir + ".retiring", ignore_errors=True)`。
3. 异常分支:先把 previous 搬回原位(现逻辑),再若 `.retiring` 存在且 `last_good_dir` 缺失/为空,将 `.retiring` 改名回 `last_good_dir`。
4. staging 构建段(468-557)整体包 try/except:异常时 `shutil.rmtree(staging_dir, ignore_errors=True)` 后 re-raise。

**Verify**: Step 1 测试 1、2 转绿。

### Step 3: 修复 archive_state 同型问题

同样的 retiring 序列应用于 `tools/prop_v3.py:4329-4331`;失败返回消息改为按实际状态措辞:检查 `last_good` 是否存在且非空,存在则 "last-good preserved",否则 "last-good may be lost; inspect <path>"(不得无条件声称 preserved)。

**Verify**: Step 1 测试 3 转绿;`python3 -m unittest discover -s tests` 全绿。

### Step 4: 全量回归

**Verify**:
- `python3 -m unittest discover -s tests` → 全部通过(比基线多 ≥3)。
- `python3 -m py_compile tools/prop_tools.py tools/prop_v3.py` → exit 0。

## Test plan

见 Step 1。失败注入统一用 `unittest.mock.patch` 对 `os.replace`/写文件函数做按调用序 side_effect;不引入第三方库。模式参照 `tests/test_prop_tools.py:365-438` 的目录断言写法。

## Done criteria

- [ ] `python3 -m unittest discover -s tests` exit 0,总数比基线多 ≥3
- [ ] `python3 -m py_compile tools/prop_tools.py tools/prop_v3.py` exit 0
- [ ] `grep -n "rmtree(last_good" tools/prop_v3.py tools/prop_tools.py` 不再出现「先删旧备份再替换」的顺序(rmtree 只发生在新链路全部成功之后或 retiring 清理)
- [ ] `git status` 只有 in-scope 文件被修改
- [ ] `plans/README.md` 状态行已更新

## STOP conditions

- 摘录与现库不符。
- `os.replace` 对非空目录的行为在你的平台上与预期不符,导致 retiring 序列无法原子实现 — 报告平台行为后停,不要改用非原子的 copy+delete。
- 修复过程中发现 staging 构建段依赖「异常时保留 staging 供排障」的隐含行为(如有注释或测试依赖) — 报告后停。

## Maintenance notes

- SIGKILL 窗口(两次 os.replace 之间进程被杀)在本方案下的最坏结果是多出一个 `.retiring` 目录,恢复点不丢;下次运行的 retiring 清理应容忍已存在的残留(实现时注意 `os.replace` 目标已存在的场景)。
- 审阅者核对:mock 的 side_effect 是否真的命中了目标调用(用调用参数断言,不要只按次序猜)。
- 显式遗留:`fsync` 级持久化(掉电安全)不在本计划范围——现有 `_write_json_atomic` 同样不做,属工具级一致取舍。
