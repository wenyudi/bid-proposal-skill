# proposal

面向广告与传媒公司的政企技术标生成 skill。proposal 3.0 默认使用 v3：先校验标书要求、客户价值、证据、责任、资源与验收边界，再生成客户容易阅读、投标人能够兑现的方案。

> 合规零遗漏 · 真懂客户 · 亮点值得选 · 证据可信 · 交付可兑现 · 风险妥帖

本项目只覆盖技术标。投标函、授权书、承诺函、法定报价表等仍须按标书原模板填写。

## 它解决什么

- 把 mandatory、评分项、预算和交付物拆成不可被创意文案覆盖的硬门。
- 从实际判断、使用、监督和担责角色出发，连接客户需求、决策标准与价值主张。
- 候选阶段保持发散，公开研究后才选择 lead / supporting 亮点；不按亮点数量或篇幅凑竞争力。
- 把承诺连接到动作、责任、资源、时点和验收，避免“创意很好，但无法落地”。
- 用独立兑现审计检查正文是否真正回答要求、有没有夸大 Claim 或 Action。
- 把 private 纪要、内部模型、URL、诊断和适配度留在内部，不破坏客户阅读体验。

复杂任务找路和压力追问的思路参考了 [mattpocock/skills](https://github.com/mattpocock/skills) 中的 wayfinder 与 grill-me，并已内生为 canonical、ChangeSet、单题 Gate 和根因诊断；运行时不需要 skill 之间互相调用。

## 快速开始

要求 Python 3.8+。运行宿主还需要具备文件读写、子 agent 和联网检索/抓取能力；Python 工具本身只使用标准库。

1. 按[安装与注册指南](docs/how-to/install-and-register.md) clone 仓库并注册 skill。
2. 新开会话，输入：

   ```text
   /proposal /绝对路径/招标文件.pdf /绝对路径/投标素材/ -deep -story
   ```

3. 在 Gate 1 逐题确认只有投标人能决定的能力、资源、报价或授权边界。
4. 调研、亮点选择、分章写作和独立审计完成后，在 Gate 2 处理红队根因并确认定稿。
5. 只在最终汇报明确 `submission_ready=true`，且人工待办中的硬项已清零后，才把 `技术方案-完整版.md` 作为递交稿继续排版。

第一次使用建议跟随[完成第一份方案](docs/tutorial/first-proposal.md)。

## 常用调用

```text
/proposal <标书路径或粘贴文本> [素材路径] [-quick|-deep] [-logic|-story|-vision|-evidence] [-auto] [-legacy]
```

- 无深度标志为 standard；`-quick` 用于小标或时间紧，`-deep` 用于重点标。
- 无叙事标志时按标书选择；叙事只决定表达，不得裁剪评分项或加强承诺。
- 默认 v3；`-v3` 只是兼容标志。只有显式 `-legacy` 才运行 2.x 回退链。
- `-auto` 生成的是保守草案。任何 assumed 决策都会阻断直接递交。
- `casebase/` 中非 `_` 开头的案例会自动纳入；沟通、踏勘和售前纪要须标 `[notes]`。

模式与组合示例见[选择深度、叙事和关卡模式](docs/how-to/choose-modes.md)。

## 你会得到什么

```text
<方案标题>-<时间戳>/
├── 技术方案-完整版.md          客户可见递交稿
├── 分册/                       目录、对照表、综述和各章
├── _内部研判.md                内部：策略、来源、fit、红队
├── _人工待办.md                内部：假设、缺口、占位符
└── _state/                     内部：canonical、快照和审计状态
```

下划线开头的文件和目录一律不递交。输出、归档和就绪信号详见[输出与可递交状态参考](docs/reference/outputs-and-readiness.md)。

## 文档

| 你现在要做什么 | 文档 |
|:---|:---|
| 第一次完整跑通 | [完成第一份方案](docs/tutorial/first-proposal.md) |
| 安装或注册 | [安装与注册](docs/how-to/install-and-register.md) |
| 整理标书、素材和纪要 | [准备输入](docs/how-to/prepare-inputs.md) |
| 选择 quick / deep / narrative / auto | [选择运行模式](docs/how-to/choose-modes.md) |
| 录入和核验真实案例 | [维护案例库](docs/how-to/manage-casebase.md) |
| 恢复 v3 或迁移旧项目 | [恢复与迁移](docs/how-to/resume-or-migrate.md) |
| 处理失败、stale 或 blocker | [解除阻断](docs/how-to/resolve-blockers.md) |
| 查命令与参数 | [命令行参考](docs/reference/command-line.md) |
| 查流程、Task 和 Gate | [流程与硬门参考](docs/reference/workflow-and-gates.md) |
| 查状态文件和写权限 | [Canonical 状态参考](docs/reference/canonical-state.md) |
| 查诊断字段和严重度 | [诊断参考](docs/reference/diagnostics.md) |
| 理解为什么改成 v3 | [为什么是 v3](docs/explanation/why-v3.md) |
| 理解客户价值底座 | [客户价值模型](docs/explanation/customer-value-model.md) |
| 理解证据、授权和隐私 | [证据、授权与隐私](docs/explanation/evidence-authority-and-privacy.md) |
| 理解快照与兑现审计 | [兑现审计与快照](docs/explanation/realization-and-snapshots.md) |

## 安全边界

proposal 不会替投标人确认资质、业绩、人员、报价、资源容量或保证性 KPI。以下任一情况存在时，输出不可直接递交：

- 最终状态为 `submission_ready=false` 或未给出最终可递交结论；
- mandatory、真实性、预算、授权、法律或兑现硬门未通过；
- 正文仍有占位符，或 `_人工待办.md` 仍有硬项；
- 运行使用了未经人工确认的 `-auto` 假设。

`customer-fit` 只用于内部发现短板，是规则敏感性区间，不是评委分数或中标概率。

## 维护

仓库入口包括 [SKILL.md](SKILL.md)、[RULES.md](RULES.md)、[DECISIONS.md](DECISIONS.md)、[TYPES.md](TYPES.md) 和 `tools/`。修改前请阅读[贡献指南](CONTRIBUTING.md)。
