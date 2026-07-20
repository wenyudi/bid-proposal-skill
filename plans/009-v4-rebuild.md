# Plan 009 — proposal v4 轻量重建：商业方案 + 默认图片 PPT 交接

| 字段 | 值 |
|:---|:---|
| 状态 | DONE — 2026-07-20 实施完成；工具 14 tests 绿、四类坏例正确 fail；未跑端到端真实 /proposal（见 §10.9，属验收续项）|
| 优先级 / 工作量 | P0 / L |
| 依赖 | 无。本计划取代 001–008 的 v3 路线图（它们保留为历史存档） |
| 来源 | 2026-07-20 会话定稿：Opus 4.8 设计 → Fable 5 评审补强 → 用户逐项拍板 |

执行者须知：开始前完整读完本文件；**第一个动作是 STOP-1 的 git tag**，之后才允许改动任何文件。SKILL.md 与 description 的写法遵循 writing-great-skills 原则（正向提示、leading words、每步可检查的完成判据、description 触发词前置）；反模式材料只进复核侧，生成侧不读。

## 0. 一句话目标

把 proposal 从政企技术标重型引擎（5-canonical 状态机 + 硬门）重建为**低仪式、高工艺**的商业方案技能：给材料 → 评分表拆解 + 制胜一页纸（唯一一次人工确认）→ 并行分章写作（缺口虚构 + 源头申报）→ ≤3 轮制胜复核 → 响应对照索引 + 默认图片 PPT 结构稿 → 文件交接 image2。**砍状态机，不砍工艺。**

## 1. 已拍板决策（实施中不得重开）

1. 重建本体，不做姊妹 skill；重引擎整体退役进 git 历史（tag `v3.4.0-heavy`），不保留运行时兼容、不留 `-legacy` 回退链。
2. PPT 结构稿是**默认产出**；`-no-ppt` 跳过。
3. 无深度、无叙事旋钮（`-quick`/`-deep`/`-logic` 等全部移除）；永远尽力做到最好。叙事仍按标型**自动**选择（`narratives.json`），只是没有用户标志。
4. 素材缺口→**具体、可信地虚构补全**，正文零"待确认"空洞、零占位符残留；每处虚构在写作源头申报，汇总进 `_风险与待核实.md`（按 权重×风险 排序的"做实清单"）。存在虚构或 `-auto` 时，最终汇报首句硬提示"核实前不可直接递交"。
5. 评分纪律保留但**模型驱动**：评分表拆解、地板（客观/mandatory 零失分）/天花板（高权重主观项差异化）、响应对照索引、制胜复核循环。不引入 requirements.json 生命周期或任何硬门状态机。
6. 图片管线走**文件交接**（image2 本机未装，proposal 不调图片模型）：`_PPT生产包/outline.md + deck-blueprint.json`；blueprint v1 **只加可选字段，不改已有字段语义**。证据类图片永不 `generate`。
7. flags 只有 `-no-ppt`、`-auto`（`-auto` 跳过唯一人工确认，产草案并登记 assumed）。

## 2. 保留 / 退役总表

| 处置 | 对象 |
|:---|:---|
| **退役**（从工作树删除；git 历史 + tag 保底） | `RULES.md`、`DECISIONS.md`、`TYPES.md`、`LEGACY.md`；`prompts/` 现有 9 个 prompt 与 `prompts/legacy/` 全部；`tools/prop_v3.py`；旧 `tools/prop_tools.py` 全部子命令；`profiles.json`；`references/strategy-rubric.md`；`docs/` 除 `docs/reference/presentation-blueprint.md` 外全部；`tests/` 旧用例。概念层面：5-canonical、ChangeSet、snapshot/freeze、两级 readiness、Gate 1/2、独立 realization audit、customer-fit 十维、receipt/validate-run/finalize-run、migrate/resume |
| **保留并改写** | 仓库 `SKILL.md`；宿主入口 `/home/raul/.agents/skills/proposal/SKILL.md`；`README.md`；`CONTRIBUTING.md`；`VERSION`（→ `4.0.0`）；`docs/reference/presentation-blueprint.md`；`references/strategy-patterns.md`、`writing-patterns.md`、`presentation-patterns.md`、`anti-patterns.md`、`contrast-examples.md`；`narratives.json`；`tools/prop_tools.py`（全新，仅两个子命令）；`tests/`（全新） |
| **保留不动** | `casebase/` 全部（含 `_quality-lessons/`，用户资产）；`plans/001-008` 与 `reports/`、`.scratch/`（历史）。`plans/README.md` 仅更新 009 状态行 |
| **检查后对齐** | `command/`、`install/`、`agents/` 三个目录：逐个检查内容，更新引用 v3 概念（RULES/Gate/canonical/-deep 等）的注册文本、安装说明、agent 定义；确属 v3 专用的文件退役 |

