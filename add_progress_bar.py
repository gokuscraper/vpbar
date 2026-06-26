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
    from PIL import Image, ImageDraw, ImageFont
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


def create_gradient_bar(width: int, height: int, colors: list, alpha: float = 1.0, radius: int = 0, output_path: str = None):
    """Create a gradient progress bar image.
    
    Args:
        width: Bar width
        height: Bar height
        colors: List of hex colors (e.g., ['FF0000', '00FF00', '0000FF'])
        alpha: Transparency 0.0-1.0
        radius: Corner radius in pixels
        output_path: Output image path
    """
    if not PIL_AVAILABLE:
        raise ImportError("PIL/Pillow is required for gradient bars")
    
    # Create image with transparency
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Parse colors
    rgb_colors = []
    for color in colors:
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        rgb_colors.append((r, g, b, int(alpha * 255)))
    
    # Calculate segment width
    num_segments = len(rgb_colors)
    segment_width = width // num_segments
    
    # Draw gradient segments
    for i, color in enumerate(rgb_colors):
        x_start = i * segment_width
        x_end = (i + 1) * segment_width if i < num_segments - 1 else width
        
        # Draw vertical gradient between colors
        if i < num_segments - 1:
            next_color = rgb_colors[i + 1]
            for x in range(x_start, x_end):
                # Interpolate between colors
                ratio = (x - x_start) / (x_end - x_start)
                r = int(color[0] + (next_color[0] - color[0]) * ratio)
                g = int(color[1] + (next_color[1] - color[1]) * ratio)
                b = int(color[2] + (next_color[2] - color[2]) * ratio)
                a = int(color[3] + (next_color[3] - color[3]) * ratio)
                draw.line([(x, 0), (x, height - 1)], fill=(r, g, b, a))
        else:
            # Last segment, fill with last color
            draw.rectangle([x_start, 0, x_end, height - 1], fill=color)
    
    # Apply rounded corners if needed
    if radius > 0:
        # Create mask for rounded corners
        mask = Image.new('L', (width, height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([0, 0, width - 1, height - 1], radius=radius, fill=255)
        
        # Apply mask
        img.putalpha(mask)
    
    if output_path:
        img.save(output_path, 'PNG')
    
    return img


def create_rounded_bar_with_text(
    width: int,
    height: int,
    color: str,
    alpha: float,
    radius: int,
    output_path: str,
    chapters: list = None,
    duration: float = None,
    divider_width: int = 3,
    divider_height_ratio: float = 0.8,
    draw_text: bool = True
):
    """Create a rounded rectangle with chapter dividers and text labels.
    
    Args:
        width: Rectangle width
        height: Rectangle height
        color: Hex color (e.g., 'FF0000')
        alpha: Transparency 0.0-1.0
        radius: Corner radius in pixels
        output_path: Output image path
        chapters: List of chapter definitions
        duration: Video duration in seconds
        divider_width: Width of divider lines
        divider_height_ratio: Height ratio of dividers
        draw_text: Whether to draw text labels (default: True)
    """
    if not PIL_AVAILABLE:
        raise ImportError("PIL/Pillow is required for rounded corners")
    
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
    
    # 绘制章节分隔线和文字
    if chapters and duration:
        # 分隔线高度
        divider_height = int(height * divider_height_ratio)
        divider_y_offset = (height - divider_height) // 2
        
        # 字体大小
        font_size = max(10, int(height * 0.5))
        
        # 加载字体
        font_paths = prepare_fonts()
        has_chinese = any('\u4e00' <= char <= '\u9fff' for chapter in chapters if chapter.get('label') for char in chapter['label'])
        
        if has_chinese and 'chinese' in font_paths:
            font_path = font_paths['chinese']
        elif 'english' in font_paths:
            font_path = font_paths['english']
        else:
            font_path = Path("C:/Windows/Fonts/msyh.ttc")
        
        try:
            font = ImageFont.truetype(str(font_path), font_size)
        except:
            font = ImageFont.load_default()
        
        # 绘制分隔线
        for i, chapter in enumerate(chapters[:-1]):
            divider_x = int(width * (chapter['end'] / duration))
            draw.rectangle(
                [divider_x - divider_width // 2, divider_y_offset,
                 divider_x + divider_width // 2, divider_y_offset + divider_height],
                fill=(0, 0, 0, 255)  # 黑色
            )
        
        # 绘制文字标签（可选）
        if draw_text:
            for chapter in chapters:
                if not chapter.get('label'):
                    continue
                
                mid_time = (chapter['start'] + chapter['end']) / 2
                text_x = int(width * (mid_time / duration))
                
                # 使用 anchor='mm' 实现水平和垂直居中
                draw.text((text_x, height // 2), chapter['label'], 
                         fill=(0, 0, 0, 255), font=font, anchor='mm')
    
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
    bg_color: str = None,
    fg_color: str = None,
    bg_alpha: float = 1.0,
    fg_alpha: float = 1.0,
    segment_interval: int = 1,
    corner_radius: int = 0,
    chapters: list = None,
    divider_width: int = 3,
    divider_height_ratio: float = 0.8,
    gradient: list = None,
    scrubber_image: str = None
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
        divider_width: Width of chapter divider lines in pixels (default: 3)
        divider_height_ratio: Height ratio of divider (0.0-1.0, default: 0.8)
        gradient: List of hex colors for gradient (e.g., ['FF0000', '00FF00', '0000FF'])
        scrubber_image: Path to scrubber image (GIF/webp for animated scrubber)
        
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
        
        # 生成底层圆角矩形（全宽，不带分隔线和文字）
        # 背景条始终使用固定颜色，不使用渐变
        # 分隔线和文字将在滤镜链最后绘制，确保永远在最上层
        bg_img_path = os.path.join(temp_dir, 'bg.png')
        create_rounded_bar_with_text(
            width, height, bg_color, bg_alpha, corner_radius, bg_img_path,
            chapters=None,  # 不绘制分隔线和文字
            duration=duration,
            divider_width=divider_width,
            divider_height_ratio=divider_height_ratio,
            draw_text=False
        )
        
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
                
                if gradient:
                    # 渐变模式：裁剪渐变图片
                    create_gradient_bar(
                        bar_width, height, gradient, fg_alpha, corner_radius, bar_img_path
                    )
                else:
                    # 纯色模式
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
        
        # 添加动态拖拽头（如果有）
        if scrubber_image:
            # 获取 GIF 信息，计算需要循环的次数
            try:
                from PIL import Image
                gif_img = Image.open(scrubber_image)
                gif_duration = 0
                try:
                    while True:
                        gif_duration += gif_img.info.get('duration', 100)
                        gif_img.seek(gif_img.tell() + 1)
                except EOFError:
                    pass
                gif_duration = gif_duration / 1000  # 轉換為秒
                # 計算需要循環的次數（視頻時長 / GIF 時長 + 1）
                loop_count = int(duration / gif_duration) + 2
            except:
                loop_count = 100  # 默認循環 100 次
            
            # 添加拖拽头图片作为输入，使用 -stream_loop 循环 GIF
            input_args.extend(["-stream_loop", str(loop_count), "-i", scrubber_image])
            scrubber_idx = len(bar_data) + 2  # 拖拽头输入索引
            
            # 缩放拖拽头图片到进度条高度的 1.2 倍
            scrubber_size = int(height * 1.2)
            
            # 拖拽头跟随进度条移动
            # x: 从左到右移动，(W-w)*t/T，W是视频宽度，w是拖拽头宽度
            # y: 进度条中间，考虑拖拽头大小
            # 进度条中心 = H - height/2，拖拽头中心对齐进度条中心
            scrubber_y = f"H-{height//2 + scrubber_size//2}"
            
            # 使用 scale 滤镜缩放拖拽头
            # 不添加 fps、format 等滤镜，保持原始 GIF 的特性
            overlay_parts.append(
                f"[{scrubber_idx}:v]scale={scrubber_size}:{scrubber_size}:flags=neighbor[scrubber_scaled];[{prev_output}][scrubber_scaled]overlay=y={scrubber_y}:x='(W-w)*t/{duration}'[v_scrubber]"
            )
            prev_output = "v_scrubber"
        
        # 在最后绘制章节分隔线和文字，确保永远在最上层
        if chapters:
            # 准备字体文件
            font_paths = prepare_fonts()
            
            # 选择字体：中文使用思源黑体，英文使用 Roboto
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
            
            # 计算字体大小（根据进度条高度）
            font_size = max(10, int(height * 0.5))
            
            # 分隔线高度
            divider_height = int(height * divider_height_ratio)
            divider_y_offset = (height - divider_height) // 2
            
            # 构建绘制命令列表
            draw_commands = []
            
            # 计算分隔线和文字的固定 y 坐标
            # 视频高度已知，直接计算数值
            video_height = video_info['height']
            divider_y_value = video_height - height + divider_y_offset
            
            # 1. 绘制分隔线（在所有内容之上）
            for i, chapter in enumerate(chapters[:-1]):
                divider_x = int(width * (chapter['end'] / duration))
                draw_commands.append(
                    f"drawbox=x={divider_x-divider_width//2}:y={divider_y_value}:color=black:w={divider_width}:h={divider_height}:t=fill"
                )
            
            # 2. 绘制文字标签（在所有内容之上）
            for chapter in chapters:
                if not chapter.get('label'):
                    continue
                
                # 文字位置：章节中间
                mid_time = (chapter['start'] + chapter['end']) / 2
                text_x = int(width * (mid_time / duration))
                
                # 文字 y 坐标：进度条中间，考虑文字高度
                # drawtext 的 y 是基线，需要上移
                text_y_offset = height // 2 + font_size // 4
                text_y = f"H-{text_y_offset}"
                
                # 使用 drawtext 滤镜绘制文字
                draw_commands.append(
                    f"drawtext=text='{chapter['label']}':fontcolor=black:fontsize={font_size}:x={text_x}:y={text_y}:fontfile={font_path_str}:shadowcolor=white@0.8:shadowx=1:shadowy=1"
                )
            
            # 将绘制命令添加到滤镜链
            if draw_commands:
                draw_filter = ",".join(draw_commands)
                overlay_parts.append(f"[{prev_output}]{draw_filter}[v_final]")
                prev_output = "v_final"
        
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
            # 分隔线高度 = 进度条高度 * 比例
            divider_height = int(height * divider_height_ratio)
            # 分隔线 y 偏移（居中）
            divider_y_offset = (height - divider_height) // 2
            
            for i, chapter in enumerate(chapters[:-1]):  # 最后一个章节不需要分隔线
                # 分隔线位置：章节结束时间对应的x坐标
                divider_x = int(width * (chapter['end'] / duration))
                
                # 分隔线 y 坐标
                if position == 'bottom':
                    divider_y = f"ih-{height}+{divider_y_offset}"
                elif position == 'top':
                    divider_y = f"{divider_y_offset}"
                else:  # middle
                    divider_y = f"(ih-{height})/2+{divider_y_offset}"
                
                # 绘制分隔线（黑色，居中）
                drawbox_filters.append(
                    f"drawbox=x={divider_x-divider_width//2}:y={divider_y}:color=black:w={divider_width}:h={divider_height}:t=fill"
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
    bg_color: str = None,
    fg_color: str = None,
    bg_alpha: float = 1.0,
    fg_alpha: float = 1.0,
    segment_interval: int = 1,
    corner_radius: int = 0,
    chapters: list = None,
    divider_width: int = 3,
    divider_height_ratio: float = 0.8,
    gradient: list = None,
    scrubber_image: str = None
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
        chapters: List of chapter definitions
        divider_width: Width of chapter divider lines in pixels (default: 3)
        divider_height_ratio: Height ratio of divider (0.0-1.0, default: 0.8)
        gradient: List of hex colors for gradient
        scrubber_image: Path to scrubber image (GIF/webp)
        
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
            chapters=chapters,
            divider_width=divider_width,
            divider_height_ratio=divider_height_ratio,
            gradient=gradient,
            scrubber_image=scrubber_image
        )
        
        print("Processing video with FFmpeg...")
        
        # 判断是否使用圆角模式
        use_rounded = corner_radius > 0 and PIL_AVAILABLE
        
        if use_rounded:
            # 圆角模式：直接使用生成的命令（包含多个输入文件）
            print(f"Command: {' '.join(cmd[:10])} ...")
            result = subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='replace')
        else:
            # 方角模式：使用 -filter_complex_script 解决中文编码问题
            filter_file = Path(tempfile.gettempdir()) / "deveco" / "ffmpeg_filter.txt"
            filter_file.parent.mkdir(parents=True, exist_ok=True)
            filter_file.write_text(filter_complex, encoding='utf-8')
            
            cmd_with_script = [
                "ffmpeg",
                "-i", input_path,
                "-filter_complex_script", str(filter_file),
                "-c:a", "copy",
                "-y",
                output_path
            ]
            
            print(f"Command: ffmpeg -i {input_path} -filter_complex_script {filter_file} ...")
            result = subprocess.run(cmd_with_script, capture_output=True, encoding='utf-8', errors='replace')
            
            # 清理临时文件
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
    
    parser.add_argument(
        "--divider-width",
        type=int,
        default=3,
        help="Width of chapter divider lines in pixels (default: 3)"
    )
    
    parser.add_argument(
        "--divider-height-ratio",
        type=float,
        default=0.8,
        help="Height ratio of divider relative to progress bar height, 0.0-1.0 (default: 0.8)"
    )
    
    parser.add_argument(
        "--gradient",
        type=str,
        default=None,
        help="Gradient colors in format: 'FF0000,00FF00,0000FF' (overrides style gradient)"
    )
    
    parser.add_argument(
        "--scrubber-image",
        type=str,
        default=None,
        help="Path to scrubber image (GIF/webp for animated scrubber, follows progress bar)"
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
    
    # Parse gradient
    gradient = None
    if args.gradient:
        gradient = [c.strip() for c in args.gradient.split(',')]
    elif "gradient" in style_config:
        gradient = style_config["gradient"]
    
    scrubber_image = args.scrubber_image
    
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
        chapters=chapters,
        divider_width=args.divider_width,
        divider_height_ratio=args.divider_height_ratio,
        gradient=gradient,
        scrubber_image=scrubber_image
    )
    
    if success:
        print("Progress bar added successfully!")
        sys.exit(0)
    else:
        print("Failed to add progress bar.")
        sys.exit(1)


if __name__ == "__main__":
    main()
