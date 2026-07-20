# Canonical 状态参考

v3 把可修改事实集中在五份 canonical JSON。正文、compiled brief、coverage、diagnostics、customer-fit 和 realization 都是派生产物，不能反向静默改写 canonical。

## 五份事实来源

| 文件 | schema | 拥有的事实 | 顶层实体集合 |
|:---|:---|:---|:---|
| `requirements.json` | `requirements/v3` | 项目、采购人、预算、mandatory、scoring、deliverables | `mandatory`、`scoring`、`deliverables` |
| `customer-value.json` | `customer-value/v2` | 客户角色、需求、判断标准、决策路径、价值、Claim、Metric 和证据关系 | `roles`、`needs`、`criteria`、`decision_paths`、`value_propositions`、`claims`、`metrics`、`evidence_links` |
| `delivery-plan.json` | `delivery-plan/v1` | 投标人交付角色、动作、资源、客户依赖和验收 | `delivery_roles`、`actions`、`resource_envelopes`、`customer_dependencies`、`acceptance_contracts` |
| `strategy.json` | `strategy/v5` | 一页纸策略、标题、叙事、决策地图和章节主线 | `sections`；DecisionJob、`strategy_role` 与 `visible_outputs` 内嵌章节，另含 `open_questions` |
| `intel-pool.json` | `intel-pool/v3` | 本标 Evidence 原记录、研究 gap 和 research manifest | `evidence`、`gaps`、`research_manifest` |

每份文件都有 `schema_version` 和整数 `revision`。实体 ID 在五份文件之间全局唯一、稳定；引用必须解析到允许的实体类型。只读兼容层仍接受 `customer-value/v1` 与 `strategy/v3/v4`，从旧 link / 顶层 DecisionJob 派生等价视图；新 bootstrap/migration 只写 v2/v5，不静默改写旧 archive。

## 关系主链

```text
Requirement ───────────────→ Section
                                ↑
OnePageStrategy ─────────→ Section.strategy_role

CustomerRole ─┐
CustomerNeed ─┼→ DecisionPath → ValueProposition
Criterion ────┘                ↓
                              Claim ← EvidenceLink ← Evidence
                                ↓
                        DeliveryAction → Resource / Dependency / Acceptance
                                ↓
                  Section(DecisionJob + visible output) → realization
```

Requirement 轨和客户价值轨并行存在：章节映射到 Requirement 只证明结构覆盖，DecisionPath 只证明 Role × Need × Criterion 连接；submission 还要求正文独立审计为 addressed / entailed，并把 required visible output 的字段判为 filled。visible output 的 grounding 只能引用标书 Requirement 或具有有效客户可见投影的 active Evidence，private/internal Evidence 不能借 semantic sidecar 充当正文依据。

`one_page_strategy` 是研究后策略的单一事实源，包含 client context、客户张力、洞察、core thesis / recall line、逻辑链、互换测试、proof plan、落地可信度、五维自评和人工 approval。每个 Section 自己拥有 `strategy_role.contribution/inherits/hands_off`；编译器据此生成全案 spine，不另存第二份可手改地图。

Section 的 `narrative_role` 使用 `primary`、`secondary:<mode>`、`fixed:logic` 或 `fixed:evidence`。编译器把它与全案 narrative 合并为本章唯一 effective guide；报价、合规、资质章固定为 logic/evidence，secondary 只有 presentation authority。

## 核心状态轴

| 对象 | 状态或轴 |
|:---|:---|
| CustomerNeed | `candidate → active / contested / superseded / rejected` |
| ValueProposition | `candidate / investigating / qualified / selected / publishable / rejected / superseded`；组合角色 lead / supporting / reserve 独立记录 |
| Claim | lifecycle：`candidate / draft_ready / publishable / contested / withdrawn`；另有 content kind、epistemic status、commitment level 三轴 |
| Claim content kind | `fact / insight / proposal / target` |
| Claim epistemic status | `evidenced / inferred / assumed` |
| commitment | `none / intended / committed`；Action 只使用 `intended / committed` |
| Action selection | `candidate / selected / superseded / rejected` |
| Action readiness | `unassessed / planned / confirmed / blocked` |
| Gate decision | `open / resolved / assumed` |
| DecisionJob kind | `understand / believe / value / deliver / safe / choose` |

