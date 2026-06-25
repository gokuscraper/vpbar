#!/usr/bin/env python3
"""Video Progress Bar CLI Tool - Add a dual-layer progress bar to videos using FFmpeg."""

import argparse
import json
import subprocess
import sys
import tempfile
import os
from pathlib import Path

try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def prepare_fonts() -> dict:
    """准备字体文件，复制到临时目录以避免路径中的中文字符问题。
    
    Returns:
        字体名称到路径的映射字典
    """
    import shutil
    
    # 临时字体目录
    temp_font_dir = Path(tempfile.gettempdir()) / "deveco" / "fonts"
    temp_font_dir.mkdir(parents=True, exist_ok=True)
    
    # 项目字体目录
    script_dir = Path(__file__).parent
    project_font_dir = script_dir / "fonts"
    
    fonts = {
        'chinese': 'SourceHanSansSC-Regular.otf',  # 思源黑体
        'english': 'Roboto-Regular.ttf',  # Roboto
    }
    
    font_paths = {}
    
    for name, font_file in fonts.items():
        src_path = project_font_dir / font_file
        dst_path = temp_font_dir / font_file
        
        # 如果源文件存在，复制到临时目录
        if src_path.exists():
            if not dst_path.exists() or src_path.stat().st_mtime > dst_path.stat().st_mtime:
                shutil.copy2(src_path, dst_path)
            font_paths[name] = dst_path
        elif dst_path.exists():
            # 源不存在但临时目录有，直接使用
            font_paths[name] = dst_path
    
    return font_paths


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


