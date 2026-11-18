#!/usr/bin/env python3
"""Pre-push security & PII scanner for public agent-skills-hub repositories.

Blocks accidental commits of:
- API keys / GitHub PATs / OpenAI / Anthropic / private key headers
- Private LAN IPv4 addresses (10.x.x.x, 192.168.x.x, 172.16-31.x.x)
- Machine-local absolute user paths (C:\\Users\\<user>\\..., /Users/<user>/..., /home/<user>/...)
- Hardcoded common test passwords
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}
TEXT_EXTS = {
    ".md", ".py", ".json", ".yaml", ".yml", ".toml", ".txt", ".sh", ".ps1",
    ".cmd", ".bat", ".js", ".ts", ".css", ".html", ".gitignore", "",
}

RULES: list[tuple[str, re.Pattern[str]]] = [
    ("GitHub/OAuth Token", re.compile(r"\b(ghp_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|gho_[A-Za-z0-9_]{20,})\b")),
    ("OpenAI/Anthropic Key", re.compile(r"\b(sk-[A-Za-z0-9]{20,}|sk-ant-[A-Za-z0-9_-]{20,})\b")),
    ("Private Key Header", re.compile(r"-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----")),
    ("Private LAN IPv4", re.compile(r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b")),
    ("Hardcoded Windows User Path", re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+(?!<)[A-Za-z0-9._-]+[\\/]", re.IGNORECASE)),
    ("Hardcoded macOS/Linux Home Path", re.compile(r"(?:/Users/|/home/)(?!<)[A-Za-z0-9._-]+/")),
    ("Hardcoded Common Password", re.compile(r"(?:password|passwd|pwd)\s*[:=]\s*[\"']?(?:admin123|123456|root123|password123)[\"']?", re.IGNORECASE)),
]


def scan_file(path: Path, root: Path) -> list[str]:
    findings: list[str] = []
    # Skip scanning this scanner script's own regex definitions
    if path.resolve() == Path(__file__).resolve():
        return findings
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return findings

    rel = str(path.relative_to(root))
    for lineno, line in enumerate(text.splitlines(), start=1):
        for rule_name, pattern in RULES:
            m = pattern.search(line)
            if m:
                snippet = m.group(0)
                if len(snippet) > 36:
                    snippet = snippet[:16] + "..." + snippet[-8:]
                findings.append(f"[{rule_name}] {rel}:{lineno} -> {snippet}")
    return findings


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan public skills repo for secrets, private IPs, and local paths.")
    parser.add_argument("--root", default=".", help="Repository root directory to scan")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    all_findings: list[str] = []
    files_scanned = 0

    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() not in TEXT_EXTS:
            continue
        files_scanned += 1
        all_findings.extend(scan_file(p, root))

    print(f"[SECURITY SCAN] root={root} files_scanned={files_scanned} findings={len(all_findings)}")
    if all_findings:
        for item in all_findings:
            print(f"  FAIL: {item}")
        sys.exit(1)
    print("[PASS] Public repository security & sanitization check passed (0 findings).")


if __name__ == "__main__":
    main()