## 3. 新 SKILL.md 规格

结构（目标 ≤120 行）：frontmatter → 定位段 → 交付 → 缺口补全与风险登记 → 主流程五步 → 汇报。

**description 基线**（可润色，触发词不可丢）：
> 商业方案与投标方案生成 v4：给材料，拆评分表，收敛制胜一页纸，并行写出成熟正文，缺口虚构补全并登记风险，产出响应对照索引与图片 PPT 结构稿交给下游图片工作流。Use when 用户要写商业方案、投标/应标方案、客户提案、PPT 提案前置稿，给一批材料要出完整方案，或输入 /proposal。

**leading words** 贯穿全文：**评分表**（骨架）、**地板/天花板**（客观零失分 / 高权重差异化）、**一页纸**（主张与拿分打法）、**主线**（贯穿正文）、**申报/登记**（虚构可追溯）、**对照索引**（覆盖证明）、**signature**（制胜一击）。

路径约定沿用宿主入口：仓库相对路径从 `/home/raul/Code/proposal` 解析；Python 优先 `python3`。各 prompt 文件头列出自己的占位变量（如 `{PER_SECTION_CHARS}`），SKILL.md 指明由主 agent 赋值；只保留必要变量。

### Step 1 摄入、评分表拆解与制胜一页纸（`prompts/task1_strategy.md`，高推理）

- 输入：标书/brief（必需）+ 素材（能力、案例、报价、团队、品牌）。`casebase/` 非 `_` 开头案例自动纳入；`[notes]` 纪要只作内部校准，不入正文、不引原句。
- **产物 A**：评分表拆解，落 `_研判.md` + `_score-table.json`（有评分表时）：每项 `id/原文/权重/kind`（floor＝客观、mandatory、格式、交付物；ceiling＝高权重主观项）。**无评分表分支**：跳过 JSON，把 brief 中客户的明确诉求整理成 floor 清单落 `_研判.md`，后续 lens① 与对照索引以它为准（索引文件本身跳过）。
- 研究：需要外部证据时抓原文（WebFetch/WebSearch），不用搜索摘要充数；抓不到→虚构补全并申报。
- **产物 B**：制胜一页纸（落 `_研判.md`）：客户张力 / 尖锐洞察 / 核心主张 + 十秒记忆句 / 推导链（洞察→策略→表达→执行→证明）/ **最强替代命题 + 为何不选（决定性依据）** / 互换测试结论（换成竞争对手是否仍成立）/ 拿分打法（地板怎么保、天花板怎么顶）/ 逐章骨架（每章：独有贡献、认领的评分项、按权重分配的 `{PER_SECTION_CHARS}` 篇幅上限——ceiling 非填满目标、与前后章的交接）/ 唯一 signature 主亮点指定 / 叙事选择（自 `narratives.json` 按标型自动选，短 guide 进 writer brief）。
- 发散纪律：先发散 ≥3 个主张角度再按 短板+差异化 收敛，被否角度各留一句理由。
- **唯一人工确认**："是否按这一页写？" 展示：主张与记忆句、最强替代与为何不选、拿分打法、逐章骨架。要改→回本步改根因。`-auto`→跳过，登记 assumed。
- 完成判据：一页纸各字段齐全；每个评分项被且仅被合理章节认领；互换测试有结论；（有评分表时）`_score-table.json` 与拆解一致。

