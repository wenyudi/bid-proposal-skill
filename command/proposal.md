---
description: 商业方案与投标方案 v4 — 拆评分表、制胜一页纸、缺口虚构补全+风险登记、响应对照索引与默认图片 PPT 结构稿
---

<command-instruction>
Load and follow the `proposal` skill exactly.

```text
skill(name="proposal")
```

Parse `$ARGUMENTS`:
- 标书/brief 输入：本地文件路径或粘贴文本（必需，否则向用户索要并等待）；素材目录可直接含 .doc/.docx/.ppt/.pptx/.pdf/扫描图片——Task 0 摄入自动转换（OCR 密钥配置见 `~/.config/proposal/ocr.json`）
- 可选素材：能力/案例/报价/团队/品牌路径；沟通纪要（踏勘/答疑/售前 → 标 `[notes]`，只作内部校准，不进正文）
- 案例库：`casebase/` 非 `_` 开头案例自动纳入
- 标志：
  - `-no-ppt` → 只出正文，跳过图片 PPT 结构稿（默认产出 PPT）
  - `-auto`   → 跳过唯一人工确认，产保守草案；assumed 决策与虚构占位阻断直接递交
- 无深度/叙事标志：永远尽力做到最好，叙事按标型自动选
</command-instruction>

<user-request>
$ARGUMENTS
</user-request>

---
```
proposal skill · 4.5.0 · lightweight commercial & bid proposal
```
