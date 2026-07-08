---
name: proposal
description: "政企传媒投标方案生成 — 多 agent 协作：标书解读拆评分项、按标选叙事（逻辑征服/故事打动/愿景共创/数据实证）、联网调研甲方/行业/竞品/案例、并行分章撰写、方案综述、红队四视角评审、应标响应对照表零遗漏校验。两道人工关卡（策略确认 / 红队定稿）把 AI 不该替人决定的判断交回投标人。"
version: 2.0.0
updated: 2026-07-08
risk: medium
---

# proposal

为广告/传媒公司生成给**政企客户**投标的方案文档。目标：在**保证基础合规（不废标、覆盖全部评分项）**的前提下，用**合理成本的单一最优解**，配**贴合本标的叙事策略**（逻辑征服/故事打动/愿景共创/数据实证，见 TYPES.md 叙事策略库），给甲方**最大惊喜**，从众多提案中脱颖而出。

- **输入**：甲方标书（本地文件 pdf/docx/md/txt，或粘贴文本）+ 可选的用户素材（资质/报价参考/**沟通纪要**）；`{SKILLDIR}/casebase/` 有案例时自动筛选纳入（无需传路径）
- **架构**：主 agent 调度 —— Task1 标书解读+投标策略（含叙事判定） → **⛳ Gate 1 策略确认（人）** → Task2 联网情报 → Task3 并行分章撰写（按叙事指令）→ Task3.5 方案综述 → Task4 装配+合规校验+自评+红队四视角+人工待办 → **⛳ Gate 2 红队定稿（人）**
- **人机分工**：AI 负责拆解、调研、撰写、校验；**人负责 AI 不可能知道的判断**——我司真实能力边界、报价心理价位、竞争对手、与甲方的关系、领导偏好。两道关卡就是把这些交回给人。`-auto` 可跳过关卡
- **情报来源**：联网为主（甲方画像/行业趋势/竞品打法/标杆案例）+ 标书 + 用户素材
- **输出**：**技术标卷册目录** `{SKILLDIR}/reports/{LANG}/<方案标题>-<时间戳>/`
  - `技术方案-完整版.md` — 递交稿（合并版，拼 Word 用）
  - `分册/NN-*.md` — 递交稿分册（目录 / 对照表 / 方案综述 / 各章，便于单章重写）
  - `_内部研判.md` — ⚠️ **不递交**：生成参数、叙事策略、情报 URL、竞争力信号
  - `_人工待办.md` — ⚠️ **不递交**：AI 不该替你编造的内容清单
  - 范围只到**技术标**。投标函/授权书/承诺函/报价一览表等格式文本按标书模板自行套用
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
| 8 | **来源可追溯** | 正文数据**行内标注**来源（「据XX研究院2026年报告」）。URL 清单只进 `_内部研判.md`，**递交稿不带网址书目**（那是研报，不是投标文件） |
| 9 | **真实不虚构** | 业绩/资质/团队真实；无把握处写"拟"或留占位符，不编造 |
| 10 | **标题含主张** | "3个月引爆城市声量"✅ \| "传播方案"❌ |
| 11 | **风险有预案** | 关键风险配应对措施 |
| 12 | **零套话** | 无"我们将竭诚服务""众所周知"等填充词 |
| 13 | **卷册结构** | 递交稿：标题 → 项目信息头 → `## 目录`（纯文本，无锚点）→ `## 应标响应与评分对照表` → `## 方案综述` → 正文各章。**没有元数据块、没有参考来源书目、没有研报式声明** |
| 14 | **零内部泄露** ⚡ | 递交稿不得出现：叙事策略、深度模式、工具版本、生成时间、阅读时间、字数、URL。这些一律进 `_内部研判.md`。`qa-proposal` 的 `no_internal_leak` 是**硬阻断** |
| 15 | **编码洁净** | 所有中间文件与最终稿 UTF-8 无 BOM，无替换字符（�）/Mojibake/`???` |
| 16 | **纯文本公式** | 不用 LaTeX（`$...$`）；货币 `$` 写 `\$` |
| 17 | **方案综述前置** | 对照表之后有一页 `## 方案综述`（Task3.5 在各章写完后提炼），评委只精读前两页 |
| 18 | **甲方导向** | `qa-proposal` 的 `buyer_focus.ratio` ≥ 0.8（甲方提及数 / 我方提及数）。低于此值说明在自夸而非解决甲方问题 |
| 19 | **引用可公开** | 只引标书原文/答疑澄清文件/公开政策/公开报道。**私下沟通、售前会议中的甲方个人表述绝不进正文**（不正当接触嫌疑） |
| 20 | **无销售话术** | 投标是密封递交，**没有 CTA**。禁止"下一步行动/期待沟通/签约条款"；禁止"排除项"式免责（易认定负偏离） |

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
 → **沟通纪要识别**：用户提供的踏勘记录/答疑会纪要/售前沟通笔记 → 在 materials.txt 中以 `[notes]` 前缀标注
   ⚡ 这是标书没写的甲方真实诉求，喂给 Task1 校准 buyer_insight
   🚫 但只作 AI 理解输入，**绝不进方案正文**（引用私下沟通 = 不正当接触嫌疑，见质量标准 #19）
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
 → **关卡解析**：
   - ` -auto` → $GATES=off（全自动跑完，不停顿。适合无人值守或初稿快评）
   - 无标志   → $GATES=on（默认）：standard/deep 停 Gate 1 + Gate 2；quick 只停 Gate 1

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
    → read strategy.json 确认 open_questions 非空（deep ≥5 条，其余 ≥3 条）；为空 → 重新派发 Task1 一次
    → 从 strategy.json 读取 title + sections 数 + depth_mode + narrative.mode；从 requirements.json 读取 scoring/mandatory 计数
    → todowrite 标记完成
 3b. ══ ⛳ Gate 1 — 策略确认（人工关卡）══  【$GATES=off 时整段跳过，直接进 Task 2】

    **为什么停在这里**：策略错了，后面所有联网调研和分章撰写全是浪费。而策略里最关键的几个判断，
    AI 无论怎么读标书都不可能知道——只有投标人本人知道。

    → 用 $LANG 向用户呈现（表格形式，简洁）：

    ```
    📋 投标策略待确认

    | 项目 | AI 的判断 |
    |:----|:---------|
    | 🎯 甲方洞察 | {buyer_insight} |
    | 💡 Big Idea | {big_idea} |
    | 🎭 叙事策略 | {narrative.mode}（{narrative.rationale}）· 主线：{through_line} |
    | ✨ 差异化点 | {differentiators 逐条：point → why_wow → 对应评分项} |
    | 💰 报价思路 | {budget_strategy} · 预算带 {budget_cap} |
    | 📑 章节框架 | {sections 逐条：n. title（覆盖评分项数）} |

    ⚠️ 以下判断 AI 不可能知道，需要你拍板：
    {open_questions 逐条：q → 「不确认的后果：why_matters」→ 「AI 目前假设：ai_assumption」}
    ```

    → **用 AskUserQuestion 工具**（若可用）把 open_questions 中最关键的 2-4 条做成选择题；
      或直接结束 response 等用户回复。**不得自行假设后继续。**
    → 用户可能：① 确认全部 → 继续  ② 修改某项（改 Big Idea/叙事/差异化/报价/章节）
      ③ 回答 open_questions  ④ 要求重做策略
    → 根据用户反馈**用 write 更新 {TMPDIR}/strategy.json**（把确认后的答案并入 buyer_insight/differentiators/budget_strategy，
      并把 open_questions 中已确认的条目标 `"resolved": "<用户的答复>"`），必要时同步 requirements.json
    → 更新后 read 确认，再进 Task 2

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
 5b. ══ Task 3.5 — 方案综述（执行摘要）══

    ⚠️ **必须在全部章节完成之后串行执行**——摘要是从写成的正文里提炼的，不是从策略推演的。
    → 读取 {PROMPTSDIR}/task3b_exec_summary.md，替换 {TMPDIR} {LANG} {TOTAL}（章数）
      {EXEC_CHARS}（quick 600 / standard 800 / deep 1000）
      {NARRATIVE_BLOCK}（同 Task3 的全案叙事要点）
    → 派发 task()（run_in_background=false），等待完成
    → read 确认 {TMPDIR}/sections/section-0.md 存在且非空；缺失 → 重试一次，仍失败则跳过（装配会自动省略综述，QA 给警告）
    → todowrite 标记完成

 6. ══ Task 4 — 装配 + 合规校验 + 自评分 + 红队 + QA（主 agent 直接执行）══
    → **Step 0 清理**：删除 {SKILLDIR}/reports/ 下 0 字节文件；确保 {SKILLDIR}/reports/$LANG/ 存在
    → **Step 1 装配**：
      `python {TOOLSDIR}/prop_tools.py assemble-proposal --strategy {TMPDIR}/strategy.json --requirements {TMPDIR}/requirements.json --intel {TMPDIR}/intel-pool.json --sections-dir {TMPDIR}/sections/ --mode {depth_mode} --output {SKILLDIR}/reports/$LANG --lang $LANG`
      → 从 `Proposal assembled: <路径>` 取 $REPORT（合并版递交稿，后续校验都跑它）
      → 从 `BundleDir: <路径>` 取 $BUNDLE；从 `InternalBrief: <路径>` 取 $BRIEF
      → 装配自动生成：标题、项目信息头、纯文本目录、**应标响应与评分对照表**（从 strategy 的
        section→addresses 映射反查）、方案综述、正文各章（汉字编号）、`分册/` 各文件、`_内部研判.md`
      → ⚠️ 递交稿里**没有**元数据块 / URL 书目 / 研报声明——这些是研报残留，一律在 `_内部研判.md`
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
    → **Step 5 QA**：`python {TOOLSDIR}/prop_tools.py qa-proposal "$REPORT" --mode {depth_mode} --strategy {TMPDIR}/strategy.json --requirements {TMPDIR}/requirements.json --lang $LANG`
      → 解析 JSON，passed=true 则机械检查通过；不通过项局部补刀（单章重写最多 1 次）
      → ⚡ **`no_internal_leak` 失败必须修**：递交稿混进了叙事策略/模式/版本/生成时间/URL 等内部信息。
        定位到具体章节（多半是某章正文写了 URL 或"本方案采用故事化叙事"之类的自我描述）→ 重写该章 → 重装配
      → 警告级信号（`buyer_focus` / `exec_summary` / `no_sales_cta` / `no_latex` / `no_id_leak`）不阻断，
        但**必须带进 Gate 2 给人看**。`buyer_focus.ratio < 0.8` 说明方案在自夸 → 建议人工复看各章开篇
    → **Step 6 🔴 红队评审（四视角并行）**：
      → mkdir {TMPDIR}/redteam/
      → 读取 {PROMPTSDIR}/task4_redteam.md 模板；从 TYPES.md「红队四视角」取四个角色的
        `{ROLE_KEY}` `{ROLE_NAME}` `{ROLE_BRIEF}`：`buyer`（采购人代表）/ `expert`（技术专家）/
        `audit`（财务纪检）/ `rival`（竞争对手）
      → **并行派发 4 个 task(run_in_background=true)**，各自替换 {ROLE_*} {REPORT} {TMPDIR} {LANG}
      → 仅当收到 [ALL BACKGROUND TASKS COMPLETE] 才继续；read 确认四个 {TMPDIR}/redteam/{role}.json
      → 汇总：按 severity 归并（致命 → 重要 → 次要），同一 target 的重复质疑合并
      → **致命项（废标风险 / 高权重评分项实质未答）不进 Gate 2 等人——先自动补**：
        定位归属章节 → 重新派发该章 agent 补写 → 重新装配 → 重跑 check-compliance → 最多 2 轮
    → **Step 7 人工待办清单 + 内部研判归档**：
      设 $TODO = "$BUNDLE/_人工待办.md"（下划线前缀 = 不递交）
      `python {TOOLSDIR}/prop_tools.py human-todo --requirements {TMPDIR}/requirements.json --strategy {TMPDIR}/strategy.json --report "$REPORT" --mode {depth_mode} --output "$TODO" --lang $LANG`
      → 解析 `HUMANTODO:` 行：blocking_count / scoring_count / weak_count
      → 用 write 把 **Step 3/3b 的竞争力自评 + Step 6 的红队结论**追加进 $BRIEF（`_内部研判.md`），
        这样卷册自带一份完整的内部备忘，TMPDIR 删掉也不丢
    → **Step 8 ⛳ Gate 2 — 红队定稿（人工关卡）**  【$GATES=off 或 quick 模式时跳过，直接 Step 9】

      **为什么停在这里**：红队只提质疑，不改稿。哪些必须补、哪些是红队想多了、哪些暴露了真实能力缺口
      需要调整策略甚至弃标——这是投标人的判断，不是 AI 的。

      → 用 $LANG 呈现：
      ```
      🔴 红队评审结果（定稿前）

      | 视角 | 判断 | 致命 | 重要 | 次要 |
      |:----|:----|:---:|:---:|:---:|
      | 采购人代表 | {overall_verdict} | n | n | n |
      | 技术专家   | … | | | |
      | 财务纪检   | … | | | |
      | 竞争对手   | … | | | |

      ⚔️ 对手会怎么打你：{rival.if_i_were_competitor}
      🛡️ 方案最能打的地方：{各视角 strongest_point 归并}

      【重要级质疑】逐条：target · quote · issue · why_it_costs · fix
      【机械信号】甲方导向比 {buyer_focus.ratio}（阈值 0.8）· 综述 {有/无} · 销售话术残留 {…} · 内部泄露 {无/已修}
      【人工待办】废标风险 {blocking_count} 项 · 丢分 {scoring_count} 项 → {$TODO 路径}
      ```
      → 用 AskUserQuestion（若可用）让用户挑要补的质疑；或结束 response 等回复
      → 用户选定后：局部补写对应章节 → 重新装配 → 重跑 check-compliance + qa → 再报告
      → 用户说"可以了" → 进 Step 9
    → **Step 9 清理**：删除 TMPDIR（Unix `rm -rf`，Windows `Remove-Item -Recurse -Force`）
      ⚠️ `_人工待办.md` 与 `_内部研判.md` 在卷册目录 $BUNDLE 内，不在 TMPDIR，不会被删
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
| 📊 竞争力自评 | 预估 {estimated_score} 分档 · 预算{within_budget ? "带内" : "⚠超预算"} · 甲方导向比 {buyer_focus.ratio} → {llm_verdict} |
| 🔴 红队 | 致命 {已补 n} · 重要 {n}（{已采纳 m}）· 对手威胁：{if_i_were_competitor 摘要} |
| 📝 人工待办 | 废标风险 {blocking_count} 项 · 丢分 {scoring_count} 项 |
| 📁 卷册 | {BUNDLE} |
| 📄 递交稿 | 技术方案-完整版.md · 分册/ {part_count} 个文件 |
| 🔒 不递交 | _内部研判.md · _人工待办.md |
| ⏱ 耗时 | {totalMin} 分钟 |
```

> 竞争力自评是**机械信号 + LLM 研判**，非评委真实打分，仅供投标决策参考。
> ⚠️ **下划线开头的两个文件不要递交**——`_内部研判.md` 里有你的叙事策略和情报 URL，给评委看等于亮底牌。
> **交付前请务必过一遍 `_人工待办.md`**——里面是 AI 不该替你决定或编造的内容（真实业绩、报价数字、团队人员、可承诺的 KPI）。废标风险项没填完就递交，方案再好也是零分。
> 本 skill 只产出**技术标**。投标函、法定代表人授权书、承诺函、报价一览表等格式文本请按标书模板自行套用。

---

## 2. Task 1 — 标书解读 + 投标策略 + 方案框架

**工具**：`task()` | 一次调用 | **prompt**：`prompts/task1_teardown.md`
**用法**：读取文件，替换 `{TMPDIR}` `{TOOLSDIR}` `{LANG}` `{MODE}` `{NARRATIVE}` `{CURRENT_YEAR}` 后注入。
**输出**（用 write 工具）：
- `{TMPDIR}/requirements.json` — 标书结构化拆解（mandatory[] / scoring[] 含权重 / budget_cap / deliverables）
- `{TMPDIR}/strategy.json` — 投标策略 + 方案框架（win_themes / differentiators / big_idea / **narrative**（mode/secondary/rationale/through_line）/ **open_questions[]**（只有投标人知道的判断，Gate 1 拿它问人）/ sections[] 含 addresses 映射与 narrative_role）

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

## 4b. Task 3.5 — 方案综述（执行摘要）

**工具**：`task()` | 一次调用 | **prompt**：`prompts/task3b_exec_summary.md`
**时机**：**全部章节完成之后**，串行执行。摘要从写成的正文里提炼，不从策略推演。
**替换变量**：`{TMPDIR}` `{LANG}` `{TOTAL}` `{EXEC_CHARS}`（quick 600 / standard 800 / deep 1000）`{NARRATIVE_BLOCK}`
**输出**：`{TMPDIR}/sections/section-0.md`（只写正文，装配自动加 `## 方案综述` 标题并置于对照表后、正文各章前；不参与章节编号）

---

## 5. Task 4 — 装配 + 合规 + 自评 + 红队 + QA（主 agent 直接执行）

主 agent 通过 bash 直接调用 `{TOOLSDIR}/prop_tools.py`，红队部分派 4 个 agent：

1. `assemble-proposal` → 生成**技术标卷册目录**：递交稿（合并版 + 分册）+ `_内部研判.md`（不递交）
2. `check-compliance` → ⚡ 合规校验（强制项/评分项零遗漏，**唯一硬阻断点**）
3. `self-score` → 竞争力机械自评（预估得分/覆盖率/薄弱项/预算合规）
4. `escape-currency` → 货币符号转义
5. `qa-proposal --requirements ...` → 全量质量检查（编码/卷册结构/对照表/差异化下限/字数 + ⚡**内部信息泄露（硬阻断）** + 甲方导向词频/综述存在/销售话术残留（警告级））
6. **红队四视角**（`prompts/task4_redteam.md` × 4 并行，角色见 TYPES.md）→ `{TMPDIR}/redteam/{role}.json`；致命项自动补，其余进 Gate 2
7. `human-todo` → 汇总正文占位符 + 薄弱项，按「不处理的后果」排序，产出 `_人工待办.md`（卷册目录内，**不随 TMPDIR 删除**）

---

## 6. 输出文件管理

- **路径优先级**：① 用户显式指定的输出目录 ② 默认 `{SKILLDIR}/reports/{LANG}/`
- **卷册目录名**：`<方案标题>-YYYYMMDD-HHmmss/`，同名旧卷册自动删除（装配时按 title 去重）
- **递交 vs 不递交**：下划线 `_` 开头的文件**一律不递交**（`_内部研判.md` / `_人工待办.md`）
- **清理**：QA 通过后删除 TMPDIR（红队 JSON 随之删除；结论已追加进 `_内部研判.md`）
- **路径核验**：QA 确认递交稿在卷册目录内，否则标"路径异常"

---

## 7. 工具依赖速查

| 工具 | 用途 | 归属 Task |
|:----|:-----|:--------|
| `websearch` / CLI 内置搜索 | 主力搜索（运行时探测） | Task2 |
| `searxng`（webfetch 访问 SearXNG JSON） | 补充搜索，含百度/搜狗等 | Task2 |
| `scrapling_bulk_get/stealthy/fetch` | 全文抓取（MCP，若已注册） | Task2 |
| `webfetch` | 抓取兜底 | Task2 |
| `prop_tools.py` | 装配/合规/自评/QA/人工待办/编码 | Task4 |
| `task()` × 4 并行 | 红队四视角评审 | Task4 Step 6 |
| `AskUserQuestion`（若可用） | Gate 1 策略确认、Gate 2 质疑取舍 | 两道关卡 |
| `read`/`write`/`glob` | 标书与素材读取、文件写入 | Task1/2/3 |
| `bash` | date 时间戳、pdf/docx 文本提取、调脚本 | 全流程 |

**标书文件读取**：`.md/.txt` 直接 read；`.pdf` 先 read 尝试，失败则 `pip install pypdf2 -q` 提取；`.docx` `pip install python-docx -q` 提取。提取到 `.txt` 后再 read（纯 I/O，豁免"禁止内联代码"铁律）。

---

## 8. 容错原则

- 所有脚本调用有兜底：主路径失败 → 换 `sys.executable` / 检查路径 / 直接 Python 实现 → 三次失败向用户报告具体问题
- Task2 联网失败不阻塞：抓不到的情报在 intel-pool 标 gap，方案照常生成（相应章节用标书+素材+专业判断补，并在自评中提示情报受限）
- Scrapling 不可用 → 全量 webfetch，标注抓取方式
- Task3.5 综述失败 → 跳过（装配自动省略，QA 给警告），不阻塞交付
- 红队某一视角失败 → 用剩余视角继续，Gate 2 标注"{role} 视角缺失"；四个全失败 → 跳过红队，Gate 2 只报机械信号
- `check-compliance` 是**唯一硬阻断点**——强制项有遗漏必须补齐才能交付
- **Gate 1/2 不得自行跳过**（除非 $GATES=off）。等不到用户回复就结束 response，不许"替用户假设后继续"

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
