---
name: proposal
description: "政企传媒投标方案生成 — 多 agent 协作：标书解读拆评分项、按标选叙事（逻辑征服/故事打动/愿景共创/数据实证）、联网调研甲方/行业/竞品/案例、并行分章撰写、应标响应对照表零遗漏校验与竞争力自评。保基础、控成本、给甲方最大惊喜。"
version: 1.2.0
updated: 2026-07-08
risk: medium
---

# proposal

为广告/传媒公司生成给**政企客户**投标的方案文档。目标：在**保证基础合规（不废标、覆盖全部评分项）**的前提下，用**合理成本的单一最优解**，配**贴合本标的叙事策略**（逻辑征服/故事打动/愿景共创/数据实证，见 TYPES.md 叙事策略库），给甲方**最大惊喜**，从众多提案中脱颖而出。

- **输入**：甲方标书（本地文件 pdf/docx/md/txt，或粘贴文本）+ 可选的用户素材（资质/报价参考）；`{SKILLDIR}/casebase/` 有案例时自动筛选纳入（无需传路径）
- **架构**：主 agent 调度 4 个 Task —— Task1 标书解读+投标策略（含叙事判定） → Task2 联网情报 → Task3 并行分章撰写（按叙事指令） → Task4 装配+合规校验+自评分+QA（主 agent 直接执行）
- **情报来源**：联网为主（甲方画像/行业趋势/竞品打法/标杆案例）+ 标书 + 用户素材
- **输出**：正式投标方案文档（Markdown，可转 Word/PDF），保存到 `{SKILLDIR}/reports/{LANG}/`
- **中间数据**：走带时间戳的临时目录 TMPDIR（requirements.json / strategy.json / intel-pool.json / sections/）
- **参考文件**：`RULES.md`（红线/废标陷阱）、`TYPES.md`（提案类型/评标维度/叙事策略库）、`profiles.json`（三档参数，修改后重启软件生效）
- **容错原则**：生成不阻塞。脚本/命令调用有兜底路径，主路径失败 → 换 `sys.executable`/检查路径/直接实现 → 三次失败后向用户报告具体问题。

---

## 0. 中标级质量标准（所有 Task 共用，缺任一即降级）

| # | 标准 | 说明 |
|---|------|------|
| 1 | **合规零废标** | 标书全部 `mandatory`（资格/实质性/格式）项都有明确响应，应标对照表零遗漏 |
| 2 | **评分项全覆盖** | 每个 `scoring` 评分项都有正文对应章节，无遗漏 |
| 3 | **甲方视角先行** | 每章以甲方要解决的问题/KPI 开头，不以自夸开篇 |
| 4 | **Big Idea 贯穿** | 有且仅有一个创意大概念统领全案，不是零散点子 |
| 4b | **叙事一致** | 全案遵循 strategy.narrative 选定的主叙事（logic/story/vision/evidence/custom），through_line 贯穿各章；报价与合规响应永远逻辑呈现；**叙事不裁内容——评分点仍须全答** |
| 5 | **创意配落地** | 每个创意/亮点配「执行路径 + 资源 + 排期」，不空谈 |
| 6 | **差异化惊喜** | ≥ `min_differentiators` 个增值点，标注"甲方未要求但加分"及其对应评分项 |
| 7 | **报价最优解** | 单一推荐报价方案，卡预算带内，价值-成本一一对应（不分档） |
| 8 | **来源可追溯** | 引用行业/案例数据标注来源（机构/年份），情报有 url |
| 9 | **真实不虚构** | 业绩/资质/团队真实；无把握处写"拟"或留占位符，不编造 |
| 10 | **标题含主张** | "3个月引爆城市声量"✅ \| "传播方案"❌ |
| 11 | **风险有预案** | 关键风险配应对措施 |
| 12 | **零套话** | 无"我们将竭诚服务""众所周知"等填充词 |
| 13 | **强制结构** | 四段式：标题 → 元数据块 → `## 目录` → `## 应标响应与评分对照表` → 正文各章 → 尾部（声明） |
| 14 | **时间戳正确** | 文件名和文末时间用 `date` 命令获取 |
| 15 | **编码洁净** | 所有中间文件与最终稿 UTF-8 无 BOM，无替换字符（�）/Mojibake/`???` |
| 16 | **纯文本公式** | 不用 LaTeX（`$...$`）；货币 `$` 写 `\$` |