### Step 2 分章写作（`prompts/task2_section.md` 并行 + `prompts/task2b_summary.md` 串行）

- 每个 writer brief 固定携带：一页纸全文、全案章节骨架、本章独有贡献/认领评分项/篇幅上限、前后章交接、叙事短 guide、`references/writing-patterns.md`。
- 要求：地板项逐项应答且可定位；高权重项用主张 + 具体证据写深；每章以客户任务/结果开篇、标题含主张、创意配动作/责任/时点，不以我司自夸开篇；套话删整句重写；缺口具体虚构，不写空洞套话也不留占位符。
- writer 返回**双产物**：`_sections/section-N.md` + 本章虚构申报（结构化：位置 / 虚构了什么 / 应核实或替换为什么 / 风险等级）。可在文中标"建议配图点"。
- 综述章在其余章定稿后**串行**写（task2b），只合成、不新增主张或承诺。
- 完成判据：全部章节齐；认领评分项全部有可定位应答；每章虚构申报随文到位。

### Step 3 制胜复核（`prompts/task3_review.md`，循环 ≤3 轮）

- 每轮**并行 3 个独立 agent**（均与 writer 分离）：
  - **lens① 覆盖审计**：逐项对照 `_score-table.json`（或 brief 诉求清单）查应答存在且可定位；漏项/弱项按权重排序返回。
  - **lens② 对手视角**：只看高权重章，问"换成竞争对手还成立吗？评委凭什么选我们？"，专抓"合规但空"；用 `contrast-examples.md` + `anti-patterns.md` 校准。
  - **lens③ 文风与登记**：主线是否贯穿、套话、递交稿禁项、虚构漏报抽查（对照输入素材查可疑的具体性）。
- 主 agent 合并为根因列表（根因/位置/权重/建议修法）→ 升级弱章（改稿或重派对应 writer）→ 再循环。
- **通过判据**：无地板缺口、无空心高权重章、无主线断裂；文风与漏报项修复完。
- 到 3 轮仍有残留→停止循环，残留**如实**写进汇报与 `_风险与待核实.md`，不静默通过。

### Step 4 定稿产物编译（含 `prompts/task4_blueprint.md`）

1. 合并全部虚构申报 → `_风险与待核实.md`：按 权重×风险 排序；每条含所在章节（及后续 slide 页码）、虚构内容、应核实/替换为什么、不核实的后果。
2. 组装 `方案正文.md`：章序、编号统一、零占位符。
3. 有评分表→生成 `响应对照索引.md`：评分项 | 权重 | 章节位置（**确切章节标题**）| 覆盖状态（完整/部分/虚构补全）。随后：
   `python3 tools/prop_tools.py validate-index --index <索引> --doc <正文> --score-table <_score-table.json> [--risk <_风险与待核实.md>]`
   失败→修→重跑。顺序固定：复核循环通过 → 生成索引 → validate-index，不再回模型。
4. 默认 PPT（`-no-ppt` 跳过）：task4_blueprint 读定稿正文 + 一页纸 + 素材清单（收割"建议配图点"）→ `deck-blueprint.json`：
   - core/appendix 双轨：core 最短说服链 + 1–2 张决定性效果图；appendix 承接**效果图系列**、长名单、尺寸材质、预算、风险查验；
   - 唯一 signature 页 = 下游样张页（`sample_slide_ref`）；
   - 每页生成简报：主画面 / 构图 / prompt seed / **规避元素** / 比例；`render_text` 准确上屏文案；素材三模式（`generate`/`strict_input`/`style_reference`）；页级**虚构标注**；
   - `visual_system` 风格锚从品牌素材 / style_reference 提取一次，全案统一；
   - **证据图红线**：`generate` 只用于效果图/示意图（对未来方案的想象）；过往案例现场、资质、数据截图等证据图必须 `strict_input` + `needs_user` 真实素材并进风险登记。
   然后：`python3 tools/prop_tools.py validate-blueprint --blueprint <blueprint> --output-dir <bundle>/_PPT生产包`（校验 + 确定性写 `outline.md`）。
