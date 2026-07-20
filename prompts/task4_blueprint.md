# Task 4 — 图片 PPT 结构稿

从定稿正文压出 `deck-blueprint.json`：一份交给下游图片工作流（image2）的逐页结构稿。你不生成图片，只定义每页要让评委形成什么判断、上屏什么文案、画什么画面、要什么素材。

占位变量：`{LANG}` · `{BLUEPRINT_BRIEF}`（一页纸 + 定稿正文 + 素材清单 + 建议配图点 + 已合并虚构申报）· `{TMPDIR}` · `{ASPECT}` 默认 16:9。

## 交付目标
用最短的核心页序把主张送进评委脑子，signature 页作为制胜一击兼下游样张；把大量效果图、长名单、尺寸材质等放进附录轨，不稀释核心说服链。

## 依据
- `{BLUEPRINT_BRIEF}`：一页纸、定稿正文（唯一事实来源）、素材清单（路径/可用状态）、建议配图点。
- `references/presentation-patterns.md`：页型、三种叙事骨架、core/appendix、signature、视觉系统、素材三模式、证据图红线。
- `docs/reference/presentation-blueprint.md`：`presentation-blueprint/v1` 字段契约。

## 工作顺序
1. 定 `deck`：title/audience/purpose/aspect_ratio/language、`core_thesis`（= 一页纸记忆句，逐字一致）、`visual_system`（从品牌素材或 style_reference 提取一次，全案统一）、`story_arc`。
2. 排 `slides`：core 轨用最短说服链（客户张力→洞察→选择→signature→机制/行动→证明/保障→收束）+ 1–2 张决定性效果图；appendix 轨接效果图系列、长名单、尺寸材质、预算、风险查验。core 全部在 appendix 之前，页码从 1 连续。
3. 每页写：结论式 `title`、`audience_takeaway`、`render_text`（需图片准确呈现的文案，其 `title` 与 slide.title 一致）、`visual`（主画面/构图/`prompt_seed`/`avoid` 规避元素/比例）、`asset_requests`、`transition`、页级 `unverified_notes`（本页承载的虚构/待核实点，对应 `_风险与待核实.md`）。
4. 唯一一张 `role=signature + emphasis=signature` 的 core 页，同时作为 `sample_slide_ref`。
5. 素材三模式与**证据图红线**：`generate` 只用于效果图/示意图（对未来方案的想象）。过往案例现场照、资质证书、数据截图等**证据类**素材，`asset_requests[].evidence=true`，且只能 `mode=strict_input` + `status=needs_user`（真实素材），绝不 `generate`；同时在 `_风险与待核实.md` 记一条。

## 输出契约
- `{TMPDIR}/presentation/deck-blueprint.json`，`schema_version="presentation-blueprint/v1"`，字段依 `docs/reference/presentation-blueprint.md`（含本版新增可选字段 `visual.avoid`、`slides[].unverified_notes[]`、`asset_requests[].evidence`）。
- 返回 JSON：`{"slides": N, "core": Nc, "appendix": Na, "signature_slide": "id", "needs_user_assets": Nu}`。

## 完成判据
- 页码连续、core 全在 appendix 前、`story_arc` 覆盖每个 core 页恰一次、唯一 signature = sample。
- 每个 `evidence=true` 素材都是 `strict_input`（不是 generate）。
- 每页 `render_text.title == title`；上屏文案无 URL / 内部 ID。
- 交给 `validate-blueprint` 前自检以上，减少往返。