---

## 1. 主 agent 调度流程

```
你（主 agent）的完整流程：

══ Setup（必须先执行）══

 → 创建带时间戳的临时目录 TMPDIR（如 /tmp/proposal-YYYYMMDD-HHMMSS 或 D:\TEMP\proposal-...）
 → 确定 TOOLSDIR（本 skill 的 tools/）、PROMPTSDIR（prompts/）、SKILLDIR（skill 根目录）
 → 读取本 SKILL.md + RULES.md + TYPES.md

══ Step 0 — 语言判定 ══

 → 分析标书/用户输入的主要语言，设 $LANG（政企标书默认 zh）。ISO 639-1 码，无法判定默认 zh
 → 写入 {TMPDIR}/language.txt
 → 从此刻起所有面向用户的输出用 $LANG。派发子 agent 时 prompt 中的 {LANG} 用此值

══ Step 0.5 — 标书摄入 + 模式解析 ══

 → **标书是必需输入**。判断用户如何提供标书：
   - 本地文件路径（.pdf/.docx/.md/.txt）→ 记入 {TMPDIR}/tender_paths.txt
   - 直接粘贴的标书文本 → 写入 {TMPDIR}/tender.txt
   - 既无路径也无文本 → 回复用户索要标书（"请提供标书文件路径或粘贴标书内容"），不继续
 → 识别用户额外素材（案例库/资质文件/报价参考/品牌手册路径）→ 记入 {TMPDIR}/materials.txt（可为空）
 → **案例库自动检测**：若 {SKILLDIR}/casebase/ 存在且含案例文件（.md，排除 _ 开头与 README）
   → 把该目录追加进 materials.txt 并标注 `[casebase]` 前缀——用户没传素材也能自动用上案例库
 → **模式解析**：用户输入末尾
   - ` -quick` → $DEPTH_MODE=quick（快速应标）
   - ` -deep`  → $DEPTH_MODE=deep（大标/重点）
   - 无后缀    → $DEPTH_MODE=standard（默认）
 → **叙事解析**（可与深度标志并用）：
   - ` -logic` / ` -story` / ` -vision` / ` -evidence` → $NARRATIVE=对应值（用户强制指定主叙事）
   - 用户在自然语言中明确表达叙事偏好（如"用讲故事的方式"）→ 映射到对应 $NARRATIVE
   - 无指定 → $NARRATIVE=auto（Task1 按 TYPES.md 叙事策略库判定）

══ 主流程 ══

 1. 记录开始时间到 {TMPDIR}/start_time.txt
 2. todowrite 创建进度条目（$LANG）
 3. ══ Task 1 — 标书解读 + 投标策略 + 方案框架 ══
    → 读取 {PROMPTSDIR}/task1_teardown.md，替换 {TMPDIR} {TOOLSDIR} {LANG} {MODE} {NARRATIVE} {CURRENT_YEAR}
    → 派发 task()，等待完成
    → 用 read 确认 {TMPDIR}/requirements.json 和 {TMPDIR}/strategy.json 存在
    → 运行 `python {TOOLSDIR}/prop_tools.py check-requirements {TMPDIR}/requirements.json`，
      确认 mandatory[]/scoring[] 结构完整、评分项含权重。不通过 → 重新派发 Task1 一次
    → read strategy.json 确认 narrative 完整（mode/through_line 存在、每章有 narrative_role）；缺失 → 重新派发 Task1 一次
    → 从 strategy.json 读取 title + sections 数 + depth_mode + narrative.mode；从 requirements.json 读取 scoring/mandatory 计数
    → todowrite 标记完成，向用户报告（$LANG）：标书类型、评分项数、预算带、差异化点数、叙事策略（mode + 一句 rationale）
 4. ══ Task 2 — 联网情报收集 ══
    → 读取 {PROMPTSDIR}/task2_intel.md，替换 {TMPDIR} {TOOLSDIR} {LANG} {COUNTRY} {CURRENT_YEAR}
      + {MATERIALS}（读取 {TMPDIR}/materials.txt 内容，空则空串）
    → 派发 task(category="unspecified-high")，等待
    → 失败（报错或 intel-pool.json 不存在）→ 自动重试 1 次，仍失败则向用户报告并终止
    → 读取 {TMPDIR}/task2_manifest.json，提取 source_count / case_count / fact_count / fetch_method / unique_domains
    → todowrite 标记完成，向用户报告（$LANG）
 5. ══ Task 3 — 并行分章撰写 ══
    → 读取 {TMPDIR}/strategy.json 的 sections 数组；读取 {TMPDIR}/intel-pool.json、{TMPDIR}/requirements.json
    → 读取 profiles.json 当前模式的 max_chars，计算 per_section_chars = max_chars ÷ sections.length
    → 读取 {PROMPTSDIR}/task3_section_agent.md 模板
    → 从 strategy.json 的 narrative 生成**全案叙事要点**（一次生成，各章共用）：主叙事 mode + TYPES.md 该模式的"章内写法/语言温度/风险禁忌"要点 + through_line + secondary（若有）
    → **并行派发各章**：
      - task_ids = []
      - For N = 1 to sections.length：
        - 读取 strategy.sections[N] 的 title、sub、addresses、narrative_role、intel_needs
        - 从 intel-pool.json 筛选与本章 addresses/intel_needs 相关的 facts/cases/insights，**直接嵌入 prompt**
        - 从 requirements.json 取本章 addresses 对应的评分项原文（评分标准），嵌入 prompt，让本章"照着评分标准写"
        - 组装 [本章叙事指令] = 全案叙事要点 + 本章 narrative_role，嵌入 prompt（报价/合规响应章补一句"本章一律逻辑与数据呈现"）
        - task(run_in_background=true) 派出，记录 background_task_id 到 task_ids
        - todowrite 标记该章 in_progress
      - task_ids 写入 {TMPDIR}/task3_bg_ids.json
      - 向用户报告"已并行派出 N 章，等待完成…"，结束 response
      - **仅当收到 [ALL BACKGROUND TASKS COMPLETE] 通知才进入 Round 2**，中间单章通知忽略
    → **Round 2 — 收集 + 失败重写**：
      - 读 {TMPDIR}/task3_bg_ids.json，对每个 id 调 background_output 收集
      - read 逐一确认 {TMPDIR}/sections/section-{N}.md 存在且非空
      - 缺失/空 → 串行重写该章（task run_in_background=false）
      - todowrite 标记完成，向用户报告
 6. ══ Task 4 — 装配 + 合规校验 + 自评分 + QA（主 agent 直接执行）══
    → **Step 0 清理**：删除 {SKILLDIR}/reports/ 下 0 字节文件；确保 {SKILLDIR}/reports/$LANG/ 存在
    → **Step 1 装配**：
      `python {TOOLSDIR}/prop_tools.py assemble-proposal --strategy {TMPDIR}/strategy.json --requirements {TMPDIR}/requirements.json --intel {TMPDIR}/intel-pool.json --sections-dir {TMPDIR}/sections/ --mode {depth_mode} --output {SKILLDIR}/reports/$LANG/ --lang $LANG`
      → 从输出 `Proposal assembled: <路径>` 提取路径设为 $REPORT
      → 装配会自动生成：封面标题、元数据块、目录、**应标响应与评分对照表**（从 strategy 的 section→addresses 映射反查生成）、正文各章（汉字编号）、参考来源、声明
    → **Step 2 ⚡ 合规校验（阻断点）**：
      `python {TOOLSDIR}/prop_tools.py check-compliance --requirements {TMPDIR}/requirements.json --strategy {TMPDIR}/strategy.json --report "$REPORT"`
      → 解析 JSON：`missing_mandatory`（未响应的强制项）、`missing_scoring`（未覆盖的评分项）、`coverage_pct`
      → **若 missing_mandatory 非空 → 有废标风险，必须补**：为每个缺失项定位应归属章节，重新派发该章 agent 补写对应响应 → 重新装配 → 重新校验，直到 missing_mandatory 为空
      → missing_scoring 非空同样补写（丢分项）
    → **Step 3 竞争力自评（机械信号）**：
      `python {TOOLSDIR}/prop_tools.py self-score --requirements {TMPDIR}/requirements.json --strategy {TMPDIR}/strategy.json --report "$REPORT" --mode {depth_mode}`
      → 解析 `SELFSCORE:` 行：estimated_score、addressed_pct、weak_items、diff_count、within_budget
    → **Step 3b 竞争力定性评估（LLM，在上下文内生成）**：
      用 Step 3 的机械信号 + 标书评分办法，在上下文内生成 2-4 句竞争力判断（$LANG）：
      预估处于什么水平、最强的差异化点、最需补强的评分项，以及叙事执行是否到位（抽读 1-2 章开头，
      判断是否符合 strategy.narrative 的讲法而非模板腔）。**这是内部竞争力研判，供用户参考，不写入交付文档。**
    → **Step 4 货币转义**：`python {TOOLSDIR}/prop_tools.py escape-currency "$REPORT"`
    → **Step 5 QA**：`python {TOOLSDIR}/prop_tools.py qa-proposal "$REPORT" --mode {depth_mode} --strategy {TMPDIR}/strategy.json --lang $LANG`
      → 解析 JSON，passed=true 则机械检查通过；不通过项局部补刀（单章重写最多 1 次）
    → **Step 6 清理**：删除 TMPDIR（Unix `rm -rf`，Windows `Remove-Item -Recurse -Force`）
    → todowrite 全部完成
    → ⏱ 计算总耗时（start_time.txt vs 当前）
    → 用 $LANG 向用户汇报最终结果（见下方汇报格式）

**禁止**：主 agent 不得在 Task 调度之间自行做联网搜索或情报处理。搜索/抓取归 Task2，标书解读归 Task1，撰写归 Task3，装配校验归 Task4。Task 间的 handoff 文件读取不受此限。
```

