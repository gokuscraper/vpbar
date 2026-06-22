#!/usr/bin/env python3
"""Video Progress Bar CLI Tool - Add a dual-layer progress bar to videos using FFmpeg."""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def get_video_info(input_path: str) -> dict:
    """Get video metadata using ffprobe.
    
    Args:
        input_path: Path to the input video file
        
    Returns:
        Dictionary containing video metadata (duration, width, height)
        
    Raises:
        FileNotFoundError: If ffprobe is not found or input file doesn't exist
        RuntimeError: If ffprobe fails or video has no valid video stream
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input video file not found: {input_path}")
    
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                str(input_path)
            ],
            capture_output=True,
            check=True
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
        "duration": duration,
        "width": int(width),
        "height": int(height)
    }


def generate_ffmpeg_command(
    input_path: str,
    output_path: str,
    position: str,
    height: int,
    bg_color: str,
    fg_color: str
) -> list:
    """Generate FFmpeg command for adding progress bar.
    
    Args:
        input_path: Path to the input video file
        output_path: Path to the output video file
        position: Progress bar position ('top' or 'bottom')
        height: Height of the progress bar in pixels
        bg_color: Background color in hex (e.g., '808080')
        fg_color: Foreground color in hex (e.g., 'FF0000')
        
    Returns:
        List of command arguments for subprocess
    """
    pass


def add_progress_bar(
    input_path: str,
    output_path: str,
    position: str,
    height: int,
    bg_color: str,
    fg_color: str
) -> bool:
    """Add progress bar to video using FFmpeg.
    
    Args:
        input_path: Path to the input video file
        output_path: Path to the output video file
        position: Progress bar position ('top' or 'bottom')
        height: Height of the progress bar in pixels
        bg_color: Background color in hex (e.g., '808080')
        fg_color: Foreground color in hex (e.g., 'FF0000')
        
    Returns:
        True if successful, False otherwise
    """
    pass


def main():
    """Main entry point for the CLI tool."""
    parser = argparse.ArgumentParser(
        description="Add a dual-layer progress bar to videos using FFmpeg.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.mp4
  %(prog)s input.mp4 -o output.mp4
  %(prog)s input.mp4 -p top --height 10
  %(prog)s input.mp4 --bg-color 000000 --fg-color 00FF00
        """
    )
    
    parser.add_argument(
        "input",
        type=str,
        help="Path to the input video file"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Path to the output video file (default: input_progress.mp4)"
    )
    
    parser.add_argument(
        "-p", "--position",
        type=str,
        choices=["top", "bottom"],
        default="bottom",
        help="Position of the progress bar (default: bottom)"
    )
    
    parser.add_argument(
        "--height",
        type=int,
        default=5,
        help="Height of the progress bar in pixels (default: 5)"
    )
    
    parser.add_argument(
        "--bg-color",
        type=str,
        default="808080",
        help="Background color in hex format (default: 808080)"
    )
    
    parser.add_argument(
        "--fg-color",
        type=str,
        default="FF0000",
        help="Foreground color in hex format (default: FF0000)"
    )
    
    args = parser.parse_args()
    
    input_path = args.input
    output_path = args.output
    if output_path is None:
        input_file = Path(input_path)
        output_path = str(input_file.parent / f"{input_file.stem}_progress{input_file.suffix}")
    
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print(f"Position: {args.position}")
    print(f"Height: {args.height}")
    print(f"Background color: #{args.bg_color}")
    print(f"Foreground color: #{args.fg_color}")
    
    success = add_progress_bar(
        input_path=input_path,
        output_path=output_path,
        position=args.position,
        height=args.height,
        bg_color=args.bg_color,
        fg_color=args.fg_color
    )
    
    if success:
        print("Progress bar added successfully!")
        sys.exit(0)
    else:
        print("Failed to add progress bar.")
        sys.exit(1)


if __name__ == "__main__":
    main()
