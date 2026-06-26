"""FFmpeg command generation for both square and rounded corner modes."""

import os
import tempfile
from pathlib import Path

from vpbar.image import create_rounded_rect, create_gradient_bar, create_rounded_bar_with_text
from vpbar.fonts import prepare_fonts
from vpbar.scrubber import get_gif_info, calculate_loop_count


def build_square_command(
    input_path: str, output_path: str, position: str, height: int,
    video_info: dict, bg_color: str, fg_color: str,
    bg_alpha: float, fg_alpha: float, segment_interval: int,
    chapters: list = None, divider_width: int = 3, divider_height_ratio: float = 0.8
):
    duration = video_info['duration']
    width = video_info['width']
    if position == 'top':
        y_pos = 0
    elif position == 'middle':
        y_pos = f"(ih-{height})/2"
    else:
        y_pos = f"ih-{height}"
    num_segments = int(duration / segment_interval) + 1
    drawbox_filters = []
    drawbox_filters.append(f"drawbox=y={y_pos}:color=0x{bg_color}@{bg_alpha}:w=iw:h={height}:t=fill")
    for i in range(num_segments):
        start_time = i * segment_interval
        end_time = min((i + 1) * segment_interval, duration)
        bar_width = int(width * (start_time / duration))
        if bar_width > 0:
            drawbox_filters.append(
                f"drawbox=y={y_pos}:color=0x{fg_color}@{fg_alpha}:w={bar_width}:h={height}:t=fill:enable='between(t,{start_time},{end_time})'"
            )
    if chapters:
        font_size = max(10, int(height * 0.5))
        divider_height = int(height * divider_height_ratio)
        divider_y_offset = (height - divider_height) // 2
        for i, chapter in enumerate(chapters[:-1]):
            divider_x = int(width * (chapter['end'] / duration))
            if position == 'bottom':
                divider_y = f"ih-{height}+{divider_y_offset}"
            elif position == 'top':
                divider_y = f"{divider_y_offset}"
            else:
                divider_y = f"(ih-{height})/2+{divider_y_offset}"
            drawbox_filters.append(
                f"drawbox=x={divider_x-divider_width//2}:y={divider_y}:color=black:w={divider_width}:h={divider_height}:t=fill"
            )
        font_paths = prepare_fonts()
        has_chinese = any('\u4e00' <= char <= '\u9fff' for chapter in chapters if chapter.get('label') for char in chapter['label'])
        if has_chinese and 'chinese' in font_paths:
            font_path = font_paths['chinese']
        elif 'english' in font_paths:
            font_path = font_paths['english']
        else:
            font_path = Path("C:/Windows/Fonts/msyh.ttc")
        font_path_str = str(font_path).replace('\\', '/')
        if len(font_path_str) > 1 and font_path_str[1] == ':':
            font_path_str = font_path_str[0] + '\\\\:' + font_path_str[2:]
        for chapter in chapters:
            if not chapter.get('label'):
                continue
            mid_time = (chapter['start'] + chapter['end']) / 2
            text_x = int(width * (mid_time / duration))
            text_y_offset = (height - font_size) // 2
            if position == 'bottom':
                text_y = f"h-{height}+{text_y_offset}"
            elif position == 'top':
                text_y = f"{text_y_offset}"
            else:
                text_y = f"(h-{height})/2+{text_y_offset}"
            drawbox_filters.append(
                f"drawtext=text='{chapter['label']}':fontcolor=black:fontsize={font_size}:x={text_x}:y={text_y}:fontfile={font_path_str}"
            )
    filter_complex = ",".join(drawbox_filters)
    filter_file = Path(tempfile.gettempdir()) / "deveco" / "ffmpeg_filter.txt"
    filter_file.parent.mkdir(parents=True, exist_ok=True)
    filter_file.write_text(filter_complex, encoding='utf-8')
    return [
        "ffmpeg",
        "-i", input_path,
        "-filter_complex_script", str(filter_file),
        "-c:a", "copy",
        "-y",
        output_path
    ], filter_file


