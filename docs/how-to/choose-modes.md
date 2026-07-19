# 选择深度、叙事和关卡模式

先按项目风险选择深度，再决定是否指定叙事，最后决定是否保留人工关卡。引擎通常不需要选择：v3 是默认值。

## 选择深度

| 场景 | 参数 | 影响 |
|:---|:---|:---|
| 小额、时间紧、竞争较弱，或先做初稿快评 | `-quick` | 聚焦研究；每批审 3 章；1 个 integrated 红队 |
| 常规政企传媒标 | 不写参数 | standard；每批审 3 章；buyer_expert + audit_rival 两组红队 |
| 预算大、多轮答辩、竞争强或风险高 | `-deep` | 更宽候选池和 Evidence；每批审 2 章；四独立红队 |

深度影响工作量，不改变硬门。`-quick` 也不能跳过 mandatory、真实性、预算、授权和兑现检查。

示例：

```text
/proposal /路径/常规项目.pdf
/proposal /路径/小额项目.pdf -quick
/proposal /路径/重点项目.pdf /路径/素材/ -deep
```

## 选择主叙事

不指定时，Task 1 会根据标型、评分权重和评委环境自动选择。只有你有明确表达方向时才加标志：

| 参数 | 适合 | 主要表达方式 |
|:---|:---|:---|
| `-logic` | 技术分高、专家评委、暗标、复杂机制 | 问题—归因—方法—路径—证据 |
| `-story` | 城市、文旅、公益、品牌传播、有讲标 | 以客户/城市/用户为主人公的克制叙事 |
| `-vision` | 多年框架、长期运营、战略合作 | 未来图景、里程碑与能力沉淀 |
| `-evidence` | 投放、增长、量化运营、报价敏感 | 数据、对标、测算口径和验收机制 |

叙事只有表达权，没有语义裁剪权。报价、合规和资质内容始终以 logic / evidence 方式呈现；任何叙事都不能删评分项、改变 Evidence、扩大 scope 或把 intended 写成保证。

示例：

```text
/proposal /路径/城市形象项目.pdf -deep -story
/proposal /路径/媒介投放项目.pdf -evidence
```

## 决定是否使用 `-auto`

默认保留人工关卡：

- standard / deep：Gate 1 决策确认 + Gate 2 红队定稿；
- quick：用 integrated 红队减少调用；若要 `submission_ready`，仍需 Gate 2 attestation。

只有需要无人值守地产出保守草案时才使用 `-auto`：

```text
/proposal /路径/项目.pdf -quick -auto
```

`-auto` 会把仍需人拍板的问题记录为 `assumed`，并撤销或降级依赖这些问题的 committed / confirmed / 发布授权。它可以解锁安全草案，但最终一定是 `submission_ready=false`，直到人工确认并重新复验。unknown 资源、预算和容量继续保持 unknown；系统使用 draft_ready/intended/planned 语义，不为推进生成补造 provisional low/high。

不要用 `-auto` 绕过团队可用性、报价、免费增值、关键 KPI、SLA、案例署名或数字发布授权。

## 引擎选择

- 无引擎参数：v3。
- `-v3`：兼容用的 no-op，效果与无参数相同。
- `-legacy`：显式运行 2.x 紧急回退，只用于旧项目维护。

不要同时写 `-v3` 和 `-legacy`，也不要把 v3 canonical、章节或 Gate 结果与 legacy 产物混合。旧项目希望采用 v3 时，应按[迁移旧项目](resume-or-migrate.md)另建状态目录。

## 推荐组合

```text
# 常规项目，让系统自动选叙事
/proposal /路径/招标文件.pdf /路径/素材/

# 重点城市传播标，强调客户叙事
/proposal /路径/招标文件.pdf /路径/素材/ -deep -story

# 时间紧，先生成不可直接递交的保守草案
/proposal /路径/招标文件.pdf -quick -auto

# 明确维护旧 2.x 项目
/proposal /路径/旧项目目录 -legacy
```
