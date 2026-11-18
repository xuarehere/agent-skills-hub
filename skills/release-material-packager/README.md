# Release Material Packager Skill

端到端「研发里程碑交付材料固化」通用技能包，适用于软件工程、AI 视觉/多模态系统与边缘计算项目的版本验收与归档。

## 输入契约（Inputs）

| 输入项 | 必填 | 示例 | 说明 |
| :--- | :---: | :--- | :--- |
| `workspace` | ✅ | `/path/to/your-repo` | 目标 Git 项目根目录 |
| `modules` | ✅ | `["模块一", "模块二", "模块三"]` | 需要补齐或整理文档的已完成模块列表 |
| `release_tag` | ✅ | `v1.3` | 本次固化的语义化版本标签 |
| `portal_url` | ⬜ | `http://<portal-host>:8000` | 若需自动录制 Web 交互操作视频则提供 |
| `media_sources` | ⬜ | 本地路径或 SSH 远端路径 | 原始测试输入、算法输出视频与真实报表来源 |
| `git_remotes` | ⬜ | `["origin"]` 或双远端列表 | 需同步推送代码与标签的远程仓库 |

完整结构化配置示例见 [examples/release_manifest.example.json](./examples/release_manifest.example.json)。

## 输出契约（Outputs）

- `docs/README.md`：总览架构图（Mermaid）、模块白皮书导航与版本里程碑
- `docs/01_<module>.md` ... `docs/<NN>_architecture_and_ops.md`：各模块图文技术白皮书与运维手册
- `docs/demos/README.md`：全部录屏、算法成果视频、图集、真实数据样本与去重输入源清单（附 MD5 与复现指南）
- `docs/demos/{images,videos,data,inputs}/`：规范归档的媒体与数据资产（所有视频 `h264 yuv420p` 且 `< 50 MB`）
- 根 `README.md` 导航入口 + `.gitignore` 精准放行规则 + Annotated Git Tag 推送结果

## 配套可执行脚本

```bash
# 1. 一键校验任意仓库的 docs/ 交付包（断链 + H.264 编码 + MD5 去重 + 体积门禁）
python scripts/verify_release_bundle.py --root <workspace>

# 2. 声明式录制 Web 端到端交互操作视频并自动转为 1280x720 H.264
python scripts/record_portal_demo.py --config <scenario.json>
```
