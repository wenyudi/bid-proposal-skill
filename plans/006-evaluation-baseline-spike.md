# Plan 006: 双标型评估基线 — 用真实端到端对比回答“是否更优”

> **Execution status: BLOCKED.** Fixtures、清单和文档已完成，但唯一一次 pre-change run 没有先冻结源码，已判无效；v3.1 之后只能做 post-change forward test，不能补造前后对比。

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**:
>
> ```bash
> git diff --stat b10506e -- tests/fixtures/ docs/reference/ docs/how-to/ README.md
> git status --short -- tests/fixtures/ docs/reference/ docs/how-to/ README.md
> ```
>
> 若 in-scope 评估资产已经由他人创建，先逐项比对，不重复建立第二套体系；字段或路径冲突属于 STOP。

## Status

- **Priority**: P1（Plan 008 的前置红线；没有前置基线就不能声称质量修复有效）
- **Effort**: L（两套 fixture、质量清单、宿主运行流程、至少一次真实 pre-change baseline）
- **Risk**: LOW（只新增虚构评估资产和文档，不改生成引擎）
- **Depends on**: 资产编写无硬依赖；实际 baseline run 建议在 007、001、002、004 落地后且必须在 005、008 之前
- **Category**: evaluation / quality baseline
- **Planned at**: commit `b10506e`, revised 2026-07-19

## Why this matters

仓库从 v1.2 到 v3.0 持续增加真实性、canonical、ChangeSet、realization 和红队规则，但没有冻结 fixture、黄金对照或 blind comparison，无法回答“细节更多后方案是否更优”。2026-07-18 的首个真实 shadow run 又证明，只看机械覆盖和 Claim/Action realization 会漏掉另一类失败：正文约 4.4 万字、硬门大体完整，却没有已填订单简报、内容母版和可拍分镜；红队修订增加约 3,700 字，3/3 项目化成果缺口不变。

原计划只使用一份轻量数字运营 fixture，且明确不要求跑通全流程。这不足以检出上述问题：

- 轻量运营标可以靠流程、栏目和排期写得像样，不一定迫使系统交付创意实物；
- 只建 fixture/清单、不实际运行，仍然没有 baseline；
- 只评价叙事、顺滑度和认知增量，可能把“更漂亮的空话”误判为提升。

本修订交付两条互补赛道：

1. **数字运营 fixture**：检验持续产能、栏目、数据闭环、私密隔离和执行细节；
2. **内容/视频 fixture**：强制检验已填内容母版、样例文案和带 timecode/画面/旁白或字幕的分镜。

完成标准从“资产写好了”提高为“至少保存一次可复核的 pre-change 端到端结果”；如果执行环境不能运行宿主流程，计划只能标 `BLOCKED`，不能标 `DONE`。

## Current state

- `casebase/` 只有 README 与 `_template.md`，无可复跑案例。
- `tests/` 是单元测试，没有端到端 tender/material fixture。
- 仓库无 `tests/fixtures/`、质量清单或 baseline how-to。
- RULES.md 定义十个 customer-fit 维度，但 `differentiation` 和 `reading_efficiency` 在缺 semantic judgment 时仍可能 `not_evaluated`。
- `reports/` 中的真实输出含客户与内部研判，绝不能成为 git fixture；真实 shadow 只在仓库外保存。
- 完整 v3 运行需要 LLM 宿主、Gate/agent 调度和可能的联网研究；纯 CLI 单元测试不能替代端到端基线。

## Commands you will need

| Purpose | Command | Expected on success |
|:---|:---|:---|
| fixture 编码 | `python3 tools/prop_tools.py check-encoding tests/fixtures/tender-digital-demo.md` | passed |
| 内容 fixture 编码 | `python3 tools/prop_tools.py check-encoding tests/fixtures/tender-content-demo.md` | passed |
| 虚构标记 | `rg -n "完全虚构|仅供评估" tests/fixtures` | 每个文件均命中 |
| 私密测试字段 | `rg -n "\[notes\]" tests/fixtures/materials-*.md` | 两份材料均命中 |
| 质量指标 | `rg -n "proof_object_coverage|lead_proof_coverage|deferred_proof_burden" docs/reference/quality-checklist.md` | 3 项均命中 |
| 全部测试 | `python3 -m unittest discover -s tests` | 全部通过 |

## Scope

