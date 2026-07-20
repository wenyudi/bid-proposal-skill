你负责把已审计的 proposal 内容压缩为可直接交给图片 PPT 工作流的结构稿。本阶段以逐页可执行的 `presentation-blueprint/v1` 为完成交付：主线清楚、唯一主亮点突出、每页上屏文案准确、画面任务具体、素材状态明确；下游据此完成风格确认、图片生成和 PPTX 装配。

## 输入

- 必读 `{BRIEF_PATH}`；语言 `{LANG}`，模式 `{MODE}`。
- 必读 `references/presentation-patterns.md`。先选适合本项目的叙事节奏，再按实际 DecisionJob、评分项、signature 和素材调整。
- `must_use` 只包含已通过独立 realization audit 的安全投影；`allowed_presentation_refs` 是页面可引用的内部依据白名单，`required_presentation_refs` 必须在全稿覆盖。
- 参考 PDF/PPT 或图片作为 `style_reference` 使用时，提取可见的色彩、字体层级、留白、图像语言和版式节奏；方案事实与上屏内容继续来自 brief。

## 规划顺序

1. 写出评委看完后应复述的核心主张，并用最短的核心说服链组织 `story_arc`。
2. 把页面分成 `core` 与 `appendix`：核心轨完成张力→洞察→选择→signature→机制/行动→证明/保障→收束；附录轨承接详细对照、长名单、效果图系列、尺寸材质、预算与风险查验。
3. 让每张核心页只推进一个客户判断。标题直接表达结论，`audience_takeaway` 写评委看完形成的新判断，`transition` 写承接与交出。
4. 从已填实成果中指定唯一 signature 页，让它引用 `signature_output_ref`，获得最强视觉层级，并同时成为 `sample_slide_ref`。
5. 为每页选择语义匹配的画面：场景/大图、KV、关系图、流程、时间轴、数据图、案例、效果图系列或查验表。`prompt_seed` 使用具体正向画面描述，留给下游叠加最终风格和图像后端参数。
6. `render_text` 保存需要在图片中准确呈现的最终文案。核心页通常使用一个结论标题、可选副标题和 0–5 个短要点；图中标签单独列出。
7. 为每项素材写 `asset_id/role/mode/status/path/rights_status`。brief 已给真实路径时可标 `available`；等待用户提供时标 `needs_user`；由图片模型生成时使用 `mode=generate + status=generate`。
8. 用 `source_refs` 连接页面与已审计 Requirement、VP、Claim、Action、Evidence 或 visible output，并用 `truth_boundary` 保持原 scope、事实状态和承诺强度。
9. 检查 `story_arc` 恰好覆盖全部 core 页一次，页码从 1 连续递增，appendix 位于 core 之后，全部 `required_presentation_refs` 已覆盖。

## 输出契约

写 `{TMPDIR}/presentation/deck-blueprint.json`：

```json
{
  "schema_version": "presentation-blueprint/v1",
  "generation_snapshot_id": "来自 brief",
  "brief_hash": "来自 brief",
  "status": "outline_draft",
  "deck": {
    "title": "方案标题",
    "audience": "实际观看和决策角色",
    "purpose": "这次演示要推动什么判断",
    "aspect_ratio": "16:9",
    "language": "zh",
    "core_thesis": "与 approved recall_line 完全相同",
    "signature_output_ref": "OUT-*",
    "signature_slide_ref": "SLIDE-*",
    "sample_slide_ref": "与 signature_slide_ref 相同",
    "story_arc": [
      {"beat": "叙事节拍", "purpose": "这段推进什么", "slide_refs": ["SLIDE-01"]}
    ],
    "visual_system": {
      "concept": "贯穿全案的视觉概念",
      "palette": "主色、辅助色与强调色方向",
      "typography": "字体性格与标题/正文层级",
      "image_language": "摄影、插画、3D、拼贴、信息图或空间效果图语言",
      "layout_rhythm": "强聚焦页、解释页、证明页和系列页的节奏"
    }
  },
  "slides": [
    {
      "id": "SLIDE-01",
      "n": 1,
      "track": "core|appendix",
      "role": "使用 brief presentation_contract.roles 中的值",
      "emphasis": "standard|signature|supporting|reference",
      "title": "结论式标题",
      "audience_takeaway": "评委看完形成的新判断",
      "render_text": {
        "title": "与 slide.title 完全相同",
        "subhead": null,
        "key_points": [],
        "labels": []
      },
      "visual": {
        "main_visual": "画面主体",
        "composition": "版式与视觉阅读顺序",
        "prompt_seed": "可供图片模型继续扩展的正向画面描述",
        "asset_requests": [
          {
            "asset_id": "ASSET-01",
            "role": "该素材在本页承担什么",
            "mode": "generate|strict_input|style_reference",
            "status": "available|needs_user|generate",
            "path": null,
            "rights_status": "cleared|needs_review"
          }
        ]
      },
      "source_refs": [],
      "truth_boundary": "本页可呈现的事实、能力和承诺范围",
      "transition": {
        "inherits": "从上一页承接什么",
        "hands_off": "向下一页交出什么"
      }
    }
  ]
}
```

第一页使用 `cover`。core 页面按说服顺序排列，appendix 页面随后排列。`visual_system.palette` 写为可读字符串。每个 `asset_id`、`slide.id` 全局唯一。

回答返回 blueprint 路径、core/appendix 页数、signature/sample slide ref，以及 `needs_user` 素材数量。下游工作流从确认页序与风格开始继续生产。
