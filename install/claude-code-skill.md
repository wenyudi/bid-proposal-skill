# 安装到 Claude Code

仓库是 skill 的唯一事实来源。宿主入口 `~/.agents/skills/proposal/SKILL.md` 只指向本仓库，不复制完整定义。

注册步骤：

1. clone 本仓库到本地（如 `~/Code/proposal`）。
2. 在宿主 skills 目录建入口 `proposal/SKILL.md`，指向仓库绝对路径（参见 `../.agents/skills/proposal/SKILL.md` 示例：读取仓库的 `SKILL.md` 并执行 v4 流程）。
3. 新开会话输入 `/proposal <标书或brief路径> [素材路径]`。

用法与产物见 [README](../README.md)。
