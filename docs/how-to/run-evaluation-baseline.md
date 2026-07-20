# 运行方案质量基线

本流程用两套完全虚构的输入保存可复核的 pre-change 和 post-change 结果。目标是比较同一 fixture 的相对修订，不是制造黄金答案、评委分或中标概率。完整卷册、内部状态和人工评分一律保存在仓库外。

## 1. 确认基线窗口

pre-change 必须来自已经冻结的旧 release/worktree 或此前保存的仓库外 run；当前 v3.2 工作树只能产生 post-change。记录固定 commit、policy 和测试结果：

```bash
git status --short
git diff -- SKILL.md narratives.json prompts/task3_section_agent.md prompts/task3c_realization_audit.md
python3 -m unittest discover -s tests
```

若没有真实 pre-change 产物，可以单独运行 post-change 验证，但结论必须标 `comparison_withheld`；不要把当前结果倒签为基线。旧 worktree 与当前 run 必须使用不同的 TMPDIR、报告目录和 agent context。

运行还需要一个真正加载 proposal skill 的 LLM 宿主，并能完成文件操作、agent 调度和所需研究。单独调用 tools/prop_tools.py 或用手写正文不能替代宿主端到端运行。

## 2. 建立仓库外目录

从仓库根目录创建基线根目录，并确认它不在仓库内：

```bash
REPO=$(pwd -P)
COMMIT=$(git rev-parse --short HEAD)
BASE="${HOME}/proposal-baselines/${COMMIT}"
case "$BASE" in
  "$REPO"/*) echo "STOP: baseline directory is inside the repository"; exit 1 ;;
esac
mkdir -p "$BASE"
printf '%s\n' "$BASE"
```

推荐的每次运行布局如下：

```text
~/proposal-baselines/<commit>/<fixture>/<timestamp>/
├── report-bundle/
├── manifest.md
├── source.sha256
├── report.sha256
├── bundle.sha256
├── quality-reviewer-1.md
├── quality-reviewer-2.md
├── quality-consensus.md
└── host-last-message.txt
```

如果工作树有未提交但属于基线窗口的正确性修复，在 manifest 中记录 git commit、git status 和 git diff 的 SHA-256；不要只写 commit 后假装工作树干净。

## 3. 在宿主会话运行两条 fixture

在仓库根目录分别新开宿主会话，逐字运行：

```text
/proposal tests/fixtures/tender-digital-demo.md tests/fixtures/materials-digital-demo.md -standard -auto -logic
```

```text
/proposal tests/fixtures/tender-content-demo.md tests/fixtures/materials-content-demo.md -deep -auto -story
```

记录每条命令的开始与结束时间。不要让第二条复用第一条的 TMPDIR、canonical、章节或报告目录。

auto 会对只有投标人能决定的容量边界采用保守假设，因此预期 submission_ready=false。这不是基线运行失败；只要流程完成并明确生成的是安全草案，就继续评估其中是否形成了足够具体、可判断的客户可见内容。schema/source/fatal 损坏、流程中断或没有完整卷册才算运行失败。

fixture 已提供完成正文所需的全部安全项目事实，不需要真实网址或客户资料。正常 Evidence 流程仍应保留；若宿主没有联网能力或研究没有必要，按实际情况记录，不能伪造来源。

## 4. 复制每次完整产物

从宿主最终消息取得本次最新 bundle 路径。为每条运行创建独立目录，并复制完整卷册：

```bash
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
DEST="$BASE/digital-demo/$STAMP"
mkdir -p "$DEST"
cp -a "<本次 assemble 返回的 bundle 路径>" "$DEST/report-bundle"
```

内容 fixture 把 digital-demo 改为 content-demo。复制后确认技术方案、分册、内部研判、人工待办和 state 都属于同一次 run。不要从不同重试拼装一份“最好看”的结果。

保存 source 和报告 hash：

```bash
sha256sum tests/fixtures/tender-digital-demo.md tests/fixtures/materials-digital-demo.md > "$DEST/source.sha256"
sha256sum "$DEST/report-bundle/技术方案-完整版.md" > "$DEST/report.sha256"
find "$DEST/report-bundle" -type f -print0 | sort -z | xargs -0 sha256sum > "$DEST/bundle.sha256"
sha256sum -c "$DEST/report.sha256"
```

