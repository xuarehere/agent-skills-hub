# Release Material Documentation Templates

Use these standardized templates when consolidating technical docs under `docs/`.

---

## Template 1: `docs/README.md` (Documentation Hub)

```markdown
# <Project Name> · 技术文档总览 (<release_tag>)

本目录为 **<Project Name> (<release_tag>)** 的完整技术白皮书、运维手册与实机图文/视频案例库。

## 1. 系统全局架构
(Insert Mermaid `flowchart TB` linking UI, Backend, Modules, and Storage/Cache)

## 2. 技术文档目录索引
| 序号 | 技术文档 | 对应模块 | 核心涵盖内容 |
| :---: | :--- | :--- | :--- |
| **01** | [01_<mod_a>.md](./01_<mod_a>.md) | ... | ... |
| **02** | [02_<mod_b>.md](./02_<mod_b>.md) | ... | ... |
| **NN** | [NN_architecture_and_ops.md](./NN_architecture_and_ops.md) | 架构与运维 | ... |
| **--** | [demos/README.md](./demos/README.md) | 案例视频与输入库 | ... |

## 3. 版本演进里程碑
| 版本标签 | 发布内容摘要 |
| :---: | :--- |
| `v1.0` | ... |
| `<release_tag>` | ... |
```

---

## Template 2: `docs/0X_<module>.md` (Module Technical Whitepaper)

```markdown
# 模块 X 技术文档：<Module Display Name>

> **模块定位**：一句话概括业务目标、核心能力与实测闭环。

## 1. 业务流程与系统架构
(Insert Mermaid `flowchart` or `sequenceDiagram`)

## 2. 核心技术实现与关键问题治理
- 列出核心算法/交互机制
- 列出实机联调遇到的典型坑点、根因与修复方案（表格形式最佳）

## 3. 边缘/真机实测结果与图文验收
- 实测指标表（100% 源自真实日志/CSV/JSON，杜绝模拟值）
- 2 列 Markdown 表格并排展示关键界面截图 (`![caption](./demos/images/0X_xxx.png)`)
- 链接对应的 H.264 操作录屏 (`./demos/videos/demo_0X_xxx.mp4`)、算法原始成果视频与真实报表 (`./demos/data/...`)

## 4. 核心 API 与代码索引
| 接口 / 代码位置 | 功能说明 |
| :--- | :--- |
| `POST /api/...` | ... |
| 源码路径 | [file.py](../path/to/file.py) |
```

---

## Template 3: `docs/demos/README.md` (Media & Reproducible Inputs Catalog)

Include all 4 sections with exact `ffprobe` metadata and MD5 checksums:
1. **浏览器端到端实机操作录屏 (`videos/demo_*.mp4`)** — table with module, duration, MB, workflow covered.
2. **实测算法原始成果视频 (`videos/case_*.mp4`)** — table with codec (`h264 yuv420p`), resolution, MB, description.
3. **高清实机验收图集 (`images/`)** — grouped by module.
4. **真实结构化报表 (`data/`) 与去重测试输入原始集 (`inputs/`)** — exact MD5 checksums + 1-step Web/CLI reproduction instructions.

---

## Template 4: `.gitignore` Narrow Allowlist Pattern

Keep global ignores intact (`*.mp4`, `*.avi`) and allowlist ONLY the curated release demo directories:

```gitignore
*.mp4
!docs/demos/videos/*.mp4
!docs/demos/inputs/*.mp4
!docs/demos/inputs/*.avi
```
