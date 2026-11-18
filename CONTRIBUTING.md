# 技能收录、同步与脱敏规范 (Contributing Guide)

本仓库面向 **多智能体生态（Gemini/Antigravity、OpenAI GPT/Codex、Claude Code、Cursor 等）** 统一沉淀可复用技能与子代理。任何新增或回收更新的技能须遵循以下规范。

---

## 1. 标准 Skill 目录契约

每个技能必须位于 `skills/<kebab-case-name>/` 下，并包含明确的输入/输出契约：

```text
skills/<skill-name>/
├── SKILL.md          # [必填] YAML frontmatter (name, description) + 清晰分步 SOP
├── README.md         # [推荐] 面向人类的说明文档：输入契约、输出结构、使用示例
├── scripts/          # [可选] 零个人路径依赖的可执行辅助脚本（Python / Shell）
├── references/       # [可选] 模板、规范与按需阅读的参考手册
└── examples/         # [可选] 脱敏后的标准输入配置示例（JSON / YAML）
```

### Frontmatter 最低要求 (`SKILL.md`)
```yaml
---
name: <skill-name>        # 必须与文件夹名完全一致（小写短横线）
description: >-
  清晰描述该技能解决什么问题以及何时触发（供各智能体自动发现路由）。
---
```

---

## 2. Subagent 角色定义契约

如需配套自主子代理，放置在 `agents/<agent-name>.md`，包含 frontmatter `name` 与 `description`，正文为可直接加载的系统指令。

---

## 3. Public 公开仓库强制脱敏红线

提交或推送前必须通过 `python tools/security_scan.py --root .` 扫描，严禁包含：
1. 任何 API Key、GitHub/CNB Token（`ghp_`、`github_pat_`、`sk-` 等）或私钥内容；
2. 任何真实内网 IP（如 `10.x.x.x`、`192.168.x.x`）、生产域名或真实账号密码；
3. 任何本机绝对路径（如 `C:\Users\<username>\...`、`/Users/<username>/...`），脚本引用一律使用相对路径（如 `./scripts/...`）或环境变量/占位符。

---

## 4. 从不同智能体回收技能的推荐流程

1. 运行 `python tools/sync_skills.py harvest --source <codex|antigravity|claude> --name <skill-name>`；
2. 审阅变更并补全/更新 `README.md` 中的输入与输出说明；
3. 运行 `python tools/security_scan.py --root .` 确保 `0 findings`；
4. 提交并推送至 `main`（重要里程碑打语义化标签如 `v1.1.0`）。
