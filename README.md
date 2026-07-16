# proposal — 政企传媒技术标生成 skill

proposal 3.0 默认运行 v3：先把标书要求、客户角色与需求、价值主张、证据、执行责任和验收边界做成可校验状态，再生成客户可读方案。目标是同时做到：

> 合规零遗漏 · 真懂客户 · 亮点值得选 · 证据可信 · 交付可兑现 · 风险妥帖

范围仅限技术标。投标函、法定代表人授权书、承诺函和法定报价表等，仍按标书模板套用。

它是独立 skill：运行时不调用 wayfinder、grill-me 或外部 issue tracker。复杂任务找路与压力追问的方法参考了 [mattpocock/skills](https://github.com/mattpocock/skills)（MIT），已经内生为本项目的 canonical、ChangeSet、单题 Gate 和诊断规则。

## 安装

必须注册 skill 入口，否则模型只会在对话里直接写稿，不会执行研究后选择、分章并行和硬门审计。

- Claude Code：见 [`install/claude-code-skill.md`](install/claude-code-skill.md)
- OpenCode：将仓库注册为 skill；`command/proposal.md` 提供 `/proposal`
- 其他 CLI：按安装文档映射 agent/search/fetch/read/write 工具

## 用法

```text
/proposal <标书路径或粘贴文本> [素材路径] [-quick|-deep] [-logic|-story|-vision|-evidence] [-auto] [-legacy]
```

- 无深度标志：standard；`-quick` 适合时间紧，`-deep` 适合重点标。
- 无叙事标志：按标书自动选 logic/story/vision/evidence；叙事只改变讲法，不能裁掉评分项或加强承诺。
- 默认停 Gate 1 和 Gate 2；quick 只停 Gate 1。每轮只解决一个需要投标人拍板的决策，并给推荐答案。
- `-auto` 可生成完整保守草案，但 assumed 能力、报价或承诺会让 `submission_ready=false`，不会伪装成可直接递交。
- 无标志和 `-v3` 都是 v3；只有显式 `-legacy` 才使用 2.x 回退流程。两套引擎不能在同一 run 混线。
- `casebase/` 非空时自动纳入。沟通/踏勘/售前纪要标 `[notes]`，只作 private 校准，正文绝不引用。

示例：

```text
/proposal /Users/me/文旅传播招标文件.pdf ~/投标素材/ -deep -story
/proposal /Users/me/新媒体代运营标书.pdf -evidence
/proposal /Users/me/小标.pdf -quick -auto
/proposal /Users/me/旧项目目录 -legacy
```

## v3 为什么更适合客户

| 客户会问 | v3 怎么回答 |
|:---|:---|
| 你真的理解谁在判断、使用和担责吗？ | 按标实例化业务、专家、采购合规、纪检、领导和使用者角色；权力、否决、履约影响与审查风险分开，不虚构个人偏好 |
| 这个亮点跟我有什么关系？ | ValueProposition 必须连到具体 Role × Need × Criterion，并说明客户变化与价值机制；满足标书本身不冒充亮点 |
| 这是点子还是能做的方案？ | proposal/commitment 连接 Action、唯一 accountable、资源时点、客户依赖安全兜底和 AcceptanceContract |
| 数字、案例和承诺凭什么信？ | Evidence 原记录与“它证明什么”分开；正文用途、scope、强度和 authority 都可校验；匿名材料不回退原文，第三方案例不能证明我方能力 |
| 评委读完会形成什么新判断？ | 评分骨架上叠加 DecisionJob：理解 → 相信 → 价值 → 落地 → 风险 → 可辩护选择，不强制六阶段一章一段 |
| 严格结构会不会让稿子难读？ | 完整图谱只在底层；每章只收到最小 compiled brief，客户稿不显示 ID、状态机、审计标签或适配度 |
| 综述会不会比正文吹得更大？ | 每章先审 Requirement 是否实质回答，再审 Claim/Action realization；方案综述只读取全部正式章的 valid 白名单 |
| “适配度 83 分”可信吗？ | 不输出伪精确点分和中标率；十个锚定维度给敏感性区间、短板、置信度和修复 owner，硬门失败则 overall withheld |

候选阶段保持发散：从 outcome、efficiency、risk、visibility、experience、asset、contrarian 多镜头生成候选。Task 2 查证后，Task 2.5 才用窄硬门、关键短板、Pareto 和组合充分性选择 lead/supporting/reserve。v3 不奖励亮点数量、篇幅、表格或形容词。

## 两道人工关卡

Gate 1 只问 AI 无法知道的真实边界：投标人能力、资源容量、报价取舍、案例/名称/数字授权、关键 KPI、免费增值、未公开履约关系和个人偏好。标书和素材能查到的事实由系统查，公开缺口交 Task 2。答案通过跨文件 ChangeSet 同时更新 decision 与受影响的 VP/Claim/Action/Resource/Acceptance，避免“状态已确认、方案还没改”。

Gate 2 在机械门与四视角红队后处理根因诊断。红队只提问题；每条带正文引文、影响、置信度、canonical owner 和修复范围。相同根因合并，不为凑数量制造质疑。用户可明确授权“其余按推荐处理”。

## 流程

```text
标书/素材
  → Task 1：五域 bootstrap + 开放候选池
  → Gate 1：真实能力/资源/报价/授权单题确认
  → Task 2：公开 Evidence、反证、案例 proof task
  → Task 2.5：lead/supporting/reserve + Claim/Action/DecisionJob 收敛
  → generation gate + customer-fit strategy checkpoint + snapshot
  → Task 3：按章最小 brief 并行写作
  → 独立 realization 审计（Requirement addressed + Claim/Action/scope/承诺）
  → Task 3.5：realized-only 方案综述
  → 装配 + compliance + QA + submission fit
  → buyer/expert/audit/rival 红队 + Gate 2
  → 最终复验 + _state 原子归档 + last-good
```

五份 canonical：

```text
requirements.json      标书 Requirement / 评分 / mandatory / 预算
customer-value.json    Role / Need / Criterion / VP / Claim / Metric / EvidenceLink
delivery-plan.json     DeliveryRole / Action / Resource / Dependency / Acceptance
strategy.json          narrative / DecisionJob / Section / Gate 决策地图
intel-pool.json        Evidence 原记录
```

Task 和 Gate 不直接散改它们，而是提交带 base revision 的 ChangeSet。工具在临时副本检查 schema、引用、生命周期、权限和跨文件硬门，全部通过才原子替换；stale 或任一失败整组回滚。

## 输出

```text
<方案标题>-<时间戳>/
├── 技术方案-完整版.md          递交稿
├── 分册/                       目录、对照表、综述、各章
├── _内部研判.md                不递交：决策、来源、fit、红队
├── _人工待办.md                不递交：assumed、缺口、占位符
└── _state/                     不递交：canonical、sections、快照、diagnostics、realization
```

下划线开头的内容一律不递交。装配先在 staging 完成，成功后才切换；上一份成功卷册保存在报告目录 `.last-good/`，状态重复归档时保留 `_state.last-good`。失败构建不会删掉上一份成功结果。`archive-state` 的 `canonical_submission_ready` 只证明归档当时的 canonical/realization；复制 `_state` 到新目录恢复后，须重编译 brief 并复审全部章节/摘要，旧绝对路径 artifact 不作为续用 attestation。最终是否可递交还必须以同一份 report 的 compliance、QA、customer-fit 和 Gate 2 为准。

## 关键命令

`tools/prop_tools.py` 保留所有 2.x 命令，并新增：

```text
bootstrap-state / migrate-state
check-canonical / apply-changeset / apply-auto-state
compile-context / promote-research / freeze-snapshot
audit-realization / customer-fit / archive-state
```

示例：

```bash
python3 tools/prop_tools.py check-canonical --state-dir /tmp/run --stage generation --write-derived
python3 tools/prop_tools.py compile-context --state-dir /tmp/run --target section --id CH-03
python3 tools/prop_tools.py customer-fit --state-dir /tmp/run --checkpoint submission
python3 tools/prop_tools.py qa-proposal /path/to/report.md --strategy /tmp/run/strategy.json --requirements /tmp/run/requirements.json --state-dir /tmp/run
```

所有运行时代码只依赖 Python 3.8+ 标准库。联网研究依赖宿主提供的 search/fetch；PDF/DOCX 提取可由宿主工具或可选库完成。

## 仓库结构

```text
SKILL.md                 v3 默认调度
LEGACY.md                显式 -legacy 回退
RULES.md                 硬门、权限和正文边界
DECISIONS.md             Gate 单题状态机与 ChangeSet 原则
TYPES.md                 六标型、评委、叙事与决策旅程变体
prompts/                 v3 Task 1/2/2.5/3/realization/summary/redteam
prompts/legacy/          2.x 回退 prompts
tools/prop_tools.py      兼容 CLI、装配、合规、QA
tools/prop_v3.py         canonical、事务、context、realization、fit、归档
tests/                   legacy 兼容与 v3 hard-gate 测试
casebase/                人工维护的真实案例事实源
```

## 刻意不做

- 不写销售 CTA、“期待进一步沟通”、分阶段 opt-in 报价。
- 不写“排除项/不包含”式免责，避免实质性负偏离；客户配合只能写有安全兜底的依赖。
- 不引用私下沟通或个人内部表述；只用标书、澄清、公开政策/报道和已批准材料投影。
- 不把 URL 书目、生成元数据、叙事策略、内部 ID、customer-fit 或工具痕迹印给评委。
- 不虚构资质、案例、团队、资源、数字或保证性结果。
- 不把第三方案例包装成我方业绩，不把“材料清单上有”当成 verified。
- 不用客户适配度软分替代 mandatory、真实性、预算、法律、授权和交付硬门。

## 合规声明

生成物是投标响应草案。真实资质、业绩、人员、报价和可承诺 KPI 必须由投标人核验；任何 `submission_ready=false`、占位符或 `_人工待办.md` 硬项未清，都不可直接递交。customer-fit 是内部敏感性诊断，不是评委分数或中标概率。

---
```
proposal skill · 3.0.0 · v3 direct-default
```
