# 恢复 v3 运行或迁移旧项目

恢复和迁移都必须在新目录进行。历史 bundle、旧状态和案例库保持不变，避免一次失败覆盖 last-good。

## 先识别来源

- v3 归档：bundle 中有 `_state/run-manifest.json`，其中 `engine` 为 `v3`，并含五份 canonical。
- legacy 项目：只有旧 `requirements.json`、`strategy.json`、情报或章节，没有 v3 run manifest。
- 只有最终 Markdown：不能恢复完整状态；应把原标书和可核验素材作为新 run 输入。

不要因为旧数据存在就自动进入 legacy。默认和 `-v3` 始终使用 v3；只有显式 `-legacy` 才维护旧链。

## 从 v3 `_state` 恢复

创建新的空工作目录，再复制归档状态；不要在 bundle 内直接继续写：

```bash
export BUNDLE=/绝对路径/方案卷册
export NEW_STATE=/绝对路径/恢复工作区
mkdir -p "$NEW_STATE"
cp -a "$BUNDLE/_state/." "$NEW_STATE/"
python3 tools/prop_tools.py check-canonical --state-dir "$NEW_STATE" --stage draft --write-derived
```

如果 source manifest 指向的原始标书或素材已移动、内容已改变，检查会失败。恢复原文件或以新输入启动新 run；不要手改 hash 来掩盖变化。

复制的 canonical 和 `sections/` 可以作为恢复材料，但旧 brief/realization 的 compiled path 不构成新目录的有效证明。v3.2 不使用 artifact registry。继续写作前必须复核迁移生成的 assumed 一页纸策略，并：

1. 重新通过 generation gate；
2. 在新目录冻结当前快照；
3. 为每个正式章节重新运行 `compile-context`；
4. 用当前 brief 重新进行独立 realization audit；
5. 重新生成并审计方案综述；
6. 重新装配并运行 `validate-run`；归档时运行 `finalize-run` 生成新 receipt。

不要把旧 manifest 的路径改成新路径后直接标记 current。当前 v3 snapshot 绑定全部五份 canonical，任一 canonical 变化都会使旧章节与摘要失效。

## 把 legacy 状态迁移到 v3

目标目录必须是新的、尚无 canonical 的目录：

```bash
python3 tools/prop_tools.py migrate-state \
  --source-dir /绝对路径/旧状态目录 \
  --output-dir /绝对路径/新-v3-状态目录 \
  --mode standard \
  --lang zh
```

迁移会建立 v3 canonical、source/run manifest 和 `legacy-to-v3-map.json`，并检查 draft 状态。它不会修改旧源目录。

迁移采用保守语义：

- 旧候选不会自动变为 selected、publishable 或 committed；
- unknown / inferred 不会升级为 verified；
- 旧案例文字不会自动获得我方能力或公开发布授权；
- legacy 章节与自评不会冒充 v3 realization。

迁移成功后，把新目录交给 v3 流程完成 Gate 1、Evidence、Task 2.5、快照、重新写作或复审。不要在同一 run 中混用 legacy 章节和 v3 Gate 结果。

## 只想继续 legacy

如果目标只是紧急维护 2.x 项目，在请求中明确写 `-legacy`：

```text
/proposal /绝对路径/旧项目目录 -legacy
```

legacy 没有 v3 customer-value、delivery-plan、compiled brief、realization 或 customer-fit 保证。若最终切回 v3，应结束旧 run，另建目录执行迁移。

## 验证恢复结果

```bash
python3 tools/prop_tools.py check-canonical --state-dir /绝对路径/新状态目录 --stage draft
python3 tools/prop_tools.py json-get /绝对路径/新状态目录/run-manifest.json engine
```

只有重新完成本轮报告级 compliance、QA、customer-fit 和 Gate 2，才可以判断最终 `submission_ready`；旧 archive 中的 `canonical_submission_ready` 不能替代这次验收。