### 最终汇报格式（$LANG）

```
📋 **方案生成完成**

| 项目 | 详情 |
|:----|:------|
| 📑 方案 | {strategy.title} · {sections 数} 章 · {depth_mode} |
| 🎯 制胜主题 | {strategy.win_themes 前两条} |
| 🎭 叙事策略 | {narrative.mode 中文名}{secondary ? " + 辅助 " + secondary : ""} · {narrative.through_line} |
| 💡 Big Idea | {strategy.big_idea} |
| ✨ 差异化惊喜 | {diff_count} 个增值点（{列出 2-3 个 point}）|
| ✅ 合规 | 强制项 {addressed_mandatory}/{total_mandatory} · 评分项覆盖 {coverage_pct}% |
| 📊 竞争力自评 | 预估 {estimated_score} 分档 · 预算{within_budget ? "带内" : "⚠超预算"} → {llm_verdict} |
| ⚠ 待补强 | {weak_items 前几项，供用户人工强化} |
| 📄 文档 | {REPORT} |
| ⏱ 耗时 | {totalMin} 分钟 · 生成 {gen_time} |
```

> 竞争力自评是**机械信号 + LLM 研判**，非评委真实打分，仅供投标决策参考。`weak_items` 是建议人工强化的评分项。

---

## 2. Task 1 — 标书解读 + 投标策略 + 方案框架

