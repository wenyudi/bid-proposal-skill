# Implementation Plans

由 improve skill 于 2026-07-16 生成,基准 commit `b10506e`(v3.0.0)。审计范围:全仓库(SKILL/RULES/TYPES/DECISIONS、8 个 v3 prompt、tools/ 两个 CLI 逐行、tests、docs 全部、casebase、仓库卫生;`prompts/legacy/` 仅抽查)。2026-07-19 根据首个 deep 真实 shadow run 的“合规但空”结果补充 Plan 008,并把 Plan 006 升级为双标型、必须保存真实 pre-change 基线的质量轨道。v3.3 又完成四项轻量增量：report-bound 红队 judgment、研究后重开候选、确定性 Task 1 scaffold、唯一 signature 成果；五份 canonical 与两级 readiness 均未增加。执行者:开始前完整读完对应计划,遵守其 STOP conditions,完成后更新本表状态行。

本次运行为非交互(用户未在线选择),按杠杆默认选出以下计划;取舍记录见文末。

## Execution order & status

| Plan | Title | Priority | Effort | Depends on | Status |
|------|-------|----------|--------|------------|--------|
| 007 | 仓库卫生:运行输出与 git 隔离、外呼端点可配置 | P1 | S | — | DONE |
| 001 | 消除 qa-proposal 硬门误报 + 正反语料回归测试 | P1 | M | — | DONE |
| 002 | 最终门盲区:待办漏扫卷首占位符、sections[].n 零校验 | P1 | S | 001* | DONE |
| 004 | agent I/O 契约:审计字段说明、占位变量定义、健壮读取、CJK token 估算 | P1 | M | — | DONE |
| 003 | last-good 恢复点在所有失败路径下不可丢失 | P1 | M | — | DONE |
| 006 | 双标型评估基线:数字运营 + 内容视频 fixture、质量清单、真实 pre-change run | P1 | L | 007,001,002,004** | BLOCKED — fixtures ready; pre-change run invalid because its source was not frozen before v3.1 edits |
| 005 | 叙事工艺送达写作 agent(TYPES.md → Task 3/3.5 断链) | P2 | M | 004* | DONE — `narratives.json` 单一事实源，brief 只注入当前短 guide |
| 008 | 项目化成果与竞争稿就绪门:proof contract → brief → 独立审计 → submission | P1 | L | 004,006***;005* | REJECTED — 原方案过重；由 v3.1 轻量 `visible_outputs` 实现核心效果，不新增 readiness/canonical |
| 009 | v4 轻量重建:商业方案 + 默认图片 PPT 交接 | P0 | L | — | TODO — 动手第一步先打 tag `v3.4.0-heavy`;规格与 STOP conditions 见 009 文件 |

Status values: TODO | IN PROGRESS | DONE | BLOCKED (with one-line reason) | REJECTED (with one-line rationale)

> 2026-07-20 更新:009 起转入 v4 轻量重建轨道(用户拍板:商业方案 + 默认图片 PPT 交接,重引擎退役进 git 历史)。001–008 属 v3 历史存档,不再继续执行;006 的"改前/改后哪个更优"关切由 009 验收判据与 v4 首次真实运行续接。

## Dependency notes

- `*` 软依赖(历史):002 与 001 改同一文件不同函数。v3.1 已把 005 收口为 `narratives.json`，并以轻量 visible output 替代 008 的大 proof 模型。
- `**` 006 的 fixture/清单/文档可提前创建,但计划只有在 007/001/002/004 后真实跑完两条 pre-change baseline 才能标 DONE;无宿主运行只能 BLOCKED。基线必须发生在 005/008 质量改动之前。
- `***` 原 008 的硬依赖不再适用；其真实性、独立审计和基线红线由 v3.1 轻量实现继续保留。
- 003 与 001/002 同文件不同函数,建议顺序合并。

推荐阶段顺序:

```text
卫生与正确性: 007 → 001 → 002 / 004 → 003
冻结质量红线: 006 assets → 两条 pre-change host baseline
提高表达上限: 005（已完成）
防止“合规但空”: v3.1 visible outputs → forward test + 可选真实 shadow
```

