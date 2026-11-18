#!/usr/bin/env python3
"""Cross-agent skill & subagent sync CLI for agent-skills-hub.

Supports:
  - list:    Show all registered skills and local install status across Antigravity, Codex/GPT, Claude.
  - install: Assemble & install skills/agents from this hub to local agent platforms.
  - harvest: Import a skill created/updated in Antigravity, Codex/GPT, or Claude back into this hub,
             update registry.json, and run security_scan.py automatically.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

HUB_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = HUB_ROOT / "registry.json"
HOME = Path.home()

PLATFORM_DIRS = {
    "antigravity_plugins": HOME / ".gemini" / "config" / "plugins",
    "antigravity_skills": HOME / ".gemini" / "config" / "skills",
    "codex_skills": HOME / ".codex" / "skills",
    "claude_skills": HOME / ".claude" / "skills",
    "claude_agents": HOME / ".claude" / "agents",
}

ORIGIN_MAP = {
    "antigravity": "gemini-antigravity",
    "codex": "openai-codex",
    "claude": "claude-code",
}


def load_registry() -> dict[str, Any]:
    if not REGISTRY_PATH.is_file():
        return {"schema_version": 1, "repository": "", "updated_at": "", "skills": []}
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def save_registry(reg: dict[str, Any]) -> None:
    reg["updated_at"] = dt.date.today().isoformat()
    REGISTRY_PATH.write_text(json.dumps(reg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_frontmatter(skill_md: Path) -> tuple[str, str]:
    text = skill_md.read_text(encoding="utf-8")
    name = skill_md.parent.name
    desc = ""
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if m:
        block = m.group(1)
        mn = re.search(r"^name:\s*(.+)$", block, re.MULTILINE)
        if mn:
            name = mn.group(1).strip().strip("'\"")
        md = re.search(r"^description:\s*(?:>-\s*\n|\|\s*\n)?(.+?)(?:\n[a-zA-Z0-9_-]+:|\Z)", block, re.MULTILINE | re.DOTALL)
        if md:
            desc = " ".join(line.strip() for line in md.group(1).splitlines()).strip().strip("'\"")
    return name, desc


def copy_tree_clean(src: Path, dst: Path, dry_run: bool = False) -> None:
    if dry_run:
        print(f"  [DRY-RUN] copy {src} -> {dst}")
        return
    if dst.exists():
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))


def install_antigravity(entry: dict[str, Any], dry_run: bool = False) -> None:
    name = entry["name"]
    skill_src = HUB_ROOT / entry["skill_path"]
    plugin_dir = PLATFORM_DIRS["antigravity_plugins"] / name

    if dry_run:
        print(f"  [DRY-RUN] assemble Antigravity plugin -> {plugin_dir}")
        return

    plugin_dir.mkdir(parents=True, exist_ok=True)
    # 1. plugin.json
    manifest_rel = entry.get("plugin_manifest")
    manifest_src = (HUB_ROOT / manifest_rel) if manifest_rel else None
    if manifest_src and manifest_src.is_file():
        shutil.copy2(manifest_src, plugin_dir / "plugin.json")
    else:
        fallback = {
            "name": name,
            "displayName": entry.get("display_name", name),
            "version": entry.get("version", "1.0.0"),
            "description": entry.get("summary", ""),
        }
        (plugin_dir / "plugin.json").write_text(json.dumps(fallback, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 2. README.md
    if (skill_src / "README.md").is_file():
        shutil.copy2(skill_src / "README.md", plugin_dir / "README.md")

    # 3. skills/<name>/
    copy_tree_clean(skill_src, plugin_dir / "skills" / name, dry_run=False)

    # 4. agents/*.md
    agents = entry.get("agents") or []
    if agents:
        agents_dst = plugin_dir / "agents"
        agents_dst.mkdir(parents=True, exist_ok=True)
        for rel_agent in agents:
            src_agent = HUB_ROOT / rel_agent
            if src_agent.is_file():
                shutil.copy2(src_agent, agents_dst / src_agent.name)

    print(f"  [OK] Antigravity plugin installed: {plugin_dir}")


def install_codex(entry: dict[str, Any], dry_run: bool = False) -> None:
    name = entry["name"]
    skill_src = HUB_ROOT / entry["skill_path"]
    dst = PLATFORM_DIRS["codex_skills"] / name
    copy_tree_clean(skill_src, dst, dry_run=dry_run)
    if not dry_run:
        print(f"  [OK] Codex/GPT skill installed: {dst}")


def install_claude(entry: dict[str, Any], dry_run: bool = False) -> None:
    name = entry["name"]
    skill_src = HUB_ROOT / entry["skill_path"]
    dst = PLATFORM_DIRS["claude_skills"] / name
    copy_tree_clean(skill_src, dst, dry_run=dry_run)
    for rel_agent in entry.get("agents") or []:
        src_agent = HUB_ROOT / rel_agent
        if src_agent.is_file():
            agent_dst = PLATFORM_DIRS["claude_agents"] / src_agent.name
            if dry_run:
                print(f"  [DRY-RUN] copy {src_agent} -> {agent_dst}")
            else:
                agent_dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_agent, agent_dst)
    if not dry_run:
        print(f"  [OK] Claude Code skill/agents installed: {dst}")


def cmd_list(_args: argparse.Namespace) -> None:
    reg = load_registry()
    skills = reg.get("skills", [])
    print(f"Agent Skills Hub Registry ({len(skills)} skill(s), updated {reg.get('updated_at', '-')}):\n")
    for s in skills:
        name = s["name"]
        agy_ok = (PLATFORM_DIRS["antigravity_plugins"] / name / "plugin.json").is_file()
        codex_ok = (PLATFORM_DIRS["codex_skills"] / name / "SKILL.md").is_file()
        claude_ok = (PLATFORM_DIRS["claude_skills"] / name / "SKILL.md").is_file()
        print(
            f"  - {name} (v{s.get('version', '1.0.0')}) | origin={s.get('origin', 'custom')} "
            f"| installed: [antigravity={'Y' if agy_ok else 'N'}, codex={'Y' if codex_ok else 'N'}, claude={'Y' if claude_ok else 'N'}]"
        )
        print(f"    {s.get('summary', '')}")


def cmd_install(args: argparse.Namespace) -> None:
    reg = load_registry()
    entries = reg.get("skills", [])
    if args.name:
        entries = [e for e in entries if e["name"] == args.name]
        if not entries:
            raise SystemExit(f"Skill not found in registry.json: {args.name}")

    targets = ["antigravity", "codex", "claude"] if args.target == "all" else [args.target]
    for entry in entries:
        print(f"Installing `{entry['name']}`...")
        for t in targets:
            if t == "antigravity":
                install_antigravity(entry, dry_run=args.dry_run)
            elif t == "codex":
                if args.target == "all" and not PLATFORM_DIRS["codex_skills"].parent.exists():
                    continue
                install_codex(entry, dry_run=args.dry_run)
            elif t == "claude":
                if args.target == "all" and not PLATFORM_DIRS["claude_skills"].parent.exists():
                    continue
                install_claude(entry, dry_run=args.dry_run)


def cmd_harvest(args: argparse.Namespace) -> None:
    name = args.name
    src_candidates: list[Path] = []
    if args.source == "codex":
        src_candidates.append(PLATFORM_DIRS["codex_skills"] / name)
    elif args.source == "claude":
        src_candidates.append(PLATFORM_DIRS["claude_skills"] / name)
    elif args.source == "antigravity":
        src_candidates.append(PLATFORM_DIRS["antigravity_plugins"] / name / "skills" / name)
        src_candidates.append(PLATFORM_DIRS["antigravity_skills"] / name)

    src_dir = next((p for p in src_candidates if (p / "SKILL.md").is_file()), None)
    if not src_dir:
        raise SystemExit(f"Could not find SKILL.md for `{name}` in source `{args.source}` (checked {src_candidates})")

    dst_dir = HUB_ROOT / "skills" / name
    copy_tree_clean(src_dir, dst_dir, dry_run=False)
    parsed_name, parsed_desc = parse_frontmatter(dst_dir / "SKILL.md")

    # Update registry.json
    reg = load_registry()
    existing = next((s for s in reg["skills"] if s["name"] == name), None)
    if existing:
        existing["summary"] = parsed_desc or existing.get("summary", "")
        existing["origin"] = ORIGIN_MAP.get(args.source, args.source)
    else:
        reg["skills"].append(
            {
                "name": parsed_name or name,
                "display_name": name.replace("-", " ").title(),
                "version": "1.0.0",
                "origin": ORIGIN_MAP.get(args.source, args.source),
                "compatible_platforms": ["antigravity", "gemini", "codex", "gpt", "claude-code", "cursor"],
                "skill_path": f"skills/{name}",
                "agents": [],
                "tags": [args.source],
                "summary": parsed_desc,
            }
        )
    save_registry(reg)
    print(f"[OK] Harvested `{name}` from `{args.source}` into {dst_dir} and updated registry.json.")

    # Automatically run public security scan
    scanner = HUB_ROOT / "tools" / "security_scan.py"
    if scanner.is_file():
        subprocess.check_call([sys.executable, str(scanner), "--root", str(HUB_ROOT)])


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync skills & subagents across AI coding agents.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List registered skills and local install status")

    p_inst = sub.add_parser("install", help="Install skills from hub into local agent platforms")
    p_inst.add_argument("--target", choices=["antigravity", "codex", "claude", "all"], required=True)
    p_inst.add_argument("--name", default="", help="Optional single skill name")
    p_inst.add_argument("--dry-run", action="store_true", help="Preview actions without copying")

    p_harv = sub.add_parser("harvest", help="Import a local skill from an agent platform back into this hub")
    p_harv.add_argument("--source", choices=["antigravity", "codex", "claude"], required=True)
    p_harv.add_argument("--name", required=True, help="Skill folder name to harvest")

    args = parser.parse_args()
    if args.command == "list":
        cmd_list(args)
    elif args.command == "install":
        cmd_install(args)
    elif args.command == "harvest":
        cmd_harvest(args)


if __name__ == "__main__":
    main()