**工具**：`task()` | 一次调用 | **prompt**：`prompts/task1_teardown.md`
**用法**：读取文件，替换 `{TMPDIR}` `{TOOLSDIR}` `{LANG}` `{MODE}` `{NARRATIVE}` `{CURRENT_YEAR}` 后注入。
**输出**（用 write 工具）：
- `{TMPDIR}/requirements.json` — 标书结构化拆解（mandatory[] / scoring[] 含权重 / budget_cap / deliverables）
- `{TMPDIR}/strategy.json` — 投标策略 + 方案框架（win_themes / differentiators / big_idea / **narrative**（mode/secondary/rationale/through_line）/ sections[] 含 addresses 映射与 narrative_role）

---

## 3. Task 2 — 联网情报收集

**工具**：`task(category="unspecified-high")` | **prompt**：`prompts/task2_intel.md`
**用法**：替换 `{TMPDIR}` `{TOOLSDIR}` `{LANG}` `{COUNTRY}` `{CURRENT_YEAR}` `{MATERIALS}`。
**输出**：`{TMPDIR}/intel-pool.json` + `{TMPDIR}/task2_manifest.json`

**LANG→COUNTRY 映射**：zh→CN, en→US, ja→JP, ko→KR, 其余按 ISO；未覆盖用空串。

