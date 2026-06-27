"""Utility functions for the Streamlit GUI — no Streamlit imports."""

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STYLES = [
    "小A", "经典红", "抖音风", "圆角小A", "彩虹", "星战光剑红", "星战光剑蓝",
    "火焰", "海洋", "红橙", "红心", "白绿", "足球", "浅黄", "粉红", "紫粉",
    "黄橙", "冒险时光", "橙黄", "青绿", "紫色", "橙红", "蓝色", "游戏红", "吃豆人蓝",
]
DEFAULT_STYLE = "小A"
TEMP_DIR = Path(tempfile.gettempdir()) / "deveco" / "gui"
SCRUBBER_DIR = PROJECT_ROOT / "scrubbers" / "gif"
SCRUBBER_DEFAULT = str(PROJECT_ROOT / "scrubber_final.gif")


def list_scrubbers() -> list[tuple[str, str]]:
    """Return sorted list of (display_name, file_path)."""
    gifs = sorted(SCRUBBER_DIR.glob("*.gif"))
    items = []
    for g in gifs:
        name = g.stem.replace("-", " ").replace("_", " ").title()
        items.append((name, str(g)))
    return items

ETA_COEFF = {
    ("funasr", False): 200 / 472,
    ("funasr", True): 232 / 472,
    ("whisper", False): (273 + 113) / 472,
    ("whisper", True): (273 + 145) / 472,
}
WHISPER_MODELS = ["large-v3-turbo", "large-v3", "medium", "small", "base", "tiny"]


def get_video_duration(path: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True, timeout=30,
    )
    return float(r.stdout.strip())


def estimate_eta(duration: float, engine: str, use_gif: bool) -> str:
    coeff = ETA_COEFF.get((engine, use_gif), 0.5)
    sec = duration * coeff
    return f"约 {sec:.0f} 秒" if sec < 60 else f"约 {sec / 60:.1f} 分钟"


def run_cli_streaming(args: list[str], log_ph):
    cmd = [sys.executable, "-m", "vpbar.cli"] + args
    proc = subprocess.Popen(
        cmd, cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    lines = []
    for line in iter(proc.stdout.readline, ""):
        if not line:
            break
        lines.append(line.rstrip())
        log_ph.code("\n".join(lines), language="text")
    proc.wait()
    return proc.returncode, "\n".join(lines)


def save_upload(uploaded) -> str:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    path = str(TEMP_DIR / uploaded.name)
    with open(path, "wb") as f:
        f.write(uploaded.read())
    return path


def parse_chapters(text: str) -> list[dict]:
    items = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        m = re.match(r"(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*:\s*(.+)", line)
        if m:
            items.append({"start": float(m.group(1)), "end": float(m.group(2)), "label": m.group(3)})
    return items


def fmt_chapters(items: list[dict]) -> str:
    return "\n".join(f"{int(i['start'])}-{int(i['end'])}: {i['label']}" for i in items)


def hex_no_hash(c: str) -> str:
    return c.lstrip("#")
