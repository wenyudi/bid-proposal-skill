# Presentation blueprint 参考

`presentation-blueprint/v1` 是已审计 proposal 与图片 PPT 工作流之间的派生交接契约。它不属于五份 canonical，也不拥有新的方案事实。

## 顶层字段

| 字段 | 含义 |
|:---|:---|
| `schema_version` | 固定 `presentation-blueprint/v1` |
| `generation_snapshot_id` | 当前 proposal generation snapshot |
| `brief_hash` | 当前 presentation context brief hash |
| `status` | 固定 `outline_draft`；下游确认 outline 后维护自己的生产状态 |
| `deck` | 全案定义、主线、视觉系统和 signature/sample 页 |
| `slides` | 按页码排列的核心与附录页面 |

## `deck`

`title/audience/purpose/aspect_ratio/language` 定义演示语境。`core_thesis` 必须与 approved recall line 完全相同；`signature_output_ref` 来自 canonical 一页纸策略。

`signature_slide_ref` 指向唯一 `role=signature + emphasis=signature` 的核心页；`sample_slide_ref` 与它相同，让下游用最能代表主张的内容页确认视觉。

`story_arc[]` 使用 `beat/purpose/slide_refs`。全部 core 页恰好出现一次；appendix 不进入 story arc。

`visual_system` 包含：

- `concept`：贯穿全案的视觉概念；
- `palette`：可读的配色方向字符串；
- `typography`：字体性格与层级；
- `image_language`：摄影、插画、3D、拼贴、信息图或效果图语言；
- `layout_rhythm`：不同页型如何形成节奏。

## `slides[]`

| 字段 | 含义 |
|:---|:---|
| `id/n` | 全局唯一 slide ID 与从 1 开始的连续页码 |
| `track` | `core` 或 `appendix`；全部 core 位于 appendix 之前 |
| `role` | cover、context、insight、thesis、signature、mechanism、roadmap、visual proof、risk、appendix 等语义页型 |
| `emphasis` | standard、signature、supporting、reference |
| `title` | 结论式上屏标题 |
| `audience_takeaway` | 本页要让评委形成的新判断 |
| `render_text` | 需要图片准确呈现的 title、subhead、key points 与 labels |
| `visual` | 主画面、构图、prompt seed 与素材请求 |
| `source_refs` | 当前 audited brief 白名单内的 Requirement、VP、Claim、Action、Evidence 或 visible output |
| `truth_boundary` | 本页事实、scope、能力和承诺边界 |
| `transition` | 核心页的 `inherits/hands_off` |

`render_text.title` 与 `slide.title` 完全相同。核心页通常使用 0–5 个短要点；校验器对超过五项给 warning，不机械阻断附录信息量。

## 素材请求

每个 `visual.asset_requests[]` 包含：

| 字段 | 值 |
|:---|:---|
| `asset_id` | 全稿唯一 |
| `role` | 素材在页面承担的证明或表达任务 |
| `mode` | `generate`、`strict_input`、`style_reference` |
| `status` | `generate`、`available`、`needs_user` |
| `path` | available 时必须存在；相对路径以 blueprint 所在目录解析 |
| `rights_status` | `cleared` 或 `needs_review` |

generated asset 使用 `mode=generate + status=generate`。strict input 与 style reference 使用 available 或 needs_user；`needs_review` 形成 warning，供下游生成前处理。

## 校验器

```text
validate-presentation --state-dir DIR --brief FILE --blueprint FILE
                      [--output-dir DIR]
```

校验器检查：

- brief、snapshot、canonical fingerprint 与 realization 当前有效；
- 页码、track 顺序、story arc 和 page role；
- approved recall line、唯一 signature 与 sample 映射；
- `required_presentation_refs` 覆盖和 source ref 白名单；
- 上屏文案不含 raw URL 或内部 ref；
- visual brief、truth boundary、transition 与素材状态完整；
- available 素材路径真实存在。

通过后确定性写 `deck-blueprint.json`、`outline.md` 和 `presentation-validation.json`。validation 状态为 `ready_for_outline_review`，并明确 `image_generation_started=false`。

## 失效

任一 canonical、source/run authority、正式章节或 authoritative realization 改变后，原 presentation brief/blueprint 重新编译和校验。图片工作流不得用旧 blueprint 覆盖新 proposal 内容。
