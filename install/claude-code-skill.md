# 安装到 Claude Code

仅 clone 仓库不会注册 skill。需要让 Claude Code 的 skill 入口指向本仓库；仓库仍是唯一事实来源，后续更新不必复制 prompt。

## 安装

1. clone 到固定目录，例如 `~/Code/proposal`。
2. 建立跨 harness 入口 `~/.agents/skills/proposal/SKILL.md`，使用下方模板并把 `{REPO}` 替换为绝对路径。
3. Claude Code 建软链：

```bash
mkdir -p ~/.agents/skills/proposal ~/.claude/skills
ln -s ../../.agents/skills/proposal ~/.claude/skills/proposal
```

pi 原生读取 `~/.agents/skills/`。新开会话后输入 `/proposal <标书路径>` 验证。

## 入口模板

````markdown
---
name: proposal
description: 政企传媒技术标 v3 生成：拆标书硬要求，建立多角色客户价值与交付 canonical，研究后选亮点，并行分章与独立兑现审计，红队和硬门定稿。Use when 用户要写投标方案/应标文件/政企客户提案，提供标书要求出方案，或输入 /proposal。
---

# proposal — Claude Code 入口

完整定义位于 `{REPO}`，它是唯一事实来源。

1. Read `{REPO}/SKILL.md`、`RULES.md`、`TYPES.md`、`profiles.json`；Task 1 前 Read `DECISIONS.md`。用户显式 `-legacy` 时改读 `LEGACY.md`，两套引擎不得混线。
2. 严格执行 SKILL.md：Task 1 bootstrap → Gate 1 → Task 2 Evidence → Task 2.5 选择 → generation gate/snapshot → 并行 Task 3 → 独立 realization audit → realized-only 综述 → 装配/硬检/fit → 四视角红队/Gate 2 → `_state` 归档。
3. 所有仓库相对路径从 `{REPO}` 解析；Python 优先 `python3`，若不可用再选当前平台 Python 3。

## 工具映射

| 文档概念 | Claude Code |
|:---|:---|
| 派 agent | `Agent`，subagent_type=`general-purpose`；章节可 `run_in_background: true` |
| 收集后台 | `TaskOutput`，或 Read 目标文件确认 |
| 进度 | `TaskCreate` / `TaskUpdate` |
| 搜索/抓取 | `WebSearch` + `WebFetch`；有 Scrapling 时可批量抓全文 |
| read/write/glob/bash | `Read` / `Write` / `Glob` / `Bash` |
| Gate 单题 | `AskUserQuestion`；一次一题，给推荐与得失后停止等待 |

派子 agent 时附上其实际可用工具映射。Task 2 必须真实联网并抓原文；Task 3 只读 compiled brief；realization auditor 必须与 writer 分离；红队只提 root diagnostic。

## 不能省的门

- canonical 只由主 agent 通过 ChangeSet 写；stale/失败整组回滚。
- Task 2.5 后 `check-canonical --stage generation` 通过才写作。
- 每章与综述 realization valid 才装配；摘要只能用 realized 白名单。
- 最终 compliance、QA、canonical submission 都通过，customer-fit 才可显示 overall；fit 不是评委分/中标概率。
- `-auto` assumed 阻断直接递交；必须醒目标草案。
- private notes、URL、canonical ID、策略/模式/工具痕迹绝不进递交稿。
- `_内部研判.md`、`_人工待办.md`、`_state/` 均不递交；状态归档成功后才清 TMPDIR。
- v3 失败不得静默切 legacy；只有用户显式 `-legacy` 才回退。
````

## 其他 CLI

- OpenCode：仓库注册为 skill 后使用 `command/proposal.md`。
- Codex / Cursor：保留同一流程，只映射 agent、search、fetch 与文件工具。

---
```
proposal skill · 3.0.0 install
```
