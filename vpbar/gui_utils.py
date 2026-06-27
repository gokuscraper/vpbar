"""Utility functions for the Streamlit GUI — no Streamlit imports."""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_style_defs() -> dict:
    """Load styles.json and return {raw_name: config_dict}."""
    path = PROJECT_ROOT / "styles.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("styles", {})
    return {}


def _get_display_name(name: str, cfg: dict) -> str:
    """Add [圆角]/[方角] prefix based on corner_radius."""
    cr = cfg.get("corner_radius", 0)
    tag = "[圆角]" if cr > 0 else "[方角]"
    return f"{tag} {name}"


# Build display list and raw-name lookup from styles.json
_STYLE_DEFS = _load_style_defs()
STYLE_DISPLAY_NAMES: list[str] = []
STYLE_RAW_NAMES: dict[str, str] = {}  # display_name -> raw_name
for raw_name, cfg in _STYLE_DEFS.items():
    if raw_name.startswith("_"):
        continue
    display = _get_display_name(raw_name, cfg)
    STYLE_DISPLAY_NAMES.append(display)
    STYLE_RAW_NAMES[display] = raw_name

DEFAULT_STYLE_DISPLAY = _get_display_name("小A", _STYLE_DEFS.get("小A", {}))


def resolve_style_name(display_name: str) -> str:
    """Convert display name ('[圆角] 小A') to raw name ('小A') for CLI."""
    return STYLE_RAW_NAMES.get(display_name, display_name)
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
    for part in text.strip().replace("\n", ",").split(","):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*:\s*(.+)", part)
        if m:
            items.append({"start": float(m.group(1)), "end": float(m.group(2)), "label": m.group(3)})
    return items


def fmt_chapters(items: list[dict]) -> str:
    return "\n".join(f"{int(i['start'])}-{int(i['end'])}: {i['label']}" for i in items)


def hex_no_hash(c: str) -> str:
    return c.lstrip("#")