- 完成判据：validate-index 与 validate-blueprint 全绿；`_风险与待核实.md` 覆盖全部申报（含页级标注）。

### Step 5 汇报

- 首句（存在虚构或 `-auto`）："已生成草案，含 N 处虚构占位（见 `_风险与待核实.md`），核实前不可直接递交。"
- 主体：标题 / 一句核心主张 + 记忆句 / 章数 / 评分覆盖状态（含复核残留，如实）/ top 待核实 3 条（权重×风险）/ 卷册路径。
- PPT 部分：页数 / signature 页 / `needs_user` 素材数 / 生产包路径，并给下一步一行："把 `_PPT生产包` 交给 image2 继续样张确认与逐页生成。"

## 4. 运行目录

```
<方案标题>-<时间戳>/
├── 方案正文.md                 客户可读递交稿
├── 响应对照索引.md             有评分表时；交付级
├── _PPT生产包/
│   ├── outline.md
│   ├── deck-blueprint.json
│   └── presentation-validation.json
├── _风险与待核实.md            内部：虚构/假设做实清单（权重×风险排序）
├── _研判.md                    内部：评分表拆解、一页纸、被否替代、来源
├── _score-table.json           内部：机器可读评分表（有评分表时）
└── _sections/                  内部：分章工作文件
```

`_` 前缀一律不递交。直接在用户指定位置（默认当前目录）建目录，无 staging/原子切换仪式。

## 5. Prompt 契约（5 个，全部新写；每个都用"交付目标 → 依据 → 工作顺序 → 输出契约"结构）

| 文件 | 取代 | 要点 |
|:---|:---|:---|
| `task1_strategy.md` | task1_teardown + task2_intel + task2b_value_selection | §3 Step 1 全部要求；先拆表落盘再发散收敛；读 `strategy-patterns.md` |
| `task2_section.md` | task3_section_agent | §3 Step 2；含虚构申报输出契约、建议配图点、叙事 guide 槽位、`{PER_SECTION_CHARS}` ceiling；读 `writing-patterns.md` |
| `task2b_summary.md` | task3b_exec_summary | 串行综述，只合成不新增 |
| `task3_review.md` | task3c_realization_audit + task4_redteam | 三 lens 定义于一个文件，主 agent 按 lens 派 3 个 agent；输出统一根因列表格式；lens②③ 读 `contrast-examples.md` + `anti-patterns.md` |
| `task4_blueprint.md` | task3d_presentation_blueprint + task4_assembly | §3 Step 4 第 4 点全部要求；去 canonical/snapshot 语汇；读 `presentation-patterns.md` |

## 6. 工具重建（`tools/prop_tools.py` 全新，标准库 only，UTF-8 无 BOM）

- **`validate-blueprint --blueprint FILE --output-dir DIR [--assets-root DIR]`**：
  - 结构：`schema_version` 兼容 `presentation-blueprint/v1`（对 `generation_snapshot_id`/`brief_hash` 等旧绑定字段**忽略而非要求**）；连续页码；core 全部先于 appendix；story arc 覆盖每个 core 页恰一次；唯一 signature + sample 映射；`render_text.title == slide.title`；上屏文案无 raw URL/内部 ref；`asset_requests` 字段完整、`available` 素材路径真实存在；`rights_status=needs_review` → warning。
  - **证据图红线**：`asset_requests[].evidence == true` 且 `mode == "generate"` → fail（`evidence` 为新增布尔字段，由 planner 申报、lens③ 抽查申报诚实性）。
  - 页级 `unverified_notes` 格式检查。
  - 通过后确定性写 `outline.md`（页码/track/标题/takeaway/素材状态/待核实标注）+ `presentation-validation.json`（`status=ready_for_outline_review`，`image_generation_started=false`）。