内容 fixture 的 source.sha256 改用 tender-content-demo.md 与 materials-content-demo.md。若报告语言或文件名不同，以 assemble 返回的实际 report 路径为准，并在 manifest 中记录。

## 5. 填写运行 manifest

每个 DEST 的 manifest.md 至少记录：

| 字段 | 要求 |
|:---|:---|
| phase | pre-change 或 post-change |
| fixture | digital-demo 或 content-demo |
| git state | commit、branch、dirty 状态、git diff SHA-256 |
| host | 宿主名称与版本；模型可见时记录模型，不可见写 unknown |
| timing | 含时区的开始、结束和总耗时 |
| command | 完整 proposal 命令、depth、narrative、auto |
| source manifest | 两个输入路径、大小、mtime 与 SHA-256 |
| runtime | Python、操作系统、可用工具与联网状态 |
| Gate assumptions | 每个 assumed 决策、影响对象和 submission_ready=false 原因 |
| run outcome | 成功/中断、最终报告路径、重试次数和每次根因 |
| verification | 单元测试结果、compliance、QA、canonical submission、customer-fit 与待办摘要 |
| hashes | report.sha256、bundle.sha256 及其校验时间 |
| uncertainty | 网络研究、模型、宿主、重试或人工判断漂移 |

source manifest 应来自本次运行的实际输入，而不是事后重新创建的文件。若输入在运行中变化，本次结果不可比较，须重跑。

## 6. 填完质量清单

复制[方案修订质量评估清单](../reference/quality-checklist.md)三份到 DEST：

```bash
cp docs/reference/quality-checklist.md "$DEST/quality-reviewer-1.md"
cp docs/reference/quality-checklist.md "$DEST/quality-reviewer-2.md"
cp docs/reference/quality-checklist.md "$DEST/quality-consensus.md"
```

两名评审先独立填写 reviewer 文件，再共同填写 consensus。对每个 required document proof 的字段标 filled、partial 或 missing，并保留客户可见正文 quote 和位置；随后计算 proof_object_coverage、lead_proof_coverage、proof_field_completeness、external_substitution_violations、deferred_proof_burden、project_specificity 和 unexpected_claims。

pre-change 阶段按正文人工判定；不要假装已有结构化成果 manifest。v3.2 post-change 可以读取 authoritative `visible_output_realizations`，但仍须复核正文和 strategy critic 的五测结果。

## 7. 运行 post-change 并盲评

完成质量改动后，用相同 fixture、参数、用户回答或 auto 状态，以及尽可能相同的模型与宿主配置重跑。目录改为新的 timestamp，phase 写 post-change，不覆盖 pre-change。

由不参与评分的人把 pre/post 客户可见报告随机命名为 A 和 B，单独保存映射。评审先判硬门，再判 proof、十维 customer-fit 和人工质量，冻结两份原始记录后才揭盲。只有硬门不回退且 proof 与关键人工项改善，才能说该 fixture 的新版本相对更优。

网络研究变化单列为 uncertainty。不要为了逐字一致关闭 Evidence，也不要比较漂亮词频。两个 fixture 结论不一致时分别报告。

## 8. 处理失败或宿主不可用

每次运行失败都记录发生阶段、原始错误、是否重试和根因。只允许按 proposal 主流程修复运行问题，不得为了让基线好看而修改 tools、prompt、RULES、fixture 验收要求或手工补写报告。

如果当前执行器不能调用真实 LLM 宿主、无法完成全流程，或不能把产物安全保存到仓库外：

- fixture、清单和本文仍可保留；
- 对比状态标记为 BLOCKED / comparison_withheld，并保留 fixture 与失败记录；
- 仍可做当前版本 forward test，但不能据此声称相对旧版更优；
- 不创建虚假的 manifest、评分或报告 hash。

真实 shadow run 可以作为第三条仓库外校准，但不能替代这两条 fixture，也不得把真实客户资料复制进仓库。