搜索/抓取沿用运行时自适应策略：探测 CLI 内置搜索引擎（如 websearch）+ SearXNG + 免费源，Scrapling 批量抓取全文，webfetch 兜底。详见 prompt。

---

## 4. Task 3 — 分章撰写

主 agent 循环中为每章 `task()`，prompt 用 `{PROMPTSDIR}/task3_section_agent.md`。
**替换变量**：`[章节 title]` `[N]` `[total]` `[sub 列表]` `[本章评分标准]`（从 requirements 取 addresses 对应评分项原文）`[本章叙事指令]`（全案叙事要点 + 本章 narrative_role，见主流程）`[本章可用情报]`（嵌入的 facts/cases/insights）`{per_section_chars}` `{min_paragraphs}` `{MODE}` `{TMPDIR}` `{TOOLSDIR}` `{LANG}`。
**输出**：`{TMPDIR}/sections/section-{N}.md`（write 工具，只写正文不写 `##` 章标题）

---

## 5. Task 4 — 装配 + 合规 + 自评 + QA（主 agent 直接执行）

主 agent 通过 bash 直接调用 `{TOOLSDIR}/prop_tools.py`：

1. `assemble-proposal` → 生成方案文档（含应标响应与评分对照表）
2. `check-compliance` → ⚡ 合规校验（强制项/评分项零遗漏，阻断）
3. `self-score` → 竞争力机械自评（预估得分/覆盖率/薄弱项/预算合规）
4. `escape-currency` → 货币符号转义
5. `qa-proposal` → 全量质量检查（编码/结构/目录/元数据/对照表/差异化下限/字数）

---

## 6. 输出文件管理

- **路径优先级**：① 用户显式指定的输出目录 ② 默认 `{SKILLDIR}/reports/{LANG}/`
- **文件名**：`<方案标题>-YYYYMMDD-HHmmss.md`，日期用 `date` 命令
- **清理**：QA 通过后删除 TMPDIR
- **路径核验**：QA 确认报告在默认目录或用户指定目录，否则标"路径异常"

---

## 7. 工具依赖速查

| 工具 | 用途 | 归属 Task |
|:----|:-----|:--------|
| `websearch` / CLI 内置搜索 | 主力搜索（运行时探测） | Task2 |
| `searxng`（webfetch 访问 SearXNG JSON） | 补充搜索，含百度/搜狗等 | Task2 |
| `scrapling_bulk_get/stealthy/fetch` | 全文抓取（MCP，若已注册） | Task2 |
| `webfetch` | 抓取兜底 | Task2 |
| `prop_tools.py` | 装配/合规/自评/QA/编码 | Task4 |
| `read`/`write`/`glob` | 标书与素材读取、文件写入 | Task1/2/3 |
| `bash` | date 时间戳、pdf/docx 文本提取、调脚本 | 全流程 |

**标书文件读取**：`.md/.txt` 直接 read；`.pdf` 先 read 尝试，失败则 `pip install pypdf2 -q` 提取；`.docx` `pip install python-docx -q` 提取。提取到 `.txt` 后再 read（纯 I/O，豁免"禁止内联代码"铁律）。

---

## 8. 容错原则

- 所有脚本调用有兜底：主路径失败 → 换 `sys.executable` / 检查路径 / 直接 Python 实现 → 三次失败向用户报告具体问题
- Task2 联网失败不阻塞：抓不到的情报在 intel-pool 标 gap，方案照常生成（相应章节用标书+素材+专业判断补，并在自评中提示情报受限）
- Scrapling 不可用 → 全量 webfetch，标注抓取方式
- `check-compliance` 是**唯一硬阻断点**——强制项有遗漏必须补齐才能交付

---

## 9. 编码规范（跨平台）

沿用「非 ASCII 文本不进 shell argv/pipe」原则：
- 写文件只用 `write` 工具（UTF-8 无 BOM）
- Python 脚本统一 `--input`/`--output` 文件参数，`stdout.reconfigure('utf-8')`，读用 `encoding='utf-8-sig'`
- 中间文件与最终稿必须 UTF-8 无 BOM，无替换字符/Mojibake

---
```
proposal skill · 政企传媒投标方案生成
```
