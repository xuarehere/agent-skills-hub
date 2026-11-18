# OpenAI GPT / Codex 平台适配指南

OpenAI Codex（及支持标准 `SKILL.md` 的 GPT 编程智能体）默认扫描 `~/.codex/skills/<skill-name>/SKILL.md`（或工作区 `.agents/skills/`）。

## 一键安装 / 同步到 Codex / GPT

```bash
# 同步全部技能到本机 ~/.codex/skills/
python tools/sync_skills.py install --target codex

# 仅同步单个技能
python tools/sync_skills.py install --target codex --name release-material-packager
```

## 从 Codex / GPT 回收新技能到本仓库

当你在 GPT / Codex 中新沉淀或迭代了某项技能时，只需一条命令即可同步回 `agent-skills-hub` 并自动登记到 `registry.json`（来源自动标记为 `openai-codex`）：

```bash
python tools/sync_skills.py harvest --source codex --name <skill-name>
python tools/security_scan.py --root .
git add . && git commit -m "feat(skills): sync <skill-name> from codex" && git push origin main
```
