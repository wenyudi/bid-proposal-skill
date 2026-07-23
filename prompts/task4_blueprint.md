# Task 4 — 图片 PPT 结构稿

从定稿正文压出 `deck-blueprint.json`：一份交给下游图片工作流（image2）的逐页结构稿。你不生成图片，只定义每页要让读者（甲方）形成什么判断、上屏什么文案、画什么画面、要什么素材。

占位变量：`{LANG}` · `{BLUEPRINT_BRIEF}`（一页纸 + 定稿正文 + 素材清单 + 建议配图点 + 已合并虚构申报）· `{TMPDIR}` · `{ASPECT}` 默认 16:9 · `{DECK_MODE}` 默认 `视觉分镜式`（无人演讲/图片 PPT；有人讲标才 `演讲式`）。

## 交付目标
按 `{DECK_MODE}`（默认**视觉分镜式**）定页数与密度：视觉分镜式靠"页多、每页一个画面、信息量小"减轻阅读负担，把能拆的子部件各拆一页画面，让甲方自己翻阅、没有讲解也能顺着画面看完整套论证；signature 页作为制胜一击兼下游样张；大量效果图/长名单/尺寸材质进附录轨。

## 依据
- `{BLUEPRINT_BRIEF}`：一页纸、定稿正文（唯一事实来源）、素材清单（路径/可用状态）、建议配图点。
- `references/presentation-patterns.md`：页型、三种叙事骨架、core/appendix、signature、视觉系统、素材三模式、证据图红线。
- `docs/reference/presentation-blueprint.md`：`presentation-blueprint/v1` 字段契约。

## 工作顺序
1. 定 `deck`：title/audience/purpose/aspect_ratio/language、`core_thesis`（= 一页纸记忆句，逐字一致）、`visual_system`（从品牌素材或 style_reference 提取一次，全案统一）、`story_arc`。
2. 排 `slides`：按 `{DECK_MODE}`——**视觉分镜式（默认）**把每个子部件各拆一页画面（如 BSB 7 道工序 = 1 页总述 + 7 页逐道工序画面；每个案例、每类设备、每名核心角色各一页），页数宁多勿少（core 常 30–60 页）；**所有可枚举的组（工序/闸门/案例/系列集/角色/设备类）都比照拆页，别厚此薄彼——拆了团队就也拆工序、闸门、系列**；**演讲式**用最短说服链、一页一判断。core 轨走 客户张力→洞察→选择→signature→机制/行动→证明/保障→收束 + 决定性效果图；appendix 轨接效果图系列、长名单、尺寸材质、预算、风险查验。core 全部在 appendix 之前，页码从 1 连续。
3. 每页写：结论式 `title`、`audience_takeaway`、`render_text`（**视觉分镜式：结论标题 + 少量关键指标/标签，信息量小、画面是主角；演讲式：最短上屏文案**；其 `title` 与 slide.title 一致）、`visual`（主画面/构图/`prompt_seed`/`avoid` 规避元素/比例）、`asset_requests`、`transition`、页级 `unverified_notes`（**只标真正承载虚构/待核实的页，别每页都挂**，对应 `_风险与待核实.md`）。**数据/报价/含精确数字的页：`prompt_seed` 只生成无数字底图，数字一律走 `render_text` 叠排**（图像模型对数字/中文易错、且改数要重出图）。
4. 唯一一张 `role=signature + emphasis=signature` 的 core 页，同时作为 `sample_slide_ref`。
5. 素材三模式与**证据图红线**：`generate` 只用于效果图/示意图（对未来方案的想象）。过往案例现场照、资质证书、数据截图等**证据类**素材，`asset_requests[].evidence=true`，且只能 `mode=strict_input` + `status=needs_user`（真实素材），绝不 `generate`；同时在 `_风险与待核实.md` 记一条。
6. **完整商业稿**（缺口不上台面）：每页都要立即可渲染成完整页面——含 `needs_user` 证据位的页，同时给一个 `generate` 意向图/图标顶位（`stand_in_for=<该证据 asset_id>`，`avoid` 注明不得仿冒真实照片/证件/公章/截图）；`prompt_seed`/`main` **不写"真实图位置留白/预留/待贴"**，顶位画面把版面做满、真图到位后整图替换；上屏文案**绝不出现"待提供/待补充/请上传/素材缺失/占位"**。缺口信息只进页级 `unverified_notes` 与 outline 素材替换清单。deck 顶层写 `field_contract`：`{"on_screen": ["title","render_text","visual"], "internal_only": ["unverified_notes","truth_boundary","source_refs"], "note": "internal_only 绝不上屏、不进讲稿；素材缺口只走 outline 素材替换清单"}`。

## 输出契约
- `{TMPDIR}/presentation/deck-blueprint.json`，`schema_version="presentation-blueprint/v1"`，字段依 `docs/reference/presentation-blueprint.md`（含可选字段 `visual.avoid`、`slides[].unverified_notes[]`、`asset_requests[].evidence`、`asset_requests[].stand_in_for`、`deck.field_contract`）。
- **分批写盘防中断**：先写「deck 元数据 + core 轨」落盘，再读回续写 appendix 轨合并——大 deck 一次性输出易断，断点从已落盘部分续，不整体重来。
- `{TMPDIR}/presentation/kv-brief.md`：给 /kv-studio 的主视觉交接单——核心主张与记忆句、制胜轴、`visual_system` 摘要、signature 页的 KV 任务描述、需 KV 延展的页清单（页码+画面任务）、参照素材路径（style_reference/available）、真实性边界（证据类不得生成）。
- 返回 JSON：`{"slides": N, "core": Nc, "appendix": Na, "signature_slide": "id", "needs_user_assets": Nu}`。

## 完成判据
- 页码连续、core 全在 appendix 前、`story_arc` 覆盖每个 core 页恰一次、唯一 signature = sample。
- 每个 `evidence=true` 素材都是 `strict_input`（不是 generate）。
- 每页 `render_text.title == title`；客户面字段（title/render_text/**audience_takeaway**/deck 级文案）无 URL / 内部 ID，**无"待提供/待补充/请上传/素材缺失/占位"，也无草案状态与内部定价规则（"草案/待授权/暂按/补实件/非递交版/按限价X%"）**——takeaway 会进讲稿，同样是客户面。
- **所有字段**（title、render_text、`audience_takeaway`、truth_boundary、story_arc purpose）都不出现"评委/评分/满分/顶格/多少分"——指读者就用"读者/贵行/甲方"。slide 是给甲方看的。
- 每个含 `needs_user` 证据位的页有可渲染顶位视觉（generate 意向图/图标或完整 prompt_seed）；画面不为真实素材预留空位；`stand_in_for` 指向同页素材。
- deck 顶层含 `field_contract` 消费契约。
- 交给 `validate-blueprint` 前自检以上，减少往返。
