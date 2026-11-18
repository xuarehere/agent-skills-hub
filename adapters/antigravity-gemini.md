# Google Gemini / Antigravity 平台适配指南

Antigravity / Gemini 支持将 Skill 与 Subagent 以 **Plugin** 形式统一装配到 `~/.gemini/config/plugins/<plugin-name>/`（全局跨项目生效）或 `<workspace>/.agents/plugins/<plugin-name>/`（仅单项目生效）。

## 一键安装 / 同步到 Antigravity

```bash
# 从本仓库同步所有技能与子代理到本机 Antigravity 全局插件目录
python tools/sync_skills.py install --target antigravity

# 仅同步指定技能
python tools/sync_skills.py install --target antigravity --name release-material-packager
```

装配完成后，Antigravity 语言服务器会自动发现该插件，并在 Customizations 页面启用对应的 Skill 与 Subagent（下一轮对话立即生效，无需重启 IDE）。

## 从 Antigravity 回收更新回本仓库

当你在 Antigravity 中优化了本地技能或新写了一个全局技能后，执行：

```bash
python tools/sync_skills.py harvest --source antigravity --name <skill-name>
python tools/security_scan.py --root .
```