- **`validate-index --index FILE --doc FILE --score-table FILE [--risk FILE]`**：索引每行引用的章节标题在正文真实存在；score-table 每项在索引恰有一行；覆盖状态 ∈ {完整, 部分, 虚构补全}；给 `--risk` 时，"虚构补全"行在风险文档中有对应条目。输出 fail 列表。
- 移植提示：旧 `validate-presentation` 逻辑在 `prop_v3.py` 内与 canonical 状态纠缠；**若剥离超过约半天工作量，直接按 `docs/reference/presentation-blueprint.md` 契约全新实现**（STOP-4），不把状态依赖带进 v4。
- `tests/` 全新：正反 fixture（合法 blueprint；证据图 `generate` 坏例；索引指向不存在章节坏例；漏评分项坏例；`unverified_notes` 与 `--risk` 交叉坏例），全部跑绿并在完成汇报附运行输出。

## 7. 工艺资产抢救清单（来源 → 去处，逐条可验）

1. RULES §7 写作工艺 → `references/writing-patterns.md` + task2 prompt：每章以客户任务/结果开篇；标题含主张；创意配动作/责任/资源/时点；不以我司自夸开篇；"赋能/生态/闭环/矩阵/全域/多维"非机械禁词——删掉术语后若无对象/机制/依据/可检查结果，删整句重写。
2. RULES §7 递交稿禁项（保留仍适用子集）→ `writing-patterns.md` "递交稿禁项"节 + lens③ 清单：URL/书目；叙事策略/模式/版本/生成时间/内部权重痕迹；工具与模型痕迹；内部 ID；销售 CTA/期待沟通签约；LaTeX；货币 `$` 未转义；章节编号混层；占位符残留。（v3 canonical/commitment 语汇剔除；虚构承诺类风险由登记制承接。）
3. `narratives.json` → 保留文件与"按标型自动选 + 短 guide 进 writer brief"机制；`TYPES.md` 中仍有价值的叙事定义并入 `narratives.json` guide 或 `strategy-patterns.md` 后，`TYPES.md` 本体退役。
4. 权重篇幅分配 → task1/task2：总规模由标书要求或材料规模判断（`profiles.json` 退役），一页纸逐章给 `{PER_SECTION_CHARS}`，ceiling 非填满目标。
5. `contrast-examples.md` + `anti-patterns.md` → 仅 lens②③ 读取（保持"反模式不进生成侧"原则）。
6. `presentation-patterns.md` → 保留并更新：效果图系列页型、core 1–2 决定性效果图、风格锚提取、证据图红线提示。
7. `strategy-patterns.md` → 保留（task1）。`strategy-rubric.md` 退役（五维打分仪式；互换测试已内嵌一页纸）。
8. casebase 机制 → SKILL.md 一句：非 `_` 开头自动纳入 + `[notes]` 只作内部校准。

## 8. blueprint v1 增量字段（全部可选、向下兼容）

| 字段 | 含义 |
|:---|:---|
| `slides[].visual.avoid` | 画面规避元素 |
| `slides[].unverified_notes[]` | 本页承载的虚构/待核实点，与 `_风险与待核实.md` 对应 |
| `asset_requests[].evidence` | 布尔；证据类素材申报，红线机器判定锚点 |
| `generation_snapshot_id` / `brief_hash` | 降级为可省略；校验器忽略 |

同步更新 `docs/reference/presentation-blueprint.md`：写明 v1 兼容声明（旧消费者忽略新字段即可）、新字段表、证据图红线、校验器脱离 state-dir 的新签名。

## 9. 仓库收尾

