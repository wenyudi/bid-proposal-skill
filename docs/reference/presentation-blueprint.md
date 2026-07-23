# Presentation blueprint 参考

`presentation-blueprint/v1` 是定稿正文与图片 PPT 工作流（image2 等）之间的交接契约。它是正文的派生压缩层，不拥有新的方案事实：proposal v4 生成它、`validate-blueprint` 校验它、下游图片工作流消费它。

## 版本兼容
v4 在 v1 上只**新增可选字段**（`visual.avoid`、`slides[].unverified_notes`、`asset_requests[].evidence`、`asset_requests[].stand_in_for`、`deck.field_contract`），不改动既有字段语义——旧消费者忽略未知字段即可继续工作。v3 曾用于快照绑定的 `generation_snapshot_id`、`brief_hash` 降级为可选，v4 校验器忽略它们。

## 顶层字段
| 字段 | 含义 |
|:---|:---|
| `schema_version` | 固定 `presentation-blueprint/v1` |
| `deck` | 全案定义、主线、视觉系统与 signature/sample 页 |
| `slides` | 按页码排列的核心与附录页 |
| `generation_snapshot_id` / `brief_hash` | 可选历史字段；v4 校验器忽略 |

## `deck`
`title/audience/purpose/aspect_ratio/language` 定义演示语境。`core_thesis` 必须与一页纸记忆句逐字一致。`signature_slide_ref` 指向唯一 `role=signature + emphasis=signature` 的核心页；`sample_slide_ref` 与它相同，让下游用最能代表主张的页确认视觉。`story_arc[]` 用 `beat/purpose/slide_refs`，全部 core 页恰好各出现一次，appendix 不进 arc。`visual_system` 含 `concept/palette/typography/image_language/layout_rhythm`。

## `slides[]`
| 字段 | 含义 |
|:---|:---|
| `id/n` | 全局唯一 slide ID 与从 1 连续的页码 |
| `track` | `core` 或 `appendix`；全部 core 在 appendix 之前 |
| `role` | cover、context、insight、thesis、signature、mechanism、roadmap、visual_proof、risk、compliance 等语义页型 |
| `emphasis` | standard、signature、supporting、reference |
| `title` | 结论式上屏标题 |
| `audience_takeaway` | 本页要让评委形成的新判断 |
| `render_text` | 需图片准确呈现的 title、subhead、key_points、labels；`render_text.title` 与 `slide.title` 一致 |
| `visual` | 主画面、构图、`prompt_seed`、`avoid`（规避元素，v4 新增）、比例与素材请求 |
| `source_refs` | 本页引用的正文依据（可选）|
| `truth_boundary` | 本页事实、scope、能力与承诺边界 |
| `transition` | 核心页的 `inherits/hands_off` |
| `unverified_notes[]` | v4 新增；本页承载的虚构/待核实点，对应 `_风险与待核实.md` |

## 素材请求
每个 `visual.asset_requests[]`：
| 字段 | 值 |
|:---|:---|
| `asset_id` | 全稿唯一 |
| `role` | 素材在页面承担的证明或表达任务 |
| `mode` | `generate`、`strict_input`、`style_reference` |
| `status` | `generate`、`available`、`needs_user` |
| `path` | available 时必须存在（相对 blueprint 目录或 `--assets-root`）|
| `evidence` | v4 新增布尔；证据类素材（案例现场、资质、数据截图）标 `true` |
| `rights_status` | `cleared` 或 `needs_review`（后者仅 warning）|
| `stand_in_for` | v4.3 新增可选；意向图/图标**顶位素材**指向被顶位的证据素材 `asset_id`（完整商业稿：缺真图的页由顶位视觉做满版面，真图到位后整图替换）|

**证据图红线**：`evidence=true` 的素材禁止 `mode=generate`，只能 `strict_input` + `needs_user` 真实素材。生成的假证据图一旦上屏即为直接造假，与可核实替换的虚构文字性质不同。

## 校验器
```text
validate-blueprint --blueprint FILE [--output-dir DIR] [--assets-root DIR]
```
检查：schema 版本；页码连续、track 顺序、story arc、page role；`render_text.title == title`；唯一 signature 与 sample 映射；上屏文案无 URL / 内部 ref / **索要占位表述**（待提供/待补充/请上传/素材缺失/占位）；画面不为真实素材**预留空位**（位置留白/预留/待贴）；含 `needs_user` 证据位的页有可渲染顶位视觉；`stand_in_for` 指向同页素材；素材字段完整、available 路径存在、证据图红线；`unverified_notes` 格式；缺 `field_contract` 给 warning。通过后确定性写 `outline.md`（末尾含**素材替换清单**）与 `presentation-validation.json`（`status=ready_for_outline_review`、`image_generation_started=false`）。

## 下游消费契约
`deck.field_contract` 声明：`on_screen`（`title`/`render_text`/`visual` 渲染层——页面上只允许出现这些）与 `internal_only`（`unverified_notes`/`truth_boundary`/`source_refs`——**绝不渲染上屏、绝不写进讲稿/speech**，只服务替换清单与内部核对）。下游图片/成稿/讲稿工作流必须按此契约消费；素材缺口的人工替换动作以 outline 的"素材替换清单"为准。

## 交接
把 `outline.md` 与 `deck-blueprint.json` 交给下游图片工作流；后者完成风格确认、图像后端确认、signature 样张批准、逐页生成、视觉 QA 和 PPTX 装配。生产包另含 `kv-brief.md`（主视觉交接单），KV/效果图延展工作流（如 kv-studio）可直接使用。proposal 本身不调用图片模型。正文或素材变化后，重新生成 blueprint 并重跑 `validate-blueprint`。