**In scope**:

- `tests/fixtures/tender-digital-demo.md`（新建）
- `tests/fixtures/materials-digital-demo.md`（新建）
- `tests/fixtures/tender-content-demo.md`（新建）
- `tests/fixtures/materials-content-demo.md`（新建）
- `docs/reference/quality-checklist.md`（新建）
- `docs/how-to/run-evaluation-baseline.md`（新建）
- `README.md` 或现有 docs 索引增加链接
- 仓库外 baseline 目录中的两次 pre-change run 及清单（不提交 git）

**Out of scope**:

- 修改 `tools/*.py`、prompt、RULES 或自动评分逻辑；这些属于 005/008。
- 把真实标书、真实报告、客户名、内部研判、底价或未授权案例提交到仓库。
- 为获得“可比较”而关闭联网或伪造真实机构资料；网络漂移只记录为 uncertainty。
- 把人工 1–5 分冒充评委分、中标概率或跨标排名。
- 在 Plan 008 前假装已有结构化 proof manifest；pre-change 阶段按同一清单人工判定，post-change 再读取结构化结果。

## Git workflow

- Branch: `advisor/006-evaluation-baseline`
- 不 push、不开 PR，除非操作者指示。

## Fixture A: 数字运营

完全虚构的政务新媒体代运营标，重点验证：

- 8–10 个评分项、总分 100，覆盖技术方案、内容创意、团队案例、服务保障和报价；
- 4–6 条 mandatory 与 3–5 项交付物；
- 一条只能由用户决定的能力/资源边界，用于 Gate 1；
- 一条 `[notes]` private 偏好，用于泄漏测试；
- 一个高权重内容策略评分项，明确要求：四周栏目日历、至少一篇已写样例内容、数据看板字段与一次优化演示；
- 一个含糊要求，例如“重大活动期间加密更新”但未定义频次，用于检查是否正确提问而非自行承诺。

该 fixture 防止系统只交“栏目规划方法”和“数据闭环流程”，却没有填入栏目、样文和看板。

## Fixture B: 内容/视频制作

完全虚构的政企内容制作框架标，重点复现 2026-07-18 shadow run 的抽象化风险，但不得复制真实客户文本：

- 虚构采购人、产品/服务与品牌事实，全部在 tender/material 中给出安全口径；
- 高权重“总体实施与创意样片”评分项；
- 技术方案必须呈现三个 document proof：
  1. 一个已填订单简报；
  2. 一个含受众、主题、主标题、核心文案、视觉锚点、三种载体适配的内容母版；
  3. 一个 45–60 秒分镜，至少含 timecode、画面动作、旁白或字幕、事实边界和转场；
- 外部 MP4 标为独立 submission attachment，不得替代正文分镜；
- materials 提供足够产品事实和虚构 bidder 资源，但故意不提供历史结果 KPI，检查系统能否写具体而不编造效果。

该 fixture 是 Plan 008 的主要 red/green 质量信号。

## Steps

### Step 1: 新建数字运营 tender fixture

创建 `tests/fixtures/tender-digital-demo.md`：

- 使用明显虚构名，例如“云澜市公共文化服务中心（虚构）”；禁止使用需要联网确认是否真实存在的普通机构名。
- 写项目编号、预算上限、服务期、mandatory、评分表、交付物与验收。
- 内容策略评分明确要求四周栏目日历、完整样文和看板字段，不只要求“提供方案”。
- 头部声明：

  ```text
  本文件为完全虚构的评估 fixture；机构、人名、项目、产品和数字均无真实对应，仅供 proposal 回归评估，不得作为真实标书递交。
  ```

**Verify**:

- `python3 tools/prop_tools.py check-encoding tests/fixtures/tender-digital-demo.md` → passed。
- `rg -c "评分" tests/fixtures/tender-digital-demo.md` ≥ 8。
- `rg -n "四周|样例|看板" tests/fixtures/tender-digital-demo.md` 三类均命中。

### Step 2: 新建数字运营 materials fixture

创建 `tests/fixtures/materials-digital-demo.md`：

- 虚构投标人、资质摘要、团队、可公开的虚构案例 Evidence 和资源边界；所有内容明确为 fixture，不进入真实 casebase。
- 提供足够栏目与平台事实，让 agent 可以填样例，不需要编造真实政府数据。
- 加一条 `[notes]`，例如“对接人口头提到更喜欢短视频”；期望只形成安全约束，不得在正文引用。
- 故意留一个需要 Gate 的夜间值班容量边界。