1. 宿主入口 `/home/raul/.agents/skills/proposal/SKILL.md` 重写：v4 description（§3 基线）、流程摘要、**保留 Codex 与 Claude Code 两张工具映射表**（行内容更新到 v4 概念：Gate 单题确认 → 一页纸唯一确认；去掉 canonical/ChangeSet 行）。
2. `README.md` 重写（~60–80 行）：定位、快速开始、产物树、`-no-ppt`/`-auto`、风险登记边界、image2 交接、恢复重引擎的方法（`git checkout v3.4.0-heavy`）。
3. `CONTRIBUTING.md` 按新仓库布局精简；`VERSION` → `4.0.0`。
4. `plans/README.md`：009 状态行随进度更新（本计划落地时由执行者改 DONE）。
5. **全库 grep 清扫**（存活文件零残留；`plans/`、`casebase/`、`reports/`、`.scratch/` 除外）：`RULES.md|DECISIONS.md|TYPES.md|LEGACY.md|profiles.json|prop_v3|canonical|ChangeSet|changeset|snapshot|readiness|receipt|Gate 1|Gate 2|gate2|-quick|-deep|-legacy|validate-run|finalize-run|apply-auto-state|compile-context|freeze|realization|customer-fit`。
6. 提交策略：commit 1 = tag 后的退役删除 + 目录骨架；commit 2 = 新 SKILL/prompts/references/tools/tests；commit 3 = docs/README/宿主入口/收尾。信息用中文 conventional 风格，与仓库既有历史一致。不 push。

## 10. 验收判据（全部满足才可标 DONE）

1. `git tag v3.4.0-heavy` 存在且指向重建前最后一个 commit。
2. 工作树中退役文件全部消失；§9.5 grep 清扫零命中。
3. 仓库 `SKILL.md` ≤120 行；只含 `-no-ppt`/`-auto` 两个 flag；七个 leading words 贯穿；五步各有可检查完成判据；description 以"商业方案"类触发词打头。
4. 宿主入口与仓库 SKILL.md 一致（路径、流程摘要、两张映射表齐全）。
5. 5 个 prompt 齐且各含"交付目标→依据→工作顺序→输出契约"；task2 含虚构申报契约；task3 含三 lens；task4 含证据图红线与页级标注。
6. `writing-patterns.md` 含开篇/标题/套话重写/递交稿禁项四组内容；`contrast-examples.md`/`anti-patterns.md` 仅被 task3_review 引用；`narratives.json` 被 task1/task2 引用。
7. 工具两个子命令在 fixtures 上跑通；四类坏例全部正确 fail；tests 全绿（完成汇报附实际运行输出）。
8. `presentation-blueprint.md` 更新为 v1+增量字段并含兼容声明；README/CONTRIBUTING/VERSION 相互一致。
9. **诚实汇报**：本计划不含端到端宿主运行；完成汇报必须明说"未跑真实 /proposal，首个真实标书运行是验收续项"，不得虚构或模拟运行结果。

## 11. STOP conditions

- **STOP-1**：动任何文件前：确认工作树 clean（不 clean 则停下问用户）→ `git tag v3.4.0-heavy` → 验证 tag 存在。失败即停。
- **STOP-2**：`casebase/` 数据、`plans/001-008`、`reports/`、`.scratch/` 不改不删（`plans/README.md` 状态行除外）。
- **STOP-3**：`deck-blueprint.json` v1 已有字段语义不改，只加可选字段；拿不准某改动是否破坏下游兼容时，停下来问。
- **STOP-4**：从 `prop_v3.py` 剥离校验器若与 canonical 状态纠缠超约半天工作量→放弃移植，按契约文档全新实现。
- **STOP-5**：不加本计划范围外的"顺手改进"（新 flag、新状态文件、新 gate、新 canonical）；确有必要→停下来问用户。
- **STOP-6**：`command/`、`install/`、`agents/` 中发现未预期的耦合或本计划未覆盖的引用→完成范围内工作，在汇报中列出并给建议，不擅自扩大范围。

---
`plan 009 · 由 2026-07-20 会话定稿 · 实施目标版本 4.0.0`
