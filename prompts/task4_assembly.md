装配 + 合规校验 + 自评 + QA —— **由主 agent 直接执行**（非独立 task agent）。本文件是命令参考。

## 输入
- {TMPDIR}/strategy.json（方案框架 + section→addresses 映射，装配对照表的依据）
- {TMPDIR}/requirements.json（应标清单，合规校验的依据）
- {TMPDIR}/intel-pool.json（参考来源提取）
- {TMPDIR}/sections/section-*.md（各章正文）
- 输出目录：{SKILLDIR}/reports/{LANG}/

## 命令序列

```bash
# 1. 装配（生成封面/元数据/目录/应标响应与评分对照表/正文/参考来源/声明）
python {TOOLSDIR}/prop_tools.py assemble-proposal \
  --strategy {TMPDIR}/strategy.json \
  --requirements {TMPDIR}/requirements.json \
  --intel {TMPDIR}/intel-pool.json \
  --sections-dir {TMPDIR}/sections/ \
  --mode {depth_mode} \
  --output {SKILLDIR}/reports/{LANG}/ \
  --lang {LANG}
# → 输出 "Proposal assembled: <路径>"，提取为 $REPORT

# 2. ⚡ 合规校验（阻断点）——强制项/评分项零遗漏
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
  --report "$REPORT"
# → SELFSCORE: estimated_score=.. addressed_pct=.. diff_count=.. within_budget=.. weak_items=..

# 4. 货币符号转义
python {TOOLSDIR}/prop_tools.py escape-currency "$REPORT"

# 5. QA
python {TOOLSDIR}/prop_tools.py qa-proposal "$REPORT" --mode {depth_mode} --strategy {TMPDIR}/strategy.json --lang {LANG}
# → JSON: passed + 各项 checks；不通过项局部补刀（单章重写≤1次）
```

## 验收清单
- [ ] check-compliance: missing_mandatory 为空（否则废标风险，必须补）
- [ ] check-compliance: missing_scoring 为空或已补
- [ ] qa-proposal passed=true（编码/四段式结构/目录/对照表/章数/尾部/子节编号/字数）
- [ ] 差异化点数 ≥ 模式下限
- [ ] 报价在预算带内（人工核对报价章）
- [ ] 无内部 id（S/M/D 编号）泄露正文

## 清理
QA 通过后：`rm -rf {TMPDIR}`（Unix）或 `Remove-Item -Recurse -Force {TMPDIR}`（Windows）

---
```
proposal skill · 政企传媒投标方案生成
```