**Verify**: `rg -n "\[notes\]|完全虚构" tests/fixtures/materials-digital-demo.md` 均命中。

### Step 3: 新建内容/视频 tender 与 materials fixture

创建：

- `tests/fixtures/tender-content-demo.md`
- `tests/fixtures/materials-content-demo.md`

tender 必须逐字定义三个 document proof 的交付要求，并把外部 MP4 单列为附件；materials 必须给出可安全使用的虚构产品事实、VI边界、目标受众和制作资源，同时明确没有历史效果基线。

为防止 fixture 自己成为“答案模板”，只定义事实和验收字段，不直接写最终主题、标题、文案或分镜；这些应由 proposal 流程生成。

两份文件均在头部和关键案例处标“完全虚构、仅供评估”。

**Verify**:

- `python3 tools/prop_tools.py check-encoding tests/fixtures/tender-content-demo.md` → passed。
- `rg -n "订单简报|内容母版|timecode|MP4" tests/fixtures/tender-content-demo.md` 四类均命中。
- `rg -n "\[notes\]|无历史效果基线" tests/fixtures/materials-content-demo.md` 均命中。

### Step 4: 写质量评估清单

创建 `docs/reference/quality-checklist.md`，分四层。

#### A. 不可回退硬门

- compliance、QA、canonical submission、真实性/private/URL/预算/authority；
- assumed/open Gate、fatal/blocker、人工待办；
- 任一硬门回退时，新版本不得判“更优”，无论文风分多高。

#### B. 项目化成果机械/结构指标

清单中必须使用以下稳定键，便于 pre/post 对齐：

- `proof_object_coverage`：required document proof 中已填对象比例；
- `lead_proof_coverage`：lead VP 是否至少有一个客户可见 proof；
- `proof_field_completeness`：每个 proof 要求字段的完成比例；
- `external_substitution_violations`：用未来附件替代当前正文 proof 的次数；
- `deferred_proof_burden`：核心选择理由中仍依赖“后续形成/递交前补”的数量；
- `project_specificity`：成果对象是否填入当前 fixture 的场景、受众、内容和输出，而非只贴字段名；
- `unexpected_claims`：具体化过程中新增的未授权事实/数字/能力。

Pre-change 没有结构化 manifest 时，由两名评审按字段逐项人工填 `filled|partial|missing`；Plan 008 后改读 authoritative proof realization，但保留人工复核。

#### C. 十维 customer-fit 与人工质量项

复用 RULES 的十维，不另造总分；再对以下项目给 1–5 锚点：

- 客户/项目特定性；
- 认知增量；
- 成果对象的可使用完整度；
- 证据—主张—成果的连通性；
- 选择理由是否容易被对手复制；
- 叙事温度与选定 mode 一致性；
- 阅读压缩度：有效信息是否被边界声明和同义重复淹没；
- “像客户可执行方案”还是“像内部审计说明”。

1 分与 5 分必须各有可观察锚点，不用“较好/优秀”循环定义。

#### D. 对比协议

- 同一 fixture、同一模式、同一用户回答或 `-auto`、同一可用模型/工具配置；
- A/B 文件名随机化，评审不知道哪份是新版本；
- 先判硬门，再判 proof，再判十维和写作；
- 只有硬门不回退且 proof/关键人工项改善，才能称“更优”；
- 结果只用于同一 fixture 的相对修订，不是评委分或中标概率。

**Verify**: 三个稳定 proof 指标检索命令通过，十个 customer-fit 维度全部出现。

### Step 5: 写端到端基线 how-to

创建 `docs/how-to/run-evaluation-baseline.md`，按现有 Diátaxis how-to 风格写清：

1. 在宿主会话分别运行：

   ```text
   /proposal tests/fixtures/tender-digital-demo.md tests/fixtures/materials-digital-demo.md -standard -auto -logic
   /proposal tests/fixtures/tender-content-demo.md tests/fixtures/materials-content-demo.md -deep -auto -story
   ```

2. `-auto` 结果预期 `submission_ready=false`，这不是失败；评估的是安全草案是否形成可判断内容。
3. 把完整卷册和清单复制到仓库外：

   ```text
   ~/proposal-baselines/<commit>/<fixture>/<timestamp>/
   ```

