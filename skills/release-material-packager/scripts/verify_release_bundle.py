#!/usr/bin/env python3
"""Automated quality gate for Release Material Packager bundles.

Validates:
1. All relative Markdown links in root README.md and docs/**/*.md (0 broken links).
2. All MP4 videos in docs/demos/videos/ are browser-compatible H.264 (yuv420p) and < 50 MB.
3. All archived input files in docs/demos/inputs/ have zero MD5 duplicates and are < 50 MB.
4. Optional JSON report output (--json-out) for CI or handoff documentation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


def file_md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def probe_video(path: Path) -> dict[str, Any]:
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_name,pix_fmt,width,height,r_frame_rate",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ],
        text=True,
    )
    data = json.loads(out)
    stream = data["streams"][0]
    dur = round(float(data.get("format", {}).get("duration") or 0.0), 1)
    size_mb = round(path.stat().st_size / (1024 * 1024), 2)
    return {
        "name": path.name,
        "codec": stream.get("codec_name", ""),
        "pix_fmt": stream.get("pix_fmt", ""),
        "width": int(stream.get("width", 0)),
        "height": int(stream.get("height", 0)),
        "r_frame_rate": stream.get("r_frame_rate", ""),
        "duration_s": dur,
        "size_mb": size_mb,
    }


def check_markdown_links(root: Path, docs_dir: Path) -> tuple[int, int, list[dict[str, str]]]:
    md_files: list[Path] = []
    if (root / "README.md").is_file():
        md_files.append(root / "README.md")
    if docs_dir.is_dir():
        md_files.extend(sorted(docs_dir.rglob("*.md")))

    checked = 0
    broken: list[dict[str, str]] = []
    for md in md_files:
        text = md.read_text(encoding="utf-8")
        for match in re.finditer(r"!?\[[^\]]*\]\(([^)]+)\)", text):
            href = match.group(1).strip()
            if href.startswith(("http://", "https://", "#", "mailto:", "file://", "customization://")):
                continue
            clean_href = href.split("#", 1)[0].split("?", 1)[0]
            if not clean_href:
                continue
            target = (md.parent / clean_href).resolve()
            checked += 1
            if not target.exists():
                broken.append(
                    {
                        "source": str(md.relative_to(root)),
                        "href": href,
                    }
                )
    return len(md_files), checked, broken


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a docs/ release material bundle.")
    parser.add_argument("--root", required=True, help="Repository root directory")
    parser.add_argument("--docs-subpath", default="docs", help="Relative docs directory (default: docs)")
    parser.add_argument("--max-file-mb", type=float, default=49.0, help="Max allowed binary size in MB")
    parser.add_argument("--json-out", default="", help="Optional path to write JSON summary report")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    docs_dir = root / args.docs_subpath
    errors: list[str] = []

    # 1. Markdown link integrity
    md_count, link_count, broken = check_markdown_links(root, docs_dir)
    print(f"[1/3] Markdown check: files={md_count}, links={link_count}, broken={len(broken)}")
    for b in broken:
        errors.append(f"Broken link in {b['source']} -> {b['href']}")

    # 2. Output / demo H.264 video verification
    videos_dir = docs_dir / "demos" / "videos"
    video_reports: list[dict[str, Any]] = []
    if videos_dir.is_dir():
        for v in sorted(videos_dir.glob("*.mp4")):
            info = probe_video(v)
            video_reports.append(info)
            ok = (
                info["codec"] == "h264"
                and info["pix_fmt"] == "yuv420p"
                and info["size_mb"] <= args.max_file_mb
            )
            status = "OK" if ok else "FAIL"
            print(
                f"  [VIDEO {status}] {info['name']}: {info['codec']} {info['pix_fmt']} "
                f"{info['width']}x{info['height']} {info['duration_s']}s {info['size_mb']}MB"
            )
            if info["codec"] != "h264" or info["pix_fmt"] != "yuv420p":
                errors.append(f"Video {info['name']} is not browser-safe h264/yuv420p ({info['codec']}/{info['pix_fmt']})")
            if info["size_mb"] > args.max_file_mb:
                errors.append(f"Video {info['name']} exceeds {args.max_file_mb}MB ({info['size_mb']}MB)")
    print(f"[2/3] Output videos checked: {len(video_reports)}")

    # 3. Archived test inputs MD5 deduplication & size guard
    inputs_dir = docs_dir / "demos" / "inputs"
    input_reports: list[dict[str, Any]] = []
    seen_md5: dict[str, str] = {}
    if inputs_dir.is_dir():
        for p in sorted(f for f in inputs_dir.iterdir() if f.is_file()):
            digest = file_md5(p)
            size_mb = round(p.stat().st_size / (1024 * 1024), 2)
            rec = {"name": p.name, "size_mb": size_mb, "md5": digest}
            if p.suffix.lower() in {".mp4", ".avi", ".mov", ".mkv", ".webm"}:
                try:
                    rec.update(probe_video(p))
                except Exception:
                    pass
            input_reports.append(rec)
            print(f"  [INPUT] {p.name}: {size_mb}MB md5={digest}")
            if digest in seen_md5:
                errors.append(f"Duplicate input detected by MD5: {p.name} == {seen_md5[digest]} ({digest})")
            else:
                seen_md5[digest] = p.name
            if size_mb > args.max_file_mb:
                errors.append(f"Input {p.name} exceeds {args.max_file_mb}MB ({size_mb}MB)")
    print(f"[3/3] Reproducible inputs checked: {len(input_reports)}")

    report = {
        "root": str(root),
        "passed": len(errors) == 0,
        "markdown_files": md_count,
        "links_checked": link_count,
        "broken_links": broken,
        "videos": video_reports,
        "inputs": input_reports,
        "errors": errors,
    }
    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if errors:
        print("\n[FAIL] Release bundle validation failed:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print("\n[PASS] ALL RELEASE MATERIAL QUALITY GATES PASSED!")


if __name__ == "__main__":
    main()