def load_styles() -> dict:
    """Load styles from styles.json file.
    
    Returns:
        Dictionary containing styles configuration
    """
    styles_path = Path(__file__).parent / "styles.json"
    
    if styles_path.exists():
        try:
            with open(styles_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load styles file: {e}", file=sys.stderr)
    
    # Default styles
    return {
        "styles": {
            "默认": {
                "bg_color": "808080",
                "bg_alpha": 1.0,
                "fg_color": "FF0000",
                "fg_alpha": 1.0,
                "height": 5,
                "position": "bottom"
            }
        },
        "default_style": "默认",
        "segment_interval": 1
    }


def create_rounded_rect(width: int, height: int, color: str, alpha: float, radius: int, output_path: str):
    """Create a rounded rectangle image with transparency.
    
    Args:
        width: Rectangle width
        height: Rectangle height
        color: Hex color (e.g., 'FF0000')
        alpha: Transparency 0.0-1.0
        radius: Corner radius in pixels
        output_path: Output image path
    """
    if not PIL_AVAILABLE:
        raise ImportError("PIL/Pillow is required for rounded corners. Install with: pip install Pillow")
    
    # Parse hex color
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)
    a = int(alpha * 255)
    
    # Create image with transparency
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw rounded rectangle
    draw.rounded_rectangle(
        [0, 0, width - 1, height - 1],
        radius=radius,
        fill=(r, g, b, a)
    )
    
    img.save(output_path, 'PNG')


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
    bg_alpha: float = 1.0,
    fg_alpha: float = 1.0,
    segment_interval: int = 1,
    corner_radius: int = 0,
    chapters: list = None
) -> list:
    """Generate FFmpeg command for adding progress bar.
    
    Args:
        input_path: Path to the input video file
        output_path: Path to the output video file
        position: Progress bar position ('top' or 'bottom')
        height: Height of the progress bar in pixels
        bg_color: Background color in hex (e.g., '808080')
        fg_color: Foreground color in hex (e.g., 'FF0000')
        bg_alpha: Background transparency (0.0-1.0, default: 1.0)
        fg_alpha: Foreground transparency (0.0-1.0, default: 1.0)
        segment_interval: Interval in seconds for drawing segments (default: 1)
        corner_radius: Corner radius in pixels, 0 for square corners (default: 0)
        chapters: List of chapter definitions, each with 'start', 'end', 'label'
        
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
    
    # 判断是否使用圆角模式
    use_rounded = corner_radius > 0 and PIL_AVAILABLE
    
    if use_rounded:
        # 圆角模式：使用预生成的圆角矩形图片
        # 使用英文临时目录，避免中文路径问题
        temp_base = 'C:\\Users\\27598\\AppData\\Local\\Temp\\deveco'
        os.makedirs(temp_base, exist_ok=True)
        temp_dir = os.path.join(temp_base, 'progress_bar_temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        # 生成底层圆角矩形（全宽）
        bg_img_path = os.path.join(temp_dir, 'bg.png')
        create_rounded_rect(width, height, bg_color, bg_alpha, corner_radius, bg_img_path)
        
        # 生成不同宽度的进度条圆角矩形
        num_segments = int(duration / segment_interval) + 1
        
        # 构建输入参数和滤镜链
        input_args = ["-i", input_path]
        
        # 底层静态条：将背景图片作为输入
        input_args.extend(["-i", bg_img_path])
        
        # 上层动态条：生成所有进度条图片
        bar_data = []
        for i in range(num_segments):
            start_time = i * segment_interval
            end_time = min((i + 1) * segment_interval, duration)
            bar_width = int(width * (start_time / duration))
            
            if bar_width > 0:
                bar_img_path = os.path.join(temp_dir, f'bar_{i}.png')
                create_rounded_rect(bar_width, height, fg_color, fg_alpha, corner_radius, bar_img_path)
                input_args.extend(["-i", bar_img_path])
                bar_data.append((start_time, end_time))
        
        # 构建 filter_complex
        # 计算y坐标（overlay中使用H表示输出高度）
        y_expr = f"H-{height}"
        
        # 先叠加底层 [0:v]视频 [1:v]背景图
        overlay_parts = [f"[0:v][1:v]overlay=y={y_expr}:x=0[v0]"]
        prev_output = "v0"
        
        # 再叠加动态条 [2:v], [3:v], ...
        for idx, (start_time, end_time) in enumerate(bar_data):
            input_idx = idx + 2  # 从2开始（0是视频，1是背景）
            overlay_parts.append(
                f"[{prev_output}][{input_idx}:v]overlay=y={y_expr}:x=0:enable='between(t,{start_time},{end_time})'[v{idx+1}]"
            )
            prev_output = f"v{idx+1}"
        
        filter_complex = ";".join(overlay_parts)
        
        cmd = [
            "ffmpeg",
        ] + input_args + [
            "-filter_complex", filter_complex,
            "-map", f"[{prev_output}]",
            "-c:a", "copy",
            "-y",
            output_path
        ]
    else:
        # 方角模式：使用 drawbox
        num_segments = int(duration / segment_interval) + 1
        drawbox_filters = []
        
        # 底层静态条（带透明度）
        drawbox_filters.append(f"drawbox=y={y_pos}:color=0x{bg_color}@{bg_alpha}:w=iw:h={height}:t=fill")
        
        # 上层动态条：分段绘制，每段宽度递增（带透明度）
        for i in range(num_segments):
            start_time = i * segment_interval
            end_time = min((i + 1) * segment_interval, duration)
            # 使用开始时间计算宽度，确保进度条与视频同步
            bar_width = int(width * (start_time / duration))
            if bar_width > 0:
                drawbox_filters.append(
                    f"drawbox=y={y_pos}:color=0x{fg_color}@{fg_alpha}:w={bar_width}:h={height}:t=fill:enable='between(t,{start_time},{end_time})'"
                )
        
        # 添加章节分隔线和文字标签
        if chapters:
            # 计算字体大小（根据进度条高度）
            font_size = max(10, int(height * 0.5))
            
            # 绘制分隔线
            for i, chapter in enumerate(chapters[:-1]):  # 最后一个章节不需要分隔线
                # 分隔线位置：章节结束时间对应的x坐标
                divider_x = int(width * (chapter['end'] / duration))
                
                # 绘制分隔线（黑色细线，宽度2px）
                drawbox_filters.append(
                    f"drawbox=x={divider_x-1}:y={y_pos}:color=black:w=2:h={height}:t=fill"
                )
            
            # 绘制文字标签
            # 准备字体文件
            font_paths = prepare_fonts()
            
            # 选择字体：中文使用思源黑体，英文使用 Roboto
            # 检查标签是否包含中文
            has_chinese = any('\u4e00' <= char <= '\u9fff' for chapter in chapters if chapter.get('label') for char in chapter['label'])
            
            if has_chinese and 'chinese' in font_paths:
                font_path = font_paths['chinese']
            elif 'english' in font_paths:
                font_path = font_paths['english']
            else:
                # 回退到系统字体
                font_path = Path("C:/Windows/Fonts/msyh.ttc")
            
            # 转换为 FFmpeg 可接受的路径格式
            # Windows 路径需要转义冒号：C:/path -> C\\:/path
            font_path_str = str(font_path).replace('\\', '/')
            if len(font_path_str) > 1 and font_path_str[1] == ':':
                font_path_str = font_path_str[0] + '\\\\:' + font_path_str[2:]
            
            for chapter in chapters:
                if not chapter.get('label'):
                    continue
                    
                # 计算文字位置（章节中间）
                mid_time = (chapter['start'] + chapter['end']) / 2
                text_x = int(width * (mid_time / duration))
                
                # 文字y坐标（进度条内部居中，使用固定数值）
                text_y_offset = (height - font_size) // 2
                if position == 'bottom':
                    text_y = f"h-{height}+{text_y_offset}"
                elif position == 'top':
                    text_y = f"{text_y_offset}"
                else:  # middle
                    text_y = f"(h-{height})/2+{text_y_offset}"
                
                # 使用 drawtext 滤镜绘制文字
                drawbox_filters.append(
                    f"drawtext=text='{chapter['label']}':fontcolor=black:fontsize={font_size}:x={text_x}:y={text_y}:fontfile={font_path_str}"
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
    
    return cmd, filter_complex


def add_progress_bar(
    input_path: str,
    output_path: str,
    position: str,
    height: int,
    bg_color: str,
    fg_color: str,
    bg_alpha: float = 1.0,
    fg_alpha: float = 1.0,
    segment_interval: int = 1,
    corner_radius: int = 0,
    chapters: list = None
) -> bool:
    """Add progress bar to video using FFmpeg.
    
    Args:
        input_path: Path to the input video file
        output_path: Path to the output video file
        position: Progress bar position ('top', 'middle', or 'bottom')
        height: Height of the progress bar in pixels
        bg_color: Background color in hex (e.g., '808080')
        fg_color: Foreground color in hex (e.g., 'FF0000')
        bg_alpha: Background transparency (0.0-1.0, default: 1.0)
        fg_alpha: Foreground transparency (0.0-1.0, default: 1.0)
        segment_interval: Interval in seconds for drawing segments (default: 1)
        corner_radius: Corner radius in pixels, 0 for square corners (default: 0)
        
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
        cmd, filter_complex = generate_ffmpeg_command(
            input_path=input_path,
            output_path=output_path,
            position=position,
            height=height,
            bg_color=bg_color,
            fg_color=fg_color,
            bg_alpha=bg_alpha,
            fg_alpha=fg_alpha,
            segment_interval=segment_interval,
            corner_radius=corner_radius,
            chapters=chapters
        )
        
        print("Processing video with FFmpeg...")
        
        # 将滤镜参数写入临时文件（解决中文编码问题）
        filter_file = Path(tempfile.gettempdir()) / "deveco" / "ffmpeg_filter.txt"
        filter_file.parent.mkdir(parents=True, exist_ok=True)
        filter_file.write_text(filter_complex, encoding='utf-8')
        
        # 使用 -filter_complex_script 从文件读取滤镜
        cmd_with_script = [
            "ffmpeg",
            "-i", input_path,
            "-filter_complex_script", str(filter_file),
            "-c:a", "copy",
            "-y",
            output_path
        ]
        
        print(f"Command: ffmpeg -i {input_path} -filter_complex_script {filter_file} ...")
        
        # 使用 UTF-8 编码运行 FFmpeg
        result = subprocess.run(cmd_with_script, capture_output=True, encoding='utf-8', errors='replace')
        
        # 保留临时文件用于调试（如果失败）
        if result.returncode == 0 and filter_file.exists():
            filter_file.unlink()
        
        if result.returncode != 0:
            print(f"Error: FFmpeg failed with return code {result.returncode}", file=sys.stderr)
            print(f"Filter file: {filter_file}", file=sys.stderr)
            if filter_file.exists():
                print(f"Filter content:\n{filter_file.read_text(encoding='utf-8')}", file=sys.stderr)
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
    # Load styles configuration
    styles_config = load_styles()
    styles = styles_config.get("styles", {})
    default_style = styles_config.get("default_style", "默认")
    
    parser = argparse.ArgumentParser(
        description="Add a dual-layer progress bar to videos using FFmpeg.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.mp4
  %(prog)s input.mp4 -o output.mp4
  %(prog)s input.mp4 --style 小A
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
        "--style",
        type=str,
        choices=list(styles.keys()),
        default=default_style,
        help=f"Progress bar style (default: {default_style}). Available: {', '.join(styles.keys())}"
    )
    
    parser.add_argument(
        "-p", "--position",
        type=str,
        choices=["top", "middle", "bottom"],
        default=None,
        help="Position of the progress bar (overrides style)"
    )
    
    parser.add_argument(
        "--height",
        type=int,
        default=None,
        help="Height of the progress bar in pixels (overrides style)"
    )
    
    parser.add_argument(
        "--bg-color",
        type=str,
        default=None,
        help="Background color in hex format (overrides style)"
    )
    
    parser.add_argument(
        "--fg-color",
        type=str,
        default=None,
        help="Foreground color in hex format (overrides style)"
    )
    
    parser.add_argument(
        "--bg-alpha",
        type=float,
        default=None,
        help="Background transparency 0.0-1.0 (overrides style)"
    )
    
    parser.add_argument(
        "--fg-alpha",
        type=float,
        default=None,
        help="Foreground transparency 0.0-1.0 (overrides style)"
    )
    
    parser.add_argument(
        "--segment-interval",
        type=int,
        default=styles_config.get("segment_interval", 1),
        help=f"Segment interval in seconds (default: {styles_config.get('segment_interval', 1)})"
    )
    
    parser.add_argument(
        "--corner-radius",
        type=int,
        default=None,
        help="Corner radius in pixels, 0 for square corners (overrides style). Requires Pillow for rounded corners."
    )
    
    parser.add_argument(
        "--chapters",
        type=str,
        default=None,
        help="Chapter definition in format: 'start1-end1:label1,start2-end2:label2,...' Example: '0-6:开头,6-11:结尾'"
    )
    
    args = parser.parse_args()
    
    # Parse chapters argument
    chapters = None
    if args.chapters:
        chapters = []
        for chapter_str in args.chapters.split(','):
            parts = chapter_str.strip().split(':')
            if len(parts) == 2:
                time_range, label = parts
                start, end = time_range.split('-')
                chapters.append({
                    'start': float(start),
                    'end': float(end),
                    'label': label.strip()
                })
    
    # Get style configuration
    style_config = styles.get(args.style, {})
    
    # Merge style config with command line arguments (CLI overrides style)
    position = args.position if args.position else style_config.get("position", "bottom")
    height = args.height if args.height else style_config.get("height", 5)
    bg_color = args.bg_color if args.bg_color else style_config.get("bg_color", "808080")
    fg_color = args.fg_color if args.fg_color else style_config.get("fg_color", "FF0000")
    bg_alpha = args.bg_alpha if args.bg_alpha is not None else style_config.get("bg_alpha", 1.0)
    fg_alpha = args.fg_alpha if args.fg_alpha is not None else style_config.get("fg_alpha", 1.0)
    corner_radius = args.corner_radius if args.corner_radius is not None else style_config.get("corner_radius", 0)
    
    input_path = args.input
    output_path = args.output
    if output_path is None:
        input_file = Path(input_path)
        output_path = str(input_file.parent / f"{input_file.stem}_with_progress{input_file.suffix}")
    
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print(f"Style: {args.style}")
    print(f"Position: {position}")
    print(f"Height: {height}")
    print(f"Background: #{bg_color} @ {bg_alpha}")
    print(f"Foreground: #{fg_color} @ {fg_alpha}")
    print(f"Corner radius: {corner_radius}px")
    print(f"Segment interval: {args.segment_interval}s")
    if chapters:
        print(f"Chapters: {len(chapters)}")
        for ch in chapters:
            print(f"  - {ch['start']}-{ch['end']}s: {ch['label']}")
    
    success = add_progress_bar(
        input_path=input_path,
        output_path=output_path,
        position=position,
        height=height,
        bg_color=bg_color,
        fg_color=fg_color,
        bg_alpha=bg_alpha,
        fg_alpha=fg_alpha,
        segment_interval=args.segment_interval,
        corner_radius=corner_radius,
        chapters=chapters
    )
    
    if success:
        print("Progress bar added successfully!")
        sys.exit(0)
    else:
        print("Failed to add progress bar.")
        sys.exit(1)


if __name__ == "__main__":
    main()
