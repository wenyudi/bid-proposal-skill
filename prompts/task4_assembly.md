装配 + 合规校验 + 自评 + 红队 + QA —— **由主 agent 直接执行**（非独立 task agent）。本文件是命令参考，权威流程见 SKILL.md 第 1 节。

## 输入
- {TMPDIR}/strategy.json（方案框架 + section→addresses 映射，装配对照表的依据）
- {TMPDIR}/requirements.json（应标清单，合规校验的依据）
- {TMPDIR}/intel-pool.json（情报 URL → 归档进 `_内部研判.md`，**不进递交稿**）
- {TMPDIR}/sections/section-0.md（方案综述）+ section-1..N.md（各章正文）
- 输出目录：{SKILLDIR}/reports/{LANG}/

## 命令序列

```bash
# 1. 装配 → 技术标卷册目录
python {TOOLSDIR}/prop_tools.py assemble-proposal \
  --strategy {TMPDIR}/strategy.json \
  --requirements {TMPDIR}/requirements.json \
  --intel {TMPDIR}/intel-pool.json \
  --sections-dir {TMPDIR}/sections/ \
  --mode {depth_mode} \
  --output {SKILLDIR}/reports/{LANG} \
  --lang {LANG}
# → Proposal assembled: <合并版递交稿>   → $REPORT
# → BundleDir: <卷册目录>                → $BUNDLE
# → InternalBrief: <_内部研判.md>        → $BRIEF
#
# 卷册内容：技术方案-完整版.md（递交）/ 分册/NN-*.md（递交）
#           _内部研判.md（不递交）
# 递交稿里没有元数据块、没有 URL 书目、没有研报声明——那些都在 $BRIEF 里

# 2. ⚡ 硬阻断之一：合规校验——强制项/评分项零遗漏
python {TOOLSDIR}/prop_tools.py check-compliance \
  --requirements {TMPDIR}/requirements.json \
  --strategy {TMPDIR}/strategy.json \
  --report "$REPORT"
# → JSON: missing_mandatory / missing_scoring / coverage_pct
# → missing_mandatory 非空 = 废标风险，必须补：把缺失 id 映射到合适章节（编辑 strategy），
#   重派该章 agent 补写 → 重新装配 → 重新校验，直到清空

# 3. 竞争力自评（机械信号）
python {TOOLSDIR}/prop_tools.py self-score \
  --requirements {TMPDIR}/requirements.json \
  --strategy {TMPDIR}/strategy.json \
  --report "$REPORT" --mode {depth_mode}
# → SELFSCORE: estimated_score=.. addressed_pct=.. diff_count=.. within_budget=.. weak_items=..

# 4. 货币符号转义
python {TOOLSDIR}/prop_tools.py escape-currency "$REPORT"

# 5. ⚡ 硬阻断之二：QA（含内部信息泄露检查）
python {TOOLSDIR}/prop_tools.py qa-proposal "$REPORT" \
  --mode {depth_mode} --strategy {TMPDIR}/strategy.json \
  --requirements {TMPDIR}/requirements.json --lang {LANG}
# → checks.no_internal_leak.passed=false 必须修：递交稿混进了叙事策略/模式/版本/
#   生成时间/URL/对手法的自我描述。定位章节 → 重写 → 重装配
# → 警告级：buyer_focus（甲方导向词频）/ exec_summary / no_sales_cta / no_latex / no_id_leak
#   不阻断，但必须带进 Gate 2 给人看

# 6. 红队四视角（并行 4 个 agent，prompt: task4_redteam.md，角色见 TYPES.md）
mkdir -p {TMPDIR}/redteam
# buyer / expert / audit / rival，各写 {TMPDIR}/redteam/{role}.json
# 致命项（废标风险 / 高权重评分项实质未答）自动补，最多 2 轮；其余进 Gate 2 交人取舍

# 7. 人工待办清单 + 内部研判归档
python {TOOLSDIR}/prop_tools.py human-todo \
  --requirements {TMPDIR}/requirements.json \
  --strategy {TMPDIR}/strategy.json \
  --report "$REPORT" --mode {depth_mode} \
  --output "$BUNDLE/_人工待办.md" --lang {LANG}
# → HUMANTODO: blocking=.. scoring=.. weak=..
# 再用 write 把「竞争力自评 + 红队结论」追加进 $BRIEF，让卷册自带完整内部备忘
```

## 验收清单
- [ ] check-compliance: missing_mandatory 为空（否则废标风险，必须补）
- [ ] check-compliance: missing_scoring 为空或已补
- [ ] qa-proposal: `no_internal_leak.passed=true`（⚡ 递交稿零内部泄露）
- [ ] qa-proposal: `structure.passed=true`（标题/项目信息头/目录/对照表齐备）
- [ ] 红队致命项已清零
- [ ] 差异化点数 ≥ 模式下限
- [ ] 报价在预算带内（人工核对报价章）
- [ ] 无内部 id（S/M/D 编号）泄露正文

## 清理
QA 通过后：`rm -rf {TMPDIR}`（Unix）或 `Remove-Item -Recurse -Force {TMPDIR}`（Windows）
⚠️ `$BUNDLE` 内的 `_内部研判.md` 与 `_人工待办.md` 不在 TMPDIR，不会被删。
**递交时下划线开头的文件一律不要交。**

---
```
proposal skill · 政企传媒投标方案生成
```
