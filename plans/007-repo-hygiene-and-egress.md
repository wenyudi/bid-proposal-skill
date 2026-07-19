# Plan 007: 仓库卫生 — 运行输出与 git 隔离、外呼端点可配置并披露

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat b10506e..HEAD -- .gitignore tools/prop_tools.py docs/reference/command-line.md CONTRIBUTING.md`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1(S 级工作量,隐私影响大,先做)
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: security
- **Planned at**: commit `b10506e`, 2026-07-16

## Why this matters

装配输出写入 `{SKILLDIR}/reports/<lang>`——即 skill 仓库自身,而 `.gitignore` 不忽略 `reports/`。当前工作区已经躺着一个完整的未跟踪运行卷册,内含 `_内部研判.md`(策略、fit、红队结论)、`_人工待办.md`、`_state/`(含 private 纪要投影)——一次随手 `git add -A` 就会把内部研判与潜在客户信息提交进版本库;git 历史里已经有一份完整的旧方案输出(`reports/zh/_legacy-v1/`,索引中呈删除状态但历史仍在)。这与 CONTRIBUTING.md:52「不要提交真实标书、客户私密材料」自相矛盾。另外 `detect-engine` 硬编码探测一个私人第三方搜索端点,每个用户每次调用都外呼该域名且文档未披露——端点易主或下线时「搜索可用性」信号失真,离线环境还要白等 15 秒。

## Current state

- `.gitignore`(全文 12 行)— 忽略 `__pycache__/`、`/tmp-proposal-*/`、`/.scratch/`,**不含** `reports/`。
- `git status`(基线时点)— 未跟踪:`reports/zh/.last-good/`、`reports/zh/让每一次商客宣传需求，都抵达可用、可验、可复用的成品-20260718-231213/`(含 `_内部研判.md`、`_人工待办.md`、`_state`、`_redteam`);已跟踪且呈本地删除:`reports/zh/_legacy-v1/` 两个文件。
- `tools/prop_tools.py:1575-1584` — `detect_engine`:

  ```python
  def detect_engine():
      import urllib.request as _req
      try:
          r = _req.Request("https://search.h33.top/search?q=test&format=json",
                           headers={"User-Agent": "Mozilla/5.0"}, method="GET")
          with _req.urlopen(r, timeout=15) as resp:
  ```

- `docs/reference/command-line.md:208` — 只说「探测可选搜索引擎,可用性仅作信息」,未披露外呼对象。
- 约束:装配默认输出到 `reports`(`assemble-proposal --output` 可指定),SKILL.md:184 的调用固定 `--output "{SKILLDIR}/reports/<lang>"` — **本计划不改输出位置**(那是行为变更,牵动 SKILL/docs/测试),只做 git 隔离与披露。

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| 全部测试 | `python3 -m unittest discover -s tests` | 全部通过 |
| 语法检查 | `python3 -m py_compile tools/prop_tools.py` | exit 0 |
| 忽略生效 | `git check-ignore -v reports/zh/x 2>/dev/null; git status --porcelain \| grep reports` | check-ignore 命中规则;status 不再列 reports 未跟踪项 |

## Scope

**In scope**:
- `.gitignore`
- git 索引操作:`git rm -r --cached "reports/zh/_legacy-v1"`(仅索引,保留工作区文件)
- `tools/prop_tools.py`(仅 `detect_engine` 函数)
- `docs/reference/command-line.md`(detect-engine 段)
- `CONTRIBUTING.md`(一句提醒)
- `tests/test_prop_tools.py`(detect-engine 离线测试)

**Out of scope**:
- 装配输出目录的迁移(改到用户目录/仓库外)— 行为变更,需维护者决策;记录于 Maintenance notes。
- 清洗 git 历史(filter-repo/BFG)— 破坏性操作,只在 Maintenance notes 中告知维护者自行决定。
- `casebase/` 的存放策略。

## Git workflow

- Branch: `advisor/007-repo-hygiene-and-egress`
- 不 push、不开 PR,除非操作者指示。`git rm --cached` 只动索引,不删除工作区文件。

## Steps

### Step 1: .gitignore 隔离运行输出

在 `.gitignore` 追加(带注释,风格与现有条目一致):

```gitignore
# 运行输出卷册（含内部研判/状态，绝不入库）
/reports/
```

**Verify**: `git status --porcelain | grep -c "reports/"` → 输出中不再出现未跟踪的 reports 目录(已跟踪的 `_legacy-v1` 删除标记仍会显示,属预期,Step 2 处理)。

### Step 2: 把历史输出移出索引

```bash
git rm -r --cached "reports/zh/_legacy-v1"
```

(该目录在工作区已被用户本地删除,`git rm --cached` 使删除进入暂存;若命令因路径不存在报错,先 `git status` 确认这两个文件的当前状态,按实际形态处理——目标是 HEAD 的下一次提交中不再跟踪 reports/ 下任何内容。)

**Verify**: `git ls-files | grep -c "^reports/"` → 0(暂存后以 `git diff --cached --name-status | grep reports` 呈现 D 状态)。

### Step 3: detect-engine 可配置 + 快速失败

`tools/prop_tools.py` `detect_engine`:
1. 端点改读环境变量 `PROPOSAL_SEARCH_PROBE_URL`;未设置时**不发任何请求**,直接返回 `{"engine": "none", "available": False, "hint": "set PROPOSAL_SEARCH_PROBE_URL to enable probing"}`(输出仍为 JSON,键结构与现有成功/失败形态兼容——先读现有 return 语句,保持键名一致)。
2. 设置了端点时 `timeout=5`,其余逻辑不变。

**Verify**: `python3 tools/prop_tools.py detect-engine` (不设环境变量)→ 立即返回(<1 秒)且 exit 0;`grep -n "h33.top" tools/prop_tools.py` → 0 命中。

### Step 4: 披露与文档

1. `docs/reference/command-line.md` detect-engine 行改为说明:默认不外呼;设置 `PROPOSAL_SEARCH_PROBE_URL` 后会向该地址发起探测请求(用户自选端点)。
2. `CONTRIBUTING.md` 「提交前检查」清单追加一行:「`git status` 不应出现 `reports/` 下的任何文件;运行输出一律不入库」。

**Verify**: `grep -n "PROPOSAL_SEARCH_PROBE_URL" docs/reference/command-line.md` → 有命中。

### Step 5: 测试与回归

在 `tests/test_prop_tools.py` 追加:不设环境变量时 `detect_engine()` 返回 `available=False` 且不发起网络调用(patch `urllib.request.urlopen` 断言未被调用)。

**Verify**: `python3 -m unittest discover -s tests` → 全部通过;`python3 -m py_compile tools/prop_tools.py` → exit 0。

## Test plan

见 Step 5(1 个新测试)。其余步骤以 git/grep 命令验证。

## Done criteria

- [ ] `git check-ignore reports/zh/anything` 命中 `/reports/` 规则
- [ ] `git ls-files | grep -c "^reports/"` = 0(或暂存区呈全部 D)
- [ ] `grep -c "h33.top" tools/prop_tools.py` = 0
- [ ] 不设环境变量时 `python3 tools/prop_tools.py detect-engine` 秒回
- [ ] `python3 -m unittest discover -s tests` exit 0
- [ ] `git status` 只有 in-scope 文件/索引被修改
- [ ] `plans/README.md` 状态行已更新

## STOP conditions

- `reports/zh/_legacy-v1` 的 git 状态与 "Current state" 描述不符(用户可能已自行处理)— 按实际状态重新评估 Step 2,拿不准就停。
- 发现调用方(SKILL.md/docs)依赖 detect-engine 的特定返回键而 Step 3 会破坏 — 保持键结构兼容,做不到则停。
- 任何步骤似乎需要改写 git 历史 — 那是明确 out of scope,停。

## Maintenance notes

- **git 历史中仍存在** `reports/zh/_legacy-v1/` 的完整方案文本(标题含具体项目名)。若该仓库计划公开或已推送远端,维护者应评估:该内容是否含真实客户信息 → 如是,需用 `git filter-repo` 清洗历史并轮换远端;本计划不执行破坏性历史操作。
- 结构性根因是「用户数据(casebase)与运行输出(reports)住在 skill 仓库里」,`git pull` 升级与本地数据天然互相污染。长期解应是输出目录移到 `~/.proposal/reports/`(或项目工作目录),`casebase` 支持外部路径——这是行为变更,建议作为独立决策评估。
- 审阅者核对:`.gitignore` 加 `/reports/` 后,`.last-good` 机制(在 reports 目录内)不受影响——它本来就不应入库。