def build_rounded_command(
    input_path: str, output_path: str, position: str, height: int,
    video_info: dict, bg_color: str, fg_color: str,
    bg_alpha: float, fg_alpha: float, segment_interval: int,
    corner_radius: int, chapters: list = None,
    divider_width: int = 3, divider_height_ratio: float = 0.8,
    gradient: list = None, scrubber_image: str = None
):
    duration = video_info['duration']
    width = video_info['width']
    video_height = video_info['height']
    temp_base = os.path.join(tempfile.gettempdir(), 'deveco')
    os.makedirs(temp_base, exist_ok=True)
    temp_dir = os.path.join(temp_base, 'progress_bar_temp')
    os.makedirs(temp_dir, exist_ok=True)

    if position == 'top':
        bar_y = "0"
        bar_top_px = 0
    elif position == 'middle':
        bar_y = f"(H-{height})/2"
        bar_top_px = (video_height - height) // 2
    else:
        bar_y = f"H-{height}"
        bar_top_px = video_height - height
    bg_img_path = os.path.join(temp_dir, 'bg.png')
    create_rounded_bar_with_text(
        width, height, bg_color, bg_alpha, corner_radius, bg_img_path,
        chapters=None, duration=duration,
        divider_width=divider_width, divider_height_ratio=divider_height_ratio,
        draw_text=False
    )
    num_segments = int(duration / segment_interval) + 1
    input_args = ["-i", input_path, "-i", bg_img_path]
    bar_data = []
    for i in range(num_segments):
        start_time = i * segment_interval
        end_time = min((i + 1) * segment_interval, duration)
        bar_width = int(width * (start_time / duration))
        if bar_width > 0:
            bar_img_path = os.path.join(temp_dir, f'bar_{i}.png')
            if gradient:
                create_gradient_bar(bar_width, height, gradient, fg_alpha, corner_radius, bar_img_path)
            else:
                create_rounded_rect(bar_width, height, fg_color, fg_alpha, corner_radius, bar_img_path)
            input_args.extend(["-i", bar_img_path])
            bar_data.append((start_time, end_time))
    overlay_parts = [f"[0:v][1:v]overlay=y={bar_y}:x=0[v0]"]
    prev_output = "v0"
    for idx, (start_time, end_time) in enumerate(bar_data):
        input_idx = idx + 2
        overlay_parts.append(
            f"[{prev_output}][{input_idx}:v]overlay=y={bar_y}:x=0:enable='between(t,{start_time},{end_time})'[v{idx+1}]"
        )
        prev_output = f"v{idx+1}"
    if scrubber_image:
        try:
            gif_info = get_gif_info(scrubber_image)
            loop_count = calculate_loop_count(gif_info["duration"], duration)
        except:
            loop_count = 100
        input_args.extend(["-stream_loop", str(loop_count), "-i", scrubber_image])
        scrubber_idx = len(bar_data) + 2
        scrubber_size = int(height * 1.2)
        scrubber_y = f"{bar_y}+{height//2 - scrubber_size//2}"
        overlay_parts.append(
            f"[{scrubber_idx}:v]scale=-1:{scrubber_size}:flags=neighbor[scrubber_scaled];"
            f"[{prev_output}][scrubber_scaled]overlay=y={scrubber_y}:x='(W-w)*t/{duration}'[v_scrubber]"
        )
        prev_output = "v_scrubber"
    if chapters:
        font_paths = prepare_fonts()
        has_chinese = any('\u4e00' <= char <= '\u9fff' for chapter in chapters if chapter.get('label') for char in chapter['label'])
        if has_chinese and 'chinese' in font_paths:
            font_path = font_paths['chinese']
        elif 'english' in font_paths:
            font_path = font_paths['english']
        else:
            font_path = Path("C:/Windows/Fonts/msyh.ttc")
        font_path_str = str(font_path).replace('\\', '/')
        if len(font_path_str) > 1 and font_path_str[1] == ':':
            font_path_str = font_path_str[0] + '\\\\:' + font_path_str[2:]
        font_size = max(10, int(height * 0.5))
        divider_height = int(height * divider_height_ratio)
        divider_y_offset = (height - divider_height) // 2
        draw_commands = []
        divider_y_value = bar_top_px + divider_y_offset
        for i, chapter in enumerate(chapters[:-1]):
            divider_x = int(width * (chapter['end'] / duration))
            draw_commands.append(
                f"drawbox=x={divider_x-divider_width//2}:y={divider_y_value}:color=black:w={divider_width}:h={divider_height}:t=fill"
            )
        for chapter in chapters:
            if not chapter.get('label'):
                continue
            mid_time = (chapter['start'] + chapter['end']) / 2
            text_x = int(width * (mid_time / duration))
            text_y_offset = height // 2 - font_size // 4
            text_y = f"{bar_y}+{text_y_offset}"
            draw_commands.append(
                f"drawtext=text='{chapter['label']}':fontcolor=black:fontsize={font_size}:"
                f"x={text_x}:y={text_y}:fontfile={font_path_str}:shadowcolor=white@0.8:shadowx=1:shadowy=1"
            )
        if draw_commands:
            draw_filter = ",".join(draw_commands)
            overlay_parts.append(f"[{prev_output}]{draw_filter}[v_final]")
            prev_output = "v_final"
    filter_complex = ";".join(overlay_parts)
    cmd = ["ffmpeg"] + input_args + [
        "-filter_complex", filter_complex,
        "-map", f"[{prev_output}]",
        "-map", "0:a?",
        "-c:a", "copy",
        "-t", str(duration),
        "-y", output_path
    ]
    return cmd, None
