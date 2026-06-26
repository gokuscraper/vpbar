"""Scrubber GIF handling - duration info and loop count calculation."""

import math

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def get_gif_info(gif_path: str) -> dict:
    """Get GIF total duration and frame count."""
    if not PIL_AVAILABLE:
        return {"duration": 0, "frames": 0}
    try:
        gif_img = Image.open(gif_path)
        total_duration = 0
        try:
            while True:
                total_duration += gif_img.info.get('duration', 100)
                gif_img.seek(gif_img.tell() + 1)
        except EOFError:
            pass
        return {
            "duration": total_duration / 1000.0,
            "frames": gif_img.tell()
        }
    except Exception:
        return {"duration": 0, "frames": 0}


def calculate_loop_count(gif_duration: float, video_duration: float) -> int:
    """Calculate minimum loop count to cover the video duration.
    
    -stream_loop N plays the GIF once + N additional loops.
    Minimum N so that (N+1) * gif_duration >= video_duration.
    """
    if gif_duration <= 0:
        return 100
    needed = math.ceil(video_duration / gif_duration) - 1
    return max(0, needed)
