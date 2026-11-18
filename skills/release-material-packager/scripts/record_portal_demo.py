#!/usr/bin/env python3
"""Reusable declarative Playwright + ffmpeg 1280x720 H.264 Web demo recorder.

Reads a JSON config describing login credentials and one or more recording
scenarios (click, fill, wait, scroll, play_video, screenshot), records crisp
WebM captures via Playwright, transcodes them to browser/PPT-ready H.264 MP4
(+faststart), and extracts a midpoint JPEG keyframe for mandatory visual QA.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright


def transcode_to_h264(
    src_webm: Path,
    dst_mp4: Path,
    keyframe_jpg: Path | None,
    width: int = 1280,
    height: int = 720,
    crf: int = 23,
) -> dict[str, Any]:
    dst_mp4.parent.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src_webm),
            "-vf",
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=#070c17",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            str(crf),
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(dst_mp4),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    dur_str = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(dst_mp4),
        ],
        text=True,
    ).strip()
    dur = float(dur_str or 0.0)
    if keyframe_jpg is not None:
        keyframe_jpg.parent.mkdir(parents=True, exist_ok=True)
        mid = max(0.5, dur * 0.55)
        subprocess.check_call(
            [
                "ffmpeg",
                "-y",
                "-ss",
                f"{mid:.1f}",
                "-i",
                str(dst_mp4),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                str(keyframe_jpg),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    return {
        "output": str(dst_mp4),
        "duration_s": round(dur, 1),
        "size_mb": round(dst_mp4.stat().st_size / (1024 * 1024), 2),
        "keyframe": str(keyframe_jpg) if keyframe_jpg else None,
    }


def perform_login(page, base_url: str, login_cfg: dict[str, Any] | None) -> None:
    page.goto(base_url, wait_until="networkidle", timeout=30000)
    if not login_cfg:
        page.wait_for_timeout(1000)
        return
    u_sel = login_cfg.get("username_selector", "#username, #login-username, input[name='username']")
    p_sel = login_cfg.get("password_selector", "#password, #login-password, input[name='password']")
    s_sel = login_cfg.get("submit_selector", "button[type='submit'], #login-btn")
    if page.locator(u_sel).count() > 0:
        page.locator(u_sel).first.fill(str(login_cfg["username"]))
        page.locator(p_sel).first.fill(str(login_cfg["password"]))
        page.locator(s_sel).first.click()
        page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1200)


def execute_steps(page, steps: list[dict[str, Any]]) -> None:
    for step in steps:
        action = step.get("action")
        if action == "click":
            loc = page.locator(step["selector"]).nth(int(step.get("nth", 0)))
            if loc.is_visible():
                loc.click()
        elif action == "fill":
            loc = page.locator(step["selector"]).first
            if loc.count() > 0:
                loc.fill(str(step["value"]))
        elif action == "wait":
            page.wait_for_timeout(int(step.get("ms", 1000)))
        elif action == "scroll":
            top = int(step.get("top", 0))
            page.evaluate(f"window.scrollTo({{top: {top}, behavior: 'smooth'}})")
        elif action == "play_video":
            vid_sel = json.dumps(step["selector"])
            start_s = float(step.get("start_sec", 0.0))
            page.evaluate(
                f"""() => {{
                    const v = document.querySelector({vid_sel});
                    if (v && v.src) {{ v.muted = true; v.currentTime = {start_s}; v.play().catch(()=>{{}}); }}
                }}"""
            )
        elif action == "screenshot":
            out = Path(step["path"])
            out.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(out), full_page=bool(step.get("full_page", True)))
        else:
            raise ValueError(f"Unsupported recording action: {action}")
        if step.get("after_ms"):
            page.wait_for_timeout(int(step["after_ms"]))


def main() -> None:
    parser = argparse.ArgumentParser(description="Record declarative Playwright H.264 portal demos.")
    parser.add_argument("--config", required=True, help="Path to JSON recording config")
    args = parser.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    base_url = cfg["base_url"]
    login_cfg = cfg.get("login")
    vp = cfg.get("viewport", {"width": 1280, "height": 720})
    w, h = int(vp["width"]), int(vp["height"])

    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            for sc in cfg.get("scenarios", []):
                tmp_dir = Path(tempfile.mkdtemp(prefix=f"rec_{sc['name']}_"))
                try:
                    ctx = browser.new_context(
                        viewport={"width": w, "height": h},
                        record_video_dir=str(tmp_dir),
                        record_video_size={"width": w, "height": h},
                    )
                    page = ctx.new_page()
                    perform_login(page, base_url, login_cfg)
                    execute_steps(page, sc.get("steps", []))
                    webm_path = Path(page.video.path())
                    ctx.close()

                    dst_mp4 = Path(sc["output_mp4"])
                    kf = Path(sc["keyframe_jpg"]) if sc.get("keyframe_jpg") else None
                    info = transcode_to_h264(webm_path, dst_mp4, kf, width=w, height=h)
                    print(f"[OK] {sc['name']} -> {info}")
                    results.append(info)
                finally:
                    shutil.rmtree(tmp_dir, ignore_errors=True)
        finally:
            browser.close()

    print(f"Completed {len(results)} recording(s).")


if __name__ == "__main__":
    main()
