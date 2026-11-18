---
name: release-material-packager
description: >-
  Use this skill when the user wants to consolidate, document, package, and tag a
  completed software/AI/edge release — including writing illustrated technical
  whitepapers across multiple modules, archiving deduplicated test input media and
  H.264 case-study videos, recording live browser walkthrough demos via Playwright
  and ffmpeg, verifying Markdown links and video codecs, creating annotated Git
  tags, and syncing to one or more Git remotes and deployment hosts.
---

# Release Material Packager (标准交付材料固化 SOP)

Use this skill to turn a completed development milestone into a self-contained,
reproducible, illustrated engineering delivery bundle under `docs/` and publish
it as a verified, tagged Git release.

---

## Input & Output Contract

### Required / Optional Inputs
- **Workspace root** (`workspace`): Git repository root (default: active workspace).
- **Modules to document** (`modules`): List of completed features/modules to cover (include any earlier completed modules that still lack formal documentation).
- **Target release tag** (`release_tag`): Semantic version tag (e.g., `v1.3`). Inspect `git tag -l` first to follow existing naming conventions.
- **Media & data sources** (optional): Local or SSH paths containing raw test inputs, H.264 result videos, screenshots, and real CSV/JSON telemetry.
- **Live demo URL** (optional): Web portal URL + test credentials if interactive walkthrough screencasts should be recorded.
- **Sync targets** (optional): Git remotes (check `git remote -v`) and any target edge/deployment host.

See [examples/release_manifest.example.json](./examples/release_manifest.example.json) for a concrete structured input schema.

### Standardized Output Deliverables
1. `docs/README.md` — Documentation hub, Mermaid architecture diagram, module index, release timeline.
2. `docs/01_<module>.md` ... `docs/<NN>_architecture_and_ops.md` — Illustrated technical whitepapers per module + operations guide (templates in [references/doc_templates.md](./references/doc_templates.md)).
3. `docs/demos/README.md` — Master catalog of all videos, screenshots, real data reports, and MD5-deduplicated test inputs with reproduction instructions.
4. `docs/demos/images/` — Semantically named, visually verified screenshots (`01_*`, `02_*`, `03_*`).
5. `docs/demos/videos/` — Browser-native `h264 (yuv420p) 1280x720` case-study videos & live recorded walkthrough demos (each `< 50 MB` for native Git hosting).
6. `docs/demos/data/` — Real structured telemetry/metrics samples (JSON, UTF-8-SIG CSV).
7. `docs/demos/inputs/` — MD5-deduplicated raw test input media so anyone checking out the tag can reproduce results 1:1.
8. Updated root `README.md` (docs navigation block) and `.gitignore` (narrow allowlist exceptions `!docs/demos/videos/*.mp4`, `!docs/demos/inputs/*`).
9. Annotated Git tag pushed to all configured remotes (and synced to deployment host if applicable).

---

## 6-Stage Execution Procedure

### Stage 1: Inventory & Deduplicate Source Materials
1. Inspect existing `git tag -l`, `git remote -v`, `.gitignore`, and existing `docs/`.
2. Inventory screenshots, algorithm output videos, real telemetry/CSV outputs, and **raw test input media** (both built-in samples and custom uploaded test clips).
3. Compute MD5 hashes on candidate input files before copying so identical files are never stored twice.
4. Check `.gitignore` for broad ignores (`*.mp4`, `*.avi`) and prepare narrow allowlist rules (`!docs/demos/videos/*.mp4`, `!docs/demos/inputs/*.mp4`, `!docs/demos/inputs/*.avi`).

### Stage 2: Archive Assets & Record Live Interactive Demos
1. Create `docs/demos/{images,videos,data,inputs}`.
2. Copy curated screenshots with numeric module prefixes (`01_...`, `02_...`, `03_...`).
3. Archive algorithm output videos (transcode any non-H.264/`mpeg4` clip to `libx264 yuv420p +faststart`; on RK3588 hosts force `-hwaccel none -c:v mpeg4` on decode to avoid `mpeg4_rkmpp` deadlock).
4. Archive real structured data samples (`telemetry.json`, `tracks.csv`, `counts.csv`) and deduplicated raw test inputs into `docs/demos/inputs/`.
5. If a live Web UI is available and walkthrough recordings are requested, run [scripts/record_portal_demo.py](./scripts/record_portal_demo.py) with a scenario JSON config to capture crisp `1280x720 H.264` demos and extract midpoint keyframes.
6. Visually inspect every extracted midpoint keyframe and key screenshot to guarantee zero black frames, zero stale UI labels, and zero layout glitches.

### Stage 3: Author Illustrated Technical Whitepapers
Follow the templates in [references/doc_templates.md](./references/doc_templates.md):
- Write one focused whitepaper per completed module (`docs/01_*.md`, `docs/02_*.md`, ...) covering: architecture (Mermaid diagram), key engineering challenges & fixes, real measured metrics (zero synthetic numbers), embedded relative screenshots (`./demos/images/...`), links to demo videos & real data samples, and API/code index.
- Write an infrastructure & operations guide (`docs/<NN>_architecture_and_ops.md`) documenting deployment, media pipelines, and ops commands.
- Write `docs/README.md`, `docs/demos/README.md` (with exact `ffprobe` specs + MD5 table + copy-paste reproduction instructions), and add a concise navigation section to root `README.md`.

### Stage 4: Run Automated Quality Gate
Execute the bundled validator script (relative to this skill directory) before any commit:

```bash
python ./scripts/verify_release_bundle.py --root "<workspace>"
```

**Do NOT proceed to Stage 5 until ALL checks pass:**
- `broken_links == 0` across root `README.md` and every Markdown file under `docs/`.
- Every `.mp4` in `docs/demos/videos/` is verified `codec=h264`, `pix_fmt=yuv420p`, `size_mb < 50.0`.
- Zero MD5-duplicate files inside `docs/demos/inputs/`.
- No unintended large binary (`> 50 MB`) staged for Git push.

### Stage 5: Commit, Annotated Tag & Multi-Remote Sync
1. Update `.gitignore` with narrow allowlist rules for `docs/demos/videos/` and `docs/demos/inputs/`.
2. Stage only intentional release files (`git add .gitignore README.md docs/`), inspect `git status -s`, and commit with a clear conventional commit message.
3. Create an annotated tag with rich release notes:
   `git tag -a <tag> -m "Release <tag>: ..."`
4. Push branch and tag to every configured remote.
5. If a target deployment host is configured, pull the commit and fetch tags there and verify service health.

### Stage 6: Final Handoff Report
Provide a concise summary linking directly to:
- `README.md`, `docs/README.md`, each module whitepaper, and `docs/demos/README.md`
- Recorded demo videos, algorithm case videos, and archived reproducible input videos (with sizes/specs)
- Commit hash, Git tag, and sync confirmation across all remotes & deployment hosts.