v3.1 仍分别处理“写得平”和“写得空”，但不再为后者引入第六 canonical、独立 proof registry 或第三种 readiness。

## v3.1 已收口的原 backlog

- **CONTRACT-02**：`apply-auto-state` 会把 Gate 绑定的 publishable/committed/confirmed 状态分别降为 draft_ready/intended/planned/unknown；unknown 不再靠虚构区间解锁。
- **SEC-01 / SEC-02**：writer/redteam brief 不再携带 Role 内部判断、Need/Criterion 未批准名称或 private Gate title，只携带安全投影、稳定 ID 和 safe constraint。
- **CONTRACT-03**：Gate 2 可提交 canonical 修订，但不能替 Gate 1/human/main 写入或改动已确认答案；`migration` 不再是 ChangeSet producer。
- **BUG-05**：非 ASCII 或超长 ID 的派生文件名统一附内容 hash，避免 brief、receipt 与 realization 覆盖。
- **DEBT-01 可安全部分**：snapshot 指纹与 stage blocker 只保留一套实现；第三方 Evidence kind 集中定义；Task 2 manifest 会进入 `intel-pool.research_manifest`。

刻意不拆 `_validate_lifecycle`：它虽长，但目前是一条内聚的跨实体硬门，机械拆分只会增加调用面而不减少认知负担。相同红线在独立 prompt 中保留必要短句，因为子 agent 不共享主 agent 的完整上下文；权威定义仍只在 `RULES.md`。

## Findings considered and rejected

- **「v3 子命令退出码恒为 0」**(引擎审计上报):复核否决。`dispatch_cli` 末行 `return 0 if result.get("passed") else 1`(`prop_v3.py:4378`),`compile_context` 等返回值均含 `passed` 包装;调用侧 `prop_tools.py:1670-1672` 正确 `sys.exit`。
- **全局 snapshot 粗粒度失效**:SKILL.md/DECISIONS.md 明文记录的暂时取舍(「后续实际使用稳定后再细化依赖级局部失效」),by-design。
- **v3 直接作为默认引擎发布**:`.scratch` 票据 11 记录的用户决策,by-design。
- **仅标准库、无第三方依赖**:CONTRIBUTING 明文约束,by-design。
- **`word-count` 中文口径**:与 Word 习惯一致,仅表格分隔残留有个位数百分比虚增,已并入 001 顺手修,不单列。
- **`github_anchor` 死代码**(`prop_tools.py:206`):无调用,但删除收益太低,不值得单独动。
- **`check_strategy` titles.count O(n²)**:n 为个位数,不构成问题。
- **task2.5 brief 含 private 原文**:RULES §8 的投影限制只约束 section/summary/redteam,value-selection 拿全图是设计内(它需要 private 约束做选择)。

## 质量发现的补充说明

- 原始静态审计准确识别了“写作工艺断链”和“没有评估闭环”,但当时没有真实 run,因此没有发现“realization 通过但客户可见成果仍为空”的第四层契约缺口。
- 2026-07-18 shadow run 的复现信号是:required document proof 3/3 缺失;红队修订增加约 3,700 字后仍为 3/3。该信号只作为 Plan 008 的设计依据,真实卷册不进入仓库。
- 006 负责回答“改前和改后哪个更优”；v3.1 deterministic visible-output gate 负责“不能再通过但空”。没有真实 pre/post 盲评时，仍不得宣称整体已最优。

## 审计中未覆盖的部分

- `prompts/legacy/` 五个旧 prompt 与 legacy 链行为:仅抽查,未逐行(冻结维护,风险低)。
- `docs/` 十六页中 tutorial/how-to/explanation 的每一句断言:重点核对了 reference 四页与 workflow;教程级漂移风险低但未逐句验证。
- 原始审计未运行端到端 `/proposal`;后续仅用一条真实 shadow run 定位项目化成果缺口,尚不能替代 006 规定的双 fixture、冻结参数和盲评基线。
