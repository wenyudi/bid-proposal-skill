# 安装并注册 proposal

仅 clone 仓库不会让宿主自动执行 proposal 流程。你还需要注册一个 skill 入口，并让入口指向仓库这个唯一事实来源。

以下步骤覆盖 Codex、Claude Code 和 pi。Codex 直接注册整个仓库；Claude Code 与 pi 使用一个指向仓库的薄入口，避免复制 prompt。

## 1. 克隆仓库

选择一个长期不变的目录：

```bash
git clone https://github.com/wenyudi/bid-proposal-skill.git ~/Code/proposal
cd ~/Code/proposal
python3 -m unittest discover -s tests
```

若你使用 GitHub SSH，也可以把 clone 地址换成 `git@github.com:wenyudi/bid-proposal-skill.git`。

测试应全部通过。后续入口只引用这个目录，更新时在仓库内执行常规 `git pull`，无需复制 prompts。

## 2. 注册到 Codex

Codex 从 `${CODEX_HOME:-$HOME/.codex}/skills` 发现 skill。先确认目标不存在，再把整个仓库软链进去；把示例仓库路径替换为实际绝对路径：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
ls -ld "${CODEX_HOME:-$HOME/.codex}/skills/proposal"
ln -s /绝对路径/proposal "${CODEX_HOME:-$HOME/.codex}/skills/proposal"
```

若 `ls` 已显示同名目标，先确认它是否指向本仓库，不要覆盖其他版本。`agents/openai.yaml` 提供 Codex 的展示名称和默认调用提示；主流程仍只以仓库根目录的 `SKILL.md` 为准。

新开 Codex 会话后用 `$proposal` 调用，例如：

```text
$proposal /绝对路径/一份测试标书.md -quick
```

## 3. 建立 Claude Code / pi 入口

创建入口目录：

```bash
mkdir -p ~/.agents/skills/proposal
```

用编辑器新建其中的 `SKILL.md`。把下面所有 `{REPO}` 替换为仓库绝对路径，例如 `/home/me/Code/proposal`；不要使用 `~`。

````markdown
---
name: proposal
description: 政企传媒技术标 v3.3 生成：拆标书硬要求，建立客户价值与真实交付边界，研究后比较策略命题，收敛一页纸主线和一个客户主亮点，以同一主线正向写作、独立兑现审计和硬门定稿。Use when 用户要写投标方案/应标文件/政企客户提案，提供标书要求出方案，或输入 /proposal。
---

# proposal — 宿主入口

完整定义位于 `{REPO}`，它是唯一事实来源。

1. Read `{REPO}/SKILL.md`、`{REPO}/RULES.md`、`{REPO}/TYPES.md`、`{REPO}/profiles.json`；Task 1 前 Read `{REPO}/DECISIONS.md`。用户显式 `-legacy` 时改读 `{REPO}/LEGACY.md`，并使用独立的 legacy 引擎与状态。
2. 严格执行 v3.3.0：确定性 Task 1 scaffold/bootstrap → Gate 1 → Task 2 Evidence/strategy signal → Task 2.5 比较命题、选择 signature 成果 → 一次人工策略批准（`-auto` 为 assumed）→ safe-draft snapshot → 并行 Task 3 正向写作 → 批量独立 realization audit → realized-only 综述 → 装配 → 自适应红队/Gate 2 → report-anchored customer-fit → `validate-run` / `finalize-run`。生成任务采用“目标—依据—工作顺序—安全替代—输出契约”，反模式只进入 critic 与复盘。
3. 所有仓库相对路径从 `{REPO}` 解析；Python 优先 `python3`，若不可用再选择当前平台的 Python 3。
4. canonical 只由主 agent 通过 ChangeSet 写。Task 2 必须抓取原文；Task 3 只读 compiled brief；realization auditor 必须与 writer 分离；红队只提交 root diagnostic。
5. `-auto` 的 assumed 决策对应 draft-only。private notes、URL、canonical ID、策略/模式/工具痕迹与下划线内容保持在内部卷册；客户递交稿只使用获授权投影。

## Claude Code 工具映射

| 流程概念 | Claude Code |
|:---|:---|
| 派 agent | `Agent`，`subagent_type=general-purpose`；章节可后台运行 |
| 收集后台结果 | `TaskOutput`，或读取目标文件确认 |
| 记录进度 | `TaskCreate` / `TaskUpdate` |
| 搜索与抓取 | `WebSearch` + `WebFetch` |
| 读写与命令 | `Read` / `Write` / `Glob` / `Bash` |
| Gate 单题 | `AskUserQuestion`；一次一题，给推荐与得失后等待 |
````

入口文件应很短。不要把仓库中的主 prompt 复制进去，否则仓库更新后会出现两份不一致的事实来源。

## 4. 注册到 Claude Code

Claude Code 使用 `~/.claude/skills/`。先检查目标是否已存在：

```bash
ls -ld ~/.agents/skills/proposal ~/.claude/skills/proposal
```

如果 `~/.claude/skills/proposal` 不存在，建立父目录和软链：

```bash
mkdir -p ~/.claude/skills
ln -s ../../.agents/skills/proposal ~/.claude/skills/proposal
```

如果目标已经存在，先人工确认它是否就是当前 proposal 入口；不要盲目覆盖其他 skill。

pi 原生读取 `~/.agents/skills/`，不需要 Claude Code 这一步软链。

## 5. 验证注册

关闭旧会话并新开一个会话。Claude Code / pi 输入：

```text
/proposal /绝对路径/一份测试标书.md -quick
```

正确注册后，宿主应先加载 proposal skill、检查标书输入并执行 Task 1，而不是直接生成一篇通用方案。

也可以在仓库内确认 CLI：

```bash
python3 tools/prop_tools.py --help
python3 tools/prop_tools.py check-canonical --help
```

## 更新

在仓库目录拉取更新并重新测试：

```bash
git pull --ff-only
python3 -m unittest discover -s tests
```

只要仓库绝对路径未变，入口和软链无需重建。若注册后未触发、提示找不到文件或 Python 不可用，按[解除常见阻断](resolve-blockers.md)检查。
