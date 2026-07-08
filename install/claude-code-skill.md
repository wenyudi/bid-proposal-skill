# 安装到 Claude Code

Claude Code 只会加载 `~/.claude/skills/<name>/SKILL.md`。**仅仅把本仓库 clone 下来是不够的**——不注册入口，Claude 不会走本 skill 的多 agent 流程（不联网调研、不并行分章、不读案例库），只会凭对话直接写方案。

## 步骤

1. clone 本仓库到任意位置，例如 `~/Code/proposal`
2. 把下面的入口模板写入 **`~/.agents/skills/proposal/SKILL.md`**（跨 harness 共享位置），
   把 `{REPO}` 全部替换成第 1 步的绝对路径
3. 从各 CLI 的 skill 目录软链过去：
   ```bash
   mkdir -p ~/.agents/skills/proposal ~/.claude/skills
   ln -s ../../.agents/skills/proposal ~/.claude/skills/proposal
   ```
   （pi 原生加载 `~/.agents/skills/`，无需软链）
4. 新开一个会话，输入 `/proposal <标书路径>` 验证

> 入口只是一个指针，仓库才是唯一事实来源。改流程改仓库里的文件即可，入口一般不用动。

## 入口模板

````markdown
---
name: proposal
description: 政企传媒投标方案生成 — 读甲方标书拆评分项保基础得分，按标选叙事策略（逻辑征服/故事打动/愿景共创/数据实证），联网调研甲方/行业/案例 + 从本地案例库自动筛选案例，并行分章撰写，方案综述，红队四视角评审，应标对照表零遗漏校验。含两道人工关卡（策略确认/红队定稿）。Use when 用户要写投标方案/应标文件/给政企客户的提案，或提供标书要求出方案，或输入 /proposal。
---

# proposal — Claude Code 执行入口

本 skill 的完整定义（调度流程/质量标准/prompt/工具脚本）在 **`{REPO}/`**，那是唯一事实来源。本文件只做两件事：把你引到那里，并把文档里的 OpenCode 工具名翻译成 Claude Code 工具。

## 执行步骤

1. **读取定义**：Read `{REPO}/SKILL.md`（主调度流程，必读）、`RULES.md`、`TYPES.md`、`profiles.json`。
2. **严格按其"主 agent 调度流程"执行**：Setup → 语言判定 → 标书摄入+模式/叙事/关卡解析 → Task1 标书解读 → **⛳ Gate 1 策略确认（停下问人）** → Task2 联网情报（含案例库筛选）→ Task3 并行分章 → Task3.5 方案综述 → Task4 装配+合规+自评+红队四视角+人工待办 → **⛳ Gate 2 红队定稿（停下问人）**。
3. 所有工具名按下表映射（**派发子 agent 时，把本映射表附在子 agent prompt 末尾**，子 agent 同样只有 Claude Code 工具）。

## 工具映射（文档写法 → Claude Code 实际）

| 文档里写的 | Claude Code 用 |
|:----------|:---------------|
| `task()` 派发子 agent | `Agent` 工具，subagent_type=`general-purpose` |
| `task(run_in_background=true)` | `Agent` 工具 `run_in_background: true`（默认即后台）；全部完成的通知到达后再收集 |
| `background_output` 收集 | `TaskOutput`（先 `ToolSearch` 加载），或直接 Read 各章输出文件确认 |
| `todowrite` 进度 | `TaskCreate` / `TaskUpdate`（先 `ToolSearch` 加载） |
| `websearch` | `WebSearch`（先 `ToolSearch` 加载） |
| `webfetch` | `WebFetch`（先 `ToolSearch` 加载） |
| `scrapling_bulk_get` 等 | 用 `ToolSearch` 搜 "scrapling"——有则用；没有则全部 `WebFetch` 兜底并在 manifest 标注 |
| `read` / `write` / `glob` / `bash` | `Read` / `Write` / `Glob` / `Bash` |
| Gate 1/2 向用户提问 | `AskUserQuestion` 工具（把 `open_questions` / 红队质疑做成选择题） |

## 关键约定（防跑偏）

- **Task2 是查资料的核心**：必须真的联网（WebSearch + WebFetch 并行多查询），产出结构化 `intel-pool.json`，不许用模型记忆凑数据。
- **Task3 是稳定分章的核心**：逐章并行派发 Agent，每章 prompt 嵌入该章评分标准 + 叙事指令 + 筛好的情报；缺章/空章必须重写，不许主 agent 自己一口气写全文。
- **Task3.5 综述必须最后写**：读完各章再提炼，不许从策略推演；主张/数字不得超出正文。
- **红队四视角并行**：`prompts/task4_redteam.md` × 4（buyer/expert/audit/rival，角色定义在 TYPES.md）。红队**只提质疑不改稿**，只有致命项才自动补。
- **案例库**：`{REPO}/casebase/` 存在且非空时自动纳入素材（见主 SKILL.md Step 0.5），Task2 按标筛选案例。
- **交付物是技术标卷册目录**，不是一份研报：`技术方案-完整版.md` + `分册/NN-*.md` + `_内部研判.md`（不递交）+ `_人工待办.md`（不递交）。范围只到技术标，投标函/授权书/承诺函/报价表不生成。
- ⚡ **递交稿零内部泄露**：不得出现叙事策略、深度模式、工具版本、生成时间、阅读时间、URL、以及对本方案手法的自我描述（"本方案采用故事化叙事"）。把这些印给评委等于亮底牌。
- **两个硬阻断点**：`check-compliance`（强制项遗漏 → 废标风险）与 `qa-proposal` 的 `no_internal_leak`（内部泄露）。两者不过不许交付。
- ⛳ **两道人工关卡不许自行跳过**（除非用户加 `-auto`）。到关卡就**结束 response 等用户回复**，绝不"替用户假设后继续"。Gate 1 在 Task1 之后（策略错了后面全白做），Gate 2 在红队之后（哪些质疑要补是投标人的判断）。
- **交付时必须提示两件事**：① `_人工待办.md` 里是 AI 不该替人编造的内容（真实业绩/报价数字/团队人员/可承诺 KPI），废标风险项没填完就递交 = 零分；② **下划线开头的文件一律不要递交**。
````

## 其他 CLI

- **OpenCode**：仓库内文档就是按 OpenCode 工具名写的，把仓库注册为 skill 即可，`command/proposal.md` 自动生效。
- **Codex CLI / Cursor**：参考上面的映射表，替换成对应工具名。