不同轴不能互相替代。例如 selected Action 不等于 confirmed，evidenced Claim 不等于 committed，resolved Gate 也只授权 `affected_refs` 中的明确对象和用途。

## Manifest

### `source-manifest.json`

schema 为 `source-manifest/v1`。记录原始标书、素材等来源的 ID、路径、类型、visibility 和 hash。工具能访问路径时会计算 hash；路径内容改变会触发 fatal，而不是自动接受新版本。

### `run-manifest.json`

schema 为 `run-manifest/v1`。记录：

- `engine: v3`、engine version 和 policy version；
- `fallback_policy: explicit`；
- `mode`、`lang`；
- 当前 run 声明的能力。

engine、版本、policy 或显式回退策略不一致会被视为状态冲突。

## 状态目录布局

```text
STATE/
├── requirements.json
├── customer-value.json
├── delivery-plan.json
├── strategy.json
├── intel-pool.json
├── source-manifest.json
├── run-manifest.json
├── legacy-to-v3-map.json        仅迁移时可能存在
├── proposals/
│   ├── changes/                 ChangeSet、receipt
│   └── diagnostics/             Task / Gate 提案诊断
├── sections/                    section-0.md、section-N.md
└── derived/
    ├── briefs/
    │   ├── strategy-review.json
    │   ├── sections/
    │   └── redteam/
    ├── realization/
    ├── manifests/
    │   ├── generation-snapshot.json
    │   ├── run-validation.json
    │   └── acceptance-receipt.json
    ├── coverage.json
    ├── diagnostics.json
    ├── customer-fit.strategy.json
    └── customer-fit.submission.json
```

`derived/` 可以重建，不是 authority。brief 与 realization 直接携带 path/hash/snapshot lineage，不再维护可漂移的 `artifacts.json`。不要手改 hash、snapshot 或 realization status 来通过硬门。

## ChangeSet v1

最低结构：

```json
{
  "schema_version": "changeset/v1",
  "changeset_id": "CS-G1-CAPABILITY-01",
  "producer": "gate1",
  "base_revisions": {
    "customer-value.json": 2,
    "delivery-plan.json": 1,
    "strategy.json": 1
  },
  "rationale": "记录用户确认及其对价值与交付边界的影响",
  "validate_stage": "draft",
  "operations": [],
  "affected_refs": [],
  "human_required": false
}
```

每个 touched canonical 都必须出现在 `base_revisions`。支持：

- JSON Pointer：`add`、`replace`、`remove`、`test`；
- 实体操作：`transition`、`upsert`。

应用顺序是：检查 base revision → 在副本应用全部 operation → 增加 touched file revision → 验证完整候选状态 → 原子替换 → 写 receipt → 失效 generation/final receipts。任一步失败都不保留半组修改；旧 brief/realization 会因 hash 不匹配自动拒绝。

## Producer 写权限

| producer | 权限 |
|:---|:---|
| `main`、`gate1`、`gate2`、`human`、`migration` | 可按规则修改 canonical；仍须通过完整验证 |
| `task2` | 可写 `intel-pool.json`；在 `customer-value.json` 仅可写 `evidence_links` |
| `task2.5` | 可收敛 one-page / Big Idea / narrative、Section spine 与 customer value / delivery 的选择编排；不能自批策略，仍受语义与 authority 冻结规则限制 |
| `task3`、`task3.5`、`redteam` | 无 canonical 写权限 |

Task 2.5 不能删除 canonical 历史、改客户语义集合或 decision map、创建新 VP 核心语义、自批 Gate/策略、增加 authority 或提升 committed / confirmed。研究后可改 one-page / Big Idea / narrative，但任何已批准策略语义变化都必须把 approval 退回 pending。

## Authority 解析

`authority_ref` 只有解析到以下之一并覆盖当前对象/用途时才有效：

1. 明确授权该对象或用途的 Requirement；
2. active/current、high/verified、用途获准且与对象 scoped 的 Evidence；
3. human-resolved、无 assumption risk、`affected_refs` 包含该对象的 `GATE-*` 决策。

任意字符串、无关条款、assumed Gate、第三方案例或只有材料清单的 Evidence 都不能解锁承诺。
