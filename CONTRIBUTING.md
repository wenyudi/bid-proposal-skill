# 贡献指南

感谢改进 proposal。v4 是低仪式、高工艺的商业/投标方案流，核心价值是**评分覆盖 + 差异化主张 + 可追溯的虚构补全**。改动时守两条底线：不要把仪式（状态机、硬门、canonical）加回来；不要让虚构变得不可追溯（每处虚构必须能进 `_风险与待核实.md`）。

## 开发环境

- Python 3.8+；运行时工具只依赖标准库。
- 能运行 `unittest` 的本地终端。

```bash
python3 -m unittest discover -s tests
python3 -m py_compile tools/prop_tools.py
python3 tools/prop_tools.py --help
```

## 改动归属

| 改动 | 主要位置 |
|:---|:---|
| 流程顺序、Task 输入输出 | `SKILL.md`、`prompts/` |
| 正文写作工艺（开篇/标题/套话/编号/递交禁项）| `references/writing-patterns.md` |
| 一页纸骨架、标型先验、叙事选型 | `references/strategy-patterns.md`；叙事短 guide 在 `narratives.json` |
| 复核判据、反模式、好坏对照 | `references/anti-patterns.md`、`references/contrast-examples.md`（只进复核与复盘）|
| PPT 结构、视觉、证据图红线 | `references/presentation-patterns.md`、`docs/reference/presentation-blueprint.md` |
| 校验器（blueprint / index）| `tools/prop_tools.py`、`tests/` |
| 案例人工事实源 | `casebase/` |
| 宿主注册 | `../.agents/skills/proposal/SKILL.md`（宿主入口，只指向本仓库）|

## 修改流程

1. 先读 `SKILL.md` 和相关参考。
2. 行为变化先补/调测试，尤其证据图红线、索引漏项与虚构登记交叉。
3. 保持轻：不新增 flag / 状态文件 / gate / canonical，除非确有必要并在 PR 说明。
4. 改 CLI 参数、blueprint 字段时，同步更新 `docs/reference/presentation-blueprint.md`。
5. 改用户流程时同步核对 `README.md`。

## 文档与安全

- 示例用占位路径与虚构项目名，不提交真实标书、客户私密材料、底价或未授权案例。
- 客户递交稿禁止 URL、内部 ID、私密原句、策略/模式/工具痕迹（见 writing-patterns 递交稿禁项）。
- `git status` 不应出现 `reports/` 运行产物；运行输出一律不入库。

## 提交前检查

```bash
python3 -m unittest discover -s tests
python3 -m py_compile tools/prop_tools.py
git diff --check
```

提交说明概括行为变化；影响 blueprint schema 或默认流程时单独指出。
