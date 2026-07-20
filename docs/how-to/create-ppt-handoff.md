# 生成 PPT 结构稿并交给图片工作流

本流程适合最终需要用图片版 PPT 展现的提案。proposal 负责内容主线、逐页结构、准确文案与真实性边界；image2、codex-ppt 或其他图片工作流负责视觉风格、样张、逐页图片和 PPTX。

启动时可直接加 `-ppt`：

```text
/proposal /绝对路径/招标文件.pdf /绝对路径/投标素材/ -deep -ppt
```

## 1. 先完成可审计内容

先按主流程完成一页纸策略、分章写作、独立 realization audit 和 Gate 2。PPT planner 只读取已经审计为 valid 的 Requirement、Claim、Action 和 visible output，因此正文变化后应先重新审计。

最终装配后确认当前变量：

```bash
export STATE=/绝对路径/当前运行目录
export BUNDLE=/绝对路径/最后一次装配卷册
```

## 2. 编译 presentation brief

```bash
python3 tools/prop_tools.py compile-context \
  --state-dir "$STATE" --target presentation \
  --token-budget 36000
```

成功后得到：

```text
$STATE/derived/briefs/presentation.json
```

它只包含已审计安全投影，并给出：

- `allowed_presentation_refs`：页面可以引用的内部依据；
- `required_presentation_refs`：整份结构稿必须覆盖的 Requirement、lead VP 和 required visible output；
- 已填实 signature 成果及字段；
- 章节 spine、动作、资源、验收与公开 Evidence；
- 页型、素材状态和画幅契约。

## 3. 生成机器结构稿

让 presentation planner 读取 brief、[PPT 结构与视觉叙事模式](../../references/presentation-patterns.md)及 `prompts/task3d_presentation_blueprint.md`，写：

```text
$STATE/presentation/deck-blueprint.json
```

planner 只规划页面，不生成图片或 PPTX。核心提案和附录分轨，signature 页同时作为下游建议样张页。

## 4. 校验并生成人读结构稿

```bash
python3 tools/prop_tools.py validate-presentation \
  --state-dir "$STATE" \
  --brief "$STATE/derived/briefs/presentation.json" \
  --blueprint "$STATE/presentation/deck-blueprint.json" \
  --output-dir "$BUNDLE/_PPT生产包"
```

通过后得到：

```text
_PPT生产包/
├── deck-blueprint.json
├── outline.md
└── presentation-validation.json
```

`outline.md` 是给人确认的 PPT 结构稿；JSON 是给图片工作流的逐页任务依据。`ready_for_outline_review` 表示结构可审阅，不表示图片已经生成。

## 5. 确认四个关键点

打开 `outline.md`，优先检查：

1. 核心轨能否用一条短链讲清客户张力、洞察、选择、主亮点、执行和证明；
2. signature 页是否是全案最想让评委记住的一页；
3. 效果图系列、长名单、尺寸、预算和预案是否进入附录轨，核心轨仍有节奏；
4. `needs_user` 素材的页码、用途和权利状态是否准确。

结构问题修改 `deck-blueprint.json` 后重新运行校验。若发现策略或事实问题，回到 Task 2.5、Task 3 或 Gate owner 修根因，再重新冻结、审计和编译 presentation brief。

## 6. 交给 image2 或图片 PPT 工作流

下游工作流读取：

| proposal 输出 | 图片工作流用途 |
|:---|:---|
| `outline.md` | 确认页序、页数、核心/附录与素材映射 |
| `deck.core_thesis` | 全案 deck context 的核心主张 |
| `deck.visual_system` | 初始风格方向；仍需用户确认最终视觉 |
| 每页 `render_text` | 图片中需要准确呈现的文案 |
| 每页 `audience_takeaway` | local context 与本页完成标准 |
| 每页 `visual` | 构图、主画面和正向 image prompt seed |
| `asset_requests` | strict input、style reference 与生成素材映射 |
| `truth_boundary/source_refs` | 生成和 QA 时保持事实与承诺边界 |

图片工作流继续按以下顺序：

1. 确认 outline 和素材映射；
2. 确认一套视觉风格；
3. 确认 image2 或其他图片后端；
4. 先生成 blueprint 指定的 signature/sample 页；
5. 样张批准后逐页生成；
6. 检查中文文字、主线、素材保真、视觉一致性和页面缺失；
7. 组装 PPTX。

若提供 PDF/PPT 作为风格参考，先渲染代表页并从实际可见页面提取配色、字体层级、留白、图像语言和版式节奏；把这些文件标为 `style_reference`。其中的客户内容、数字和方案主张不会成为本项目事实来源。

## 7. 理解边界

proposal 的结构校验无法证明图片模型最终把中文、数字、Logo 和技术图渲染正确。最终图片仍需逐页视觉 QA；strict input 资产需要确认真实路径、内容保真和发布权限。只有原 proposal receipt 与图片版人工复核都通过，才进入最终递交排版。