4. 记录 commit、模式、模型/宿主（若可见）、开始结束时间、source manifest、网络状态、Gate 假设、测试结果与报告 hash。
5. pre-change 必须在 Plan 005/008 前运行；post-change 使用相同输入和参数。
6. 网络研究变化单列 uncertainty；不要为追求逐字一致删除 Evidence 流程。
7. 真实 shadow run 可作为第三条外部校准，但不得复制进仓库。

**Verify**: 文档同时命中两个 fixture 名、`pre-change`、`post-change`、`proof_object_coverage`。

### Step 6: 挂文档索引

在 README.md 文档导航中增加：

- “评估修订是否更优” → baseline how-to；
- “方案质量评估清单” → quality checklist。

保持既有表格格式，不重复已有链接。

### Step 7: 实际保存 pre-change baseline

在 007、001、002、004 完成后、005/008 开始前，真实运行两条 fixture。每条：

1. 保存完整仓库外卷册；
2. 填完质量清单；
3. 对项目化成果记录 `filled|partial|missing` 与正文 quote；
4. 记录运行失败/重试次数和根因；
5. 计算报告 hash 并写入同目录 manifest。

如果当前执行器不能调用 LLM 宿主或无法完成全流程：

- 资产与文档可以提交；
- 本计划状态必须写 `BLOCKED — fixtures ready, pre-change host run not captured`；
- Plan 008 STOP，不得先改质量轨道再补“基线”。

## Test plan

- 四个 fixture 均通过 UTF-8 检查，且每个含明显虚构声明。
- `rg` 检查不含 URL、真实联系方式、真实客户路径和 `/home/...` 上传路径。
- 数字 fixture 能检查栏目日历、样文、看板；内容 fixture 能检查三类 document proof 与 external attachment 分离。
- 质量清单包含全部硬门、十维、七项 proof 指标和 blind protocol。
- 文档命令与实际路径逐字一致。
- `python3 -m unittest discover -s tests` 通过。
- 两次宿主 run 的报告、清单、manifest、hash 在仓库外可读。

## Done criteria

- [ ] 4 个 fixture 文件存在且全部声明“完全虚构、仅供评估”
- [ ] 数字 fixture 要求已填栏目日历、样文与看板字段
- [ ] 内容 fixture 要求订单简报、内容母版、具体分镜，并将 MP4 单列 external
- [ ] quality checklist 含硬门、十维、proof 指标和 blind comparison
- [ ] baseline how-to 含两条可复制命令与 pre/post 保存规则
- [ ] README 索引链接存在且目标文件可读
- [ ] 全部单元测试通过
- [ ] 两条 pre-change 宿主基线已实际运行并保存到仓库外
- [ ] 每条基线都有 report hash、运行元数据和填完的质量清单
- [ ] `git status` 只有 in-scope 评估资产、索引和计划状态变化
- [ ] `plans/README.md` 状态行已更新；缺宿主 run 时必须 BLOCKED，不能 DONE

## STOP conditions

- 任何 fixture 名称、机构、人名或案例无法确认是明显虚构。
- fixture 需要真实 URL、真实客户资料、未授权案例或本机上传文件才能成立。
- 为让 baseline 通过而改生成器、prompt 或规则；本计划只测，不修。
- 当前已有另一套质量清单/fixture 体系且无法无损合并。
- 无法把 baseline 产物保存到仓库外，或发现它们会进入 git。
- 计划执行时 005/008 已经落地但没有 pre-change 结果；报告后停，不伪造基线。
- 两条宿主 run 未完成却准备把计划标 DONE。

## Maintenance notes

- 首轮 baseline 不是黄金答案，只是可重跑的起点；至少经历两轮修订和盲评后再考虑冻结 golden excerpts。
- 后续应扩展到六标型，但先保证这两条轨道真正被使用，而不是一次性文档工程。
- 真实中标/失标复盘只能以授权、脱敏和仓库外方式校准；不得把 win/loss 标签直接变成固定 fit 权重。
- 若 Plan 008 改变 proof schema，quality checklist 的稳定键保持不变，只替换数据来源。
- 网络与模型漂移使逐字 diff 不可靠；比较结构、事实安全、proof completeness 与盲评判断，不比较漂亮词频。
