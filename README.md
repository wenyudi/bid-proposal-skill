# proposal — 政企传媒投标方案生成 skill

为广告/传媒公司生成给**政企客户**投标的正式方案文档。核心目标：

> **保证基础（不废标、覆盖全部评分项）→ 合理成本（单一最优报价）→ 贴标的叙事（逻辑征服 / 故事打动 / 愿景共创 / 数据实证）→ 给甲方最大惊喜（差异化脱颖而出）**

配套 [deep-research](https://github.com/hoolulu/deep-research) 使用：调研负责"看清一件事"，proposal 负责"赢下一个标"。多 agent 链式架构（拆解 → 情报 → 并行撰写 → 装配 QA）借鉴自 deep-research（MIT）。

---

## 安装

**必须注册 skill 入口，否则 AI 不会走本 skill 的多 agent 流程**（不联网调研、不并行分章、不读案例库，只会凭对话直接写方案）。

- Claude Code → 见 [`install/claude-code-skill.md`](install/claude-code-skill.md)
- OpenCode → 直接把本仓库注册为 skill，`command/proposal.md` 自动生效
- 其他 CLI → 参考上文的工具映射表适配

---

## 用法

```
/proposal <标书文件路径或粘贴标书文本> [素材路径] [-quick|-deep] [-logic|-story|-vision|-evidence]
```

- **必需**：甲方标书（`.pdf/.docx/.md/.txt` 路径，或直接粘贴标书内容）
- **可选**：案例库 / 资质 / 报价参考等本地素材路径
- **模式**：
  - `-quick` 快速应标（小标 / 时间紧）
  - 默认 标准投标（评分项 8-12 项）
  - `-deep` 大标 / 重点项目（强竞争 / 多轮答辩）
- **叙事**（可选；不指定则按标书特征自动判定，见 TYPES.md 叙事策略库）：
  - `-logic` 逻辑征服 · `-story` 故事打动 · `-vision` 愿景共创 · `-evidence` 数据实证

示例：
```
/proposal /Users/me/招标文件.pdf ~/我司案例库/ -deep
/proposal /Users/me/文旅局宣传标书.pdf -story
/proposal （粘贴标书正文……）
```

---

## 它怎么保证"赢标三要素"

| 诉求 | 机制 |
|:----|:-----|
| **保基础** | Task1 把标书拆成 `requirements.json`（强制项 + 评分项 + 权重）；Task4 生成**应标响应与评分对照表**并做 `check-compliance` **阻断式**零遗漏校验——任一强制项漏应答即视为废标风险，必须补齐才能交付 |
| **控成本** | 报价章只出**单一最优解**，卡在标书预算带内，价值-成本一一对应（不做分档阶梯） |
| **会讲法** | Task1 按标书特征选定**叙事策略**（逻辑征服 / 故事打动 / 愿景共创 / 数据实证，用户可用标志强制指定），through_line 贯穿各章；**叙事只决定讲法不裁内容**——评分点仍零遗漏，报价与合规响应永远逻辑呈现 |
| **有战绩** | 把真实案例放进 `casebase/`（格式见其 README），生成时自动按行业/客户类型/预算量级筛选 3-8 个最匹配案例写进方案；案例库案例永远优先于联网第三方案例 |
| **给惊喜** | Task1 提炼 Big Idea + 差异化增值点候选；Task2 联网找甲方画像/行业数据/标杆案例坐实（story/vision 叙事下加采叙事素材）；Task3 写入并标为亮点；QA 校验差异化点数 ≥ 模式下限 |
| **竞争力研判** | Task4 `self-score` 给出预估得分、覆盖率、薄弱评分项，+ LLM 定性研判（内部参考，不写入交付文档） |

---

## 架构

主 agent 调度 4 个 Task，中间数据走临时目录：

```
标书 → Task1 标书解读+投标策略  → requirements.json + strategy.json
       Task2 联网情报收集        → intel-pool.json（甲方/行业/竞品/案例）
       Task3 并行分章撰写        → sections/section-*.md（每章照评分标准写）
       Task4 装配+合规+自评+QA   → reports/zh/<方案标题>-<时间戳>.md
```

- **联网为主**：沿用运行时自适应搜索（CLI 内置引擎 + SearXNG + 免费源）+ Scrapling 全文抓取，webfetch 兜底
- **交付物**：正式投标方案文档（Markdown，可转 Word/PDF）

---

## 文件结构

```
proposal/
├── SKILL.md              主调度流程 + 中标级质量标准
├── RULES.md              废标红线 / 真实性红线 / 常见陷阱
├── TYPES.md              六类提案类型 + 评标维度模型 + 叙事策略库 + 编号体系
├── profiles.json         三档参数（章节数/段落/差异化下限/字数）
├── VERSION
├── command/proposal.md   /proposal 命令入口
├── prompts/
│   ├── task1_teardown.md      标书解读 + 投标策略 + 方案框架
│   ├── task2_intel.md         联网情报收集
│   ├── task3_section_agent.md 分章撰写
│   └── task4_assembly.md      装配/合规/自评/QA 命令参考
├── tools/prop_tools.py   自包含引擎：assemble / check-compliance / self-score / qa / encoding
├── casebase/             案例库（放真实案例 .md，自动筛选进方案；格式见其 README）
└── reports/zh/           输出目录
```

---

## 依赖

- Python 3.8+（`prop_tools.py` 仅用标准库）
- 联网调研需要可用的搜索工具（CLI 内置 websearch / SearXNG）与抓取工具（Scrapling MCP 或 webfetch）
- 读 `.pdf/.docx` 标书时自动安装 `pypdf2` / `python-docx`

---

## ⚠️ 合规声明

生成内容为投标响应草案，业绩/资质/团队信息以真实素材为准，无把握处以 `【待补充/待核实】` 占位——**切勿用虚构信息投标**（涉嫌串标/骗标，法律责任严重）。竞争力自评为机械估算，非评委真实打分，仅供投标决策参考。

---
```
proposal skill · 政企传媒投标方案生成
```
