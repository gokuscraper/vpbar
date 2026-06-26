"""Video metadata retrieval via ffprobe."""

import json
import subprocess
from pathlib import Path


def get_video_info(input_path: str) -> dict:
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input video file not found: {input_path}")
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_format", "-show_streams",
                str(input_path)
            ],
            capture_output=True, check=True
        )
    except FileNotFoundError:
        raise FileNotFoundError(
            "ffprobe not found. Please ensure FFmpeg is installed and ffprobe is in PATH."
        )
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8', errors='replace') if e.stderr else 'Unknown error'
        raise RuntimeError(f"ffprobe failed to analyze video: {error_msg}")
    try:
        stdout_text = result.stdout.decode('utf-8', errors='replace')
        data = json.loads(stdout_text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse ffprobe JSON output: {e}")
    if "format" not in data:
        raise RuntimeError("No format information found in video file")
    try:
        duration = float(data["format"].get("duration", 0))
    except (ValueError, TypeError):
        raise RuntimeError("Invalid or missing duration in video format")
    video_stream = None
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            video_stream = stream
            break
    if video_stream is None:
        raise RuntimeError("No video stream found in the input file")
    width = video_stream.get("width")
    height = video_stream.get("height")
    if width is None or height is None:
        raise RuntimeError("Video stream missing width or height information")
    return {
        "duration": float(duration),
        "width": int(width),
        "height": int(height)
    }
