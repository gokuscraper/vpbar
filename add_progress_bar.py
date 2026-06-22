#!/usr/bin/env python3
"""Video Progress Bar CLI Tool - Add a dual-layer progress bar to videos using FFmpeg."""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def load_config() -> dict:
    """Load configuration from config.json file.
    
    Returns:
        Dictionary containing configuration parameters
    """
    config_path = Path(__file__).parent / "config.json"
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load config file: {e}", file=sys.stderr)
    
    # Default configuration
    return {
        "position": "bottom",
        "height": 5,
        "bg_color": "808080",
        "fg_color": "FF0000",
        "segment_interval": 1
    }


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
    fg_color: str,
    segment_interval: int = 1
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
    video_info = get_video_info(input_path)
    duration = video_info['duration']
    
    if position == 'top':
        y_pos = 0
    elif position == 'middle':
        y_pos = f"(ih-{height})/2"
    else:  # bottom
        y_pos = f"ih-{height}"
    
    # 使用 filter_complex 实现真正的动态进度条
    # 方法：创建进度条视频，用 trim 动态裁剪，叠加到视频上
    
    width = video_info['width']
    fps = video_info.get('fps', 30)  # 默认 30fps
    
    # filter_complex 方案：
    # 1. 底层静态灰色条
    # 2. 创建红色条视频
    # 3. 用 timeline 方式动态控制宽度
    # 4. 叠加到原视频
    
    # 更简单可靠的方法：用 drawbox + enable 分段绘制
    # 或者用 geq 滤镜
    
    # 最可靠的方法：用 overlay 配合动态生成的进度条
    # 使用 colorkey 滤镜来实现动态裁剪效果
    
    filter_complex = (
        # 底层灰色静态条
        f"[0:v]drawbox=y={y_pos}:color=0x{bg_color}:w=iw:h={height}:t=fill[bg];"
        # 创建红色进度条视频，时长与原视频相同
        f"color=c=0x{fg_color}:s={width}x{height}:r={fps}:d={duration}[redbar];"
        # 用 trim 滤镜动态裁剪：每秒显示更多内容
        # 这里用循环方式：在每个时间点，只显示对应比例的宽度
        # 实际上用 crop 的 width 表达式
        f"[redbar]crop=w='min({width},{width}*on/(on+off))':h={height}:x=0:y=0,"
        # 这里 on/off 不对，需要用 t 变量
        f"setsar=1[bar];"
        # 叠加到视频上
        f"[bg][bar]overlay=y={y_pos}:x=0"
    )
    
    # 使用 drawbox 的 enable 参数，在不同时间绘制不同宽度的条
    # 使用配置的 segment_interval 参数
    
    num_segments = int(duration / segment_interval) + 1
    drawbox_filters = []
    
    # 底层静态条
    drawbox_filters.append(f"drawbox=y={y_pos}:color=0x{bg_color}:w=iw:h={height}:t=fill")
    
    # 上层动态条：分段绘制，每段宽度递增
    for i in range(num_segments):
        start_time = i * segment_interval
        end_time = min((i + 1) * segment_interval, duration)
        # 计算这个时间段的进度条宽度
        bar_width = int(width * (end_time / duration))
        if bar_width > 0:
            drawbox_filters.append(
                f"drawbox=y={y_pos}:color=0x{fg_color}:w={bar_width}:h={height}:t=fill:enable='between(t,{start_time},{end_time})'"
            )
    
    filter_complex = ",".join(drawbox_filters)
    
    cmd = [
        "ffmpeg",
        "-i", input_path,
        "-vf", filter_complex,
        "-c:a", "copy",
        "-y",
        output_path
    ]
    
    return cmd


def add_progress_bar(
    input_path: str,
    output_path: str,
    position: str,
    height: int,
    bg_color: str,
    fg_color: str,
    segment_interval: int = 1
) -> bool:
    """Add progress bar to video using FFmpeg.
    
    Args:
        input_path: Path to the input video file
        output_path: Path to the output video file
        position: Progress bar position ('top', 'middle', or 'bottom')
        height: Height of the progress bar in pixels
        bg_color: Background color in hex (e.g., '808080')
        fg_color: Foreground color in hex (e.g., 'FF0000')
        segment_interval: Interval in seconds for drawing segments (default: 1)
        
    Returns:
        True if successful, False otherwise
    """
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        return False
    
    if output_path is None:
        output_path = str(input_file.parent / f"{input_file.stem}_with_progress{input_file.suffix}")
    
    try:
        print("Getting video information...")
        video_info = get_video_info(input_path)
        
        duration = video_info['duration']
        width = video_info['width']
        height_res = video_info['height']
        
        print(f"Video duration: {duration:.2f} seconds")
        print(f"Video resolution: {width}x{height_res}")
        
        print("Generating FFmpeg command...")
        cmd = generate_ffmpeg_command(
            input_path=input_path,
            output_path=output_path,
            position=position,
            height=height,
            bg_color=bg_color,
            fg_color=fg_color,
            segment_interval=segment_interval
        )
        
        print("Processing video with FFmpeg...")
        print(f"Command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error: FFmpeg failed with return code {result.returncode}", file=sys.stderr)
            if result.stderr:
                print(f"FFmpeg error: {result.stderr}", file=sys.stderr)
            return False
        
        print(f"Success! Output saved to: {output_path}")
        return True
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point for the CLI tool."""
    # Load configuration
    config = load_config()
    
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
        choices=["top", "middle", "bottom"],
        default=config.get("position", "bottom"),
        help=f"Position of the progress bar (default: {config.get('position', 'bottom')})"
    )
    
    parser.add_argument(
        "--height",
        type=int,
        default=config.get("height", 5),
        help=f"Height of the progress bar in pixels (default: {config.get('height', 5)})"
    )
    
    parser.add_argument(
        "--bg-color",
        type=str,
        default=config.get("bg_color", "808080"),
        help=f"Background color in hex format (default: {config.get('bg_color', '808080')})"
    )
    
    parser.add_argument(
        "--fg-color",
        type=str,
        default=config.get("fg_color", "FF0000"),
        help=f"Foreground color in hex format (default: {config.get('fg_color', 'FF0000')})"
    )
    
    parser.add_argument(
        "--segment-interval",
        type=int,
        default=config.get("segment_interval", 1),
        help=f"Segment interval in seconds for drawing progress bar (default: {config.get('segment_interval', 1)})"
    )
    
    args = parser.parse_args()
    
    input_path = args.input
    output_path = args.output
    if output_path is None:
        input_file = Path(input_path)
        output_path = str(input_file.parent / f"{input_file.stem}_with_progress{input_file.suffix}")
    
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print(f"Position: {args.position}")
    print(f"Height: {args.height}")
    print(f"Background color: #{args.bg_color}")
    print(f"Foreground color: #{args.fg_color}")
    print(f"Segment interval: {args.segment_interval}s")
    
    success = add_progress_bar(
        input_path=input_path,
        output_path=output_path,
        position=args.position,
        height=args.height,
        bg_color=args.bg_color,
        fg_color=args.fg_color,
        segment_interval=args.segment_interval
    )
    
    if success:
        print("Progress bar added successfully!")
        sys.exit(0)
    else:
        print("Failed to add progress bar.")
        sys.exit(1)


if __name__ == "__main__":
    main()
