"""Progress bar orchestration - the main workflow."""

import subprocess
import sys
from pathlib import Path

from vpbar.video import get_video_info
from vpbar.ffmpeg import build_bar_command


def add_progress_bar(
    input_path: str, output_path: str = None,
    position: str = "bottom", height: int = 5,
    bg_color: str = "808080", fg_color: str = "FF0000",
    bg_alpha: float = 1.0, fg_alpha: float = 1.0,
    segment_interval: int = 1, corner_radius: int = 0,
    chapters: list = None, divider_width: int = 3,
    divider_height_ratio: float = 0.8, gradient: list = None,
    scrubber_image: str = None
) -> bool:
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        return False
    if output_path is None:
        output_path = str(input_file.parent / f"{input_file.stem}_with_progress{input_file.suffix}")
    try:
        print("Getting video information...")
        video_info = get_video_info(input_path)
        print(f"Video duration: {video_info['duration']:.2f} seconds")
        print(f"Video resolution: {video_info['width']}x{video_info['height']}")
        print("Generating FFmpeg command...")

        cmd, _ = build_bar_command(
            input_path=input_path, output_path=output_path,
            position=position, height=height,
            bg_color=bg_color, fg_color=fg_color,
            bg_alpha=bg_alpha, fg_alpha=fg_alpha,
            segment_interval=segment_interval,
            corner_radius=corner_radius,
            chapters=chapters, divider_width=divider_width,
            divider_height_ratio=divider_height_ratio,
            gradient=gradient, scrubber_image=scrubber_image,
            video_info=video_info
        )
        print("Processing video with FFmpeg...")
        print(f"Command: {' '.join(str(c) for c in cmd[:8])} ...")
        result = subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='replace')
        if result.returncode != 0:
            print(f"Error: FFmpeg failed with return code {result.returncode}", file=sys.stderr)
            if result.stderr:
                print(f"FFmpeg error: {result.stderr}", file=sys.stderr)
            return False
        print(f"Success! Output saved to: {output_path}")
        return True
    except (FileNotFoundError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return False
