# 输出、归档与可递交状态参考

proposal 同时产生客户可见卷册和内部审计状态。文件是否以下划线开头，是第一层递交边界；最终 `submission_ready` 是第二层边界。

## 卷册布局

装配成功后，在指定 output 基目录中生成：

```text
<安全化方案标题>-YYYYMMDD-HHMMSS/
├── 技术方案-完整版.md
├── 分册/
│   ├── 00-目录.md
│   ├── 01-应标响应与评分对照表.md
│   ├── 02-方案综述.md            存在 section-0 时
│   └── NN-<章节标题>.md
├── _内部研判.md
├── _人工待办.md                 最终阶段生成
├── _state/                      archive-state 后生成
└── _state.last-good/            重复归档时可能存在
```

英文输出会使用对应英文名称；应以 `assemble-proposal` 返回的 `output_path`、`bundle_dir` 和 `internal_brief` 为准，不要沿用上一次时间戳路径。

## 递交边界

| 内容 | 客户可见 | 用途 |
|:---|:---:|:---|
| `技术方案-完整版.md` | 是，人工复核后 | 标题、项目信息、目录、对照表、综述和正文 |
| `分册/` | 是，按排版需要 | 拼 Word / PDF、单章复核 |
| `_内部研判.md` | 否 | 模式、叙事、来源 URL、Gate、fit、红队与内部边界 |
| `_人工待办.md` | 否 | 占位符、assumed、Evidence gap、硬门和薄弱项 |
| `_state/` | 否 | canonical、sections、snapshot、diagnostics、realization |
| `_state.last-good/` | 否 | 上一次成功状态归档 |

下划线内部内容一律不递交，也不要复制其中的 URL、内部 ID、private 原句、fit 或诊断到客户稿。

## 完整版结构

装配顺序固定为：

1. 方案标题；
2. 项目名称、项目编号、采购人、待填投标人和日期；
3. 目录；
4. mandatory、deliverables、scoring 对照表；
5. 方案综述（存在 valid `section-0.md` 时）；
6. 正式章节。

对照表只证明 Requirement 到章节的结构映射；正文是否实质回答仍由独立 realization audit 判断。

## 四层就绪信号

| 层 | 信号 | 能证明什么 | 不能证明什么 |
|:---|:---|:---|:---|
| canonical | `check-canonical --stage submission` 的 `submission_ready=true` | canonical 与当前 authoritative realization 无 fatal / blocker | 当前 report 已通过 compliance、QA、红队 |
| archive | `_state/archive-manifest.json` 的 `canonical_submission_ready` | 归档时 canonical / realization gate 状态 | report-level 可递交；字段 `submission_ready` 不会冒充完整验收 |
| customer fit | `gates.passed`、overall range/band | 内部客户适配短板与规则敏感性 | 评委分数、中标概率、hard gate 豁免 |
| 最终交付 | 主流程汇报的 `submission_ready` | 同一最新 report 已完成全套验收 | 人工对真实资质、报价和法定模板的责任 |

最终 `submission_ready=true` 至少要求同一轮、同一路径的：

- compliance 通过；
- QA 硬项通过；
- canonical submission 与全部正式章、综述 realization 通过；
- customer-fit 无 hard gate failure；
- Gate 2 根因已处理；
- 不存在 assumed、硬占位符或其他不可递交待办。

任何 mandatory、法律、真实性、预算、授权、private 泄露或无效 publishable path 都不能由 fit、叙事、红队意见或 accepted risk 抵消。

## `-auto` 输出

`-auto` 可以装配完整草案，但 assumed 决策会：

- 进入 `_内部研判.md` 和 `_人工待办.md`；
- 降级相关 committed / confirmed / 发布授权；
- 使最终 `submission_ready=false`。

最终汇报应以“已生成草案，不可直接递交”开头，而不是用“生成完成”掩盖状态。

## last-good 行为

装配先在 staging 构建全部文件并检查编码。成功切换前不会触碰当前卷册；同标题的上一份成功卷册移动到 output 基目录下：

```text
.last-good/<安全化方案标题>/
```

状态归档也先在 staging 完成。若 bundle 已有 `_state/`，它会在新状态安装前移动为 `_state.last-good/`。归档失败会保留或恢复上一份成功状态。

`archive-state --allow-draft` 允许保存结构完好的非 submission-ready 状态，并在 archive manifest 中明确 `canonical_submission_ready=false`、`submission_ready=false`。它仍拒绝 schema、source 或 fatal 损坏。

## 从归档恢复时

`_state/` 保存 canonical 和 sections，但旧 artifact、brief 和 realization 中的绝对路径不跨目录续用。复制到新目录后必须重新冻结/编译全部 snapshot-bound brief，复审正式章节和综述，再对新 report 重跑全部报告级验收。

详细步骤见[恢复与迁移](../how-to/resume-or-migrate.md)。

## 递交前人工清单

- 最终汇报明确 `submission_ready=true`；
- 打开的路径是最后一次装配返回的 report；
- `_人工待办.md` 的硬项已清；
- 投标人全称、日期、人员、资质、业绩、数字和报价已核验；
- 法定文件另按标书模板完成；
- 只导出客户可见文件，未夹带任何下划线内部内容。
