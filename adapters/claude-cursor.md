# Claude Code & Cursor 平台适配指南

Claude Code 默认发现 `~/.claude/skills/<skill-name>/SKILL.md` 与 `~/.claude/agents/<agent-name>.md`（或项目级 `.claude/`）；Cursor 可直接引用 `skills/<skill-name>/SKILL.md` 作为项目规则或工作流参考。

## 一键安装 / 同步到 Claude Code

```bash
# 同步全部技能与子代理到本机 ~/.claude/
python tools/sync_skills.py install --target claude
```

## 从 Claude Code 回收技能到本仓库

```bash
python tools/sync_skills.py harvest --source claude --name <skill-name>
python tools/security_scan.py --root .
git add . && git commit -m "feat(skills): sync <skill-name> from claude" && git push origin main
```
