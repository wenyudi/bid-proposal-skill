# 维护真实案例库

`casebase/` 是公司案例的人工事实源。目标不是堆案例描述，而是把每个案例拆成有范围、有材料、有权限的原子证据，供不同标书安全复用。

## 新建案例

从模板复制一个不以 `_` 开头的 Markdown 文件：

```bash
cp casebase/_template.md casebase/case-city-brand-2025.md
```

也可以按行业建立子目录。`README.md` 和 `_` 开头文件不会被当作案例。

## 填写 CaseRecord

编辑 frontmatter，至少确认：

- `case_id` 全库唯一且长期稳定；
- 项目、客户、服务日期、行业和服务范围；
- `bidder_role` 是 `prime`、`consortium`、`subcontract` 或 `unknown`；
- `engagement_scope` 只写我方真实承担范围；
- `status` 是 `draft`、`active`、`contested` 或 `retired`；
- 客户名、Logo、评价和数字结果是否分别获授权；
- 核验材料是否真实存在。

不清楚时使用 `unknown` 或 `false`，不要按常见行业做法推断。案例可匿名使用，也不代表金额、Logo、评价或数字结果自动获批。

## 拆分原子证据

在“原子证据”的 `case-evidence/v1` JSON 中，每个 item 只写一条可核验事实。例如，合同范围和验收结果应分成两项，因为它们的证明边界不同。

每项至少写清：

- `id`：稳定、唯一；
- `kind`：参与事实、交付事实、能力观察、结果观察、评价、奖项或资质；
- `statement`、`scope`、`period`；
- `source_material`：合同条款、验收页码、截图位置或证书编号；
- `verification_status`；
- `visibility` 和 `allowed_uses`；
- `limitations`：这份材料不能证明什么。

直接使用 [`casebase/_template.md`](../../casebase/_template.md)，完整字段含义见 [`casebase/README.md`](../../casebase/README.md)。

## 核验并授权

按以下顺序升级状态：

1. 只有文字描述：保持 `asserted`。
2. 已列出待查材料：`material_listed`。
3. 人工实际核对了材料及适用范围：才可设为 `verified`。
4. 过期、冲突或被否定：改为 `expired`、`contested` 或 `rejected`，不要覆盖历史。

匿名正文使用还需要 `safe_title`、`approved_wording` 和 `publication_authority`。三者缺一，证据仍留在 internal；模型不能自行批准。

量化结果还要补齐指标定义、统计对象或公式、单位、基线、结果、时间窗、数据源、归因和容差。口径不完整时可以参与匹配，不能支持 publishable 数字 Claim。

## 在本标中选择案例

proposal 会先看本标对类似业绩的年份、角色、材料和硬排除，再比较机制、规模、渠道、时效、我方角色和结果口径。它选择的是最小充分 proof portfolio，不设固定案例数量。

以下边界不会因行业相似而放宽：

- 合同只证明参与和合同范围；
- 验收只证明被验收的部分；
- 截图只证明特定时点数据；
- 历史结果不自动证明归因或本项目结果；
- 第三方案例不能证明我方能力。

## 提交前检查案例文件

```bash
python3 tools/prop_tools.py check-encoding casebase/case-city-brand-2025.md
git diff --check
```

再人工确认 JSON 代码块可解析、ID 不重复、材料位置可找到、授权未被扩大。不要把合同原件、个人信息、底价或未授权客户材料直接提交到公共仓库。
