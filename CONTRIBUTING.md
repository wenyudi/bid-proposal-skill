# 贡献指南

感谢改进 proposal。v3 的首要约束是：新增能力不能降低 mandatory、真实性、预算、授权、隐私或兑现硬门，也不能让客户稿暴露底层状态。

## 开发环境

- Python 3.8+；运行时代码只依赖标准库。
- Git。
- 能运行 `unittest` 的本地终端。

克隆并进入仓库后，无需安装 Python 依赖即可运行测试：

```bash
python3 -m unittest discover -s tests
python3 -m py_compile tools/prop_tools.py tools/prop_v3.py
```

## 先确定改动归属

| 改动 | 主要位置 |
|:---|:---|
| v3 调度顺序或 Task 输入输出 | `SKILL.md`、`prompts/` |
| 硬门、写权限、客户稿边界 | `RULES.md` |
| Gate 单题交互和决策状态 | `DECISIONS.md` |
| 标型/评委/章节先验与调度 | `TYPES.md`、`profiles.json`；叙事写作 guide 只在 `narratives.json` |
| canonical、事务、brief、realization、fit、归档 | `tools/prop_v3.py` |
| 装配、合规、QA 和兼容 CLI | `tools/prop_tools.py` |
| 2.x 紧急回退 | `LEGACY.md`、`prompts/legacy/` |
| 案例人工事实源 | `casebase/` |
| 用户文档 | `README.md`、`docs/` |

五份 canonical 只有各自的事实归属。不要为了省一次查找，把同一事实复制到另一份可手改 JSON；derived 文件也不能反向成为写入依据。

## 修改流程

1. 先阅读 [SKILL.md](SKILL.md)、[RULES.md](RULES.md) 和与改动相关的参考文档。
2. 为行为变化先补或调整测试，尤其覆盖失败路径、回滚、stale、private 泄露和 `-auto` 降级。
3. 保持 v3 为默认引擎。只有用户显式 `-legacy` 才能进入旧链；不要在 v3 失败时静默回退。
4. canonical 修改必须继续走带 base revision 的 ChangeSet，并在写入前验证完整候选状态。
5. 修改 CLI 参数、输出字段、状态结构或硬门时，同步更新对应 `docs/reference/` 页面。
6. 修改用户流程时，同步检查教程和 how-to，避免把内部维护步骤写成普通用户必做步骤。

## 文档约定

文档采用 Diátaxis 分工：

- `docs/tutorial/`：带首次使用者完成一个学习闭环。
- `docs/how-to/`：解决一个明确任务，只给完成任务所需步骤。
- `docs/reference/`：准确描述命令、状态、输出和诊断。
- `docs/explanation/`：说明设计原因、取舍和模型关系。

不要在多个页面复制同一份长命令或 schema。优先在参考页保留唯一完整定义，其他页面链接过去。示例必须使用占位路径和虚构项目名，不要提交真实标书、客户私密材料、底价或未授权案例。

## 兼容性要求

- 不新增 legacy 功能；只维护紧急回退和旧项目可读性。
- schema 变化必须显式升级 `schema_version` 或提供安全迁移，不能把 unknown / inferred 自动升为 verified / committed / publishable。
- 当前 generation snapshot 绑定五份 canonical 与 source/run fingerprint。除非同时完成依赖级失效设计和测试，否则任一 authority 输入变化后都应让 snapshot-bound brief、章节、摘要和 realization 失效。
- v3.2 新状态使用 `customer-value/v2` 与 `strategy/v5`；旧 customer-value/v1 与 strategy/v3/v4 archive 必须保持只读兼容，不能静默重写。显式迁移的一页纸策略只能 assumed，不能冒充人工批准。
- `archive-state --allow-draft` 只能放宽 submission blocker，不能接收 schema、source 或 fatal 损坏。
- 客户稿继续禁止 URL、内部 ID、private 原句、策略/模式/工具痕迹和适配度。

## 提交前检查

```bash
python3 -m unittest discover -s tests
python3 -m py_compile tools/prop_tools.py tools/prop_v3.py
python3 tools/prop_tools.py --help
git diff --check
```

还应人工检查：

- 新增或修改的 Markdown 相对链接能够从所在页面打开；
- 文档里的命令参数与 `--help` 一致；
- 新诊断包含稳定的 `rule_id`、根因、严重度、owner 和可执行修复；
- 失败路径不会覆盖当前 canonical、当前卷册或 last-good；
- 测试和示例不包含真实客户信息。
- `git status` 不出现新增或修改的 `reports/` 运行产物；清理历史误提交只允许删除，后续输出一律不入库。

提交说明应概括行为变化及其安全影响。若改动影响 schema、默认流程、递交就绪或兼容链，请在说明中单独指出。
