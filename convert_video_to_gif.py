#!/usr/bin/env python3
"""将视频文件转换为 GIF，支持绿幕去除。

用法:
    python convert_video_to_gif.py input.mp4 output.gif --height 60
    python convert_video_to_gif.py input.mp4 output.gif --height 60 --green-screen
"""

import argparse
import os
import subprocess
import shutil
from pathlib import Path

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def convert_video_to_gif(
    input_path: str,
    output_path: str,
    height: int = 60,
    green_screen: bool = False,
    green_threshold: int = 150
):
    """将视频转换为 GIF，可选去除绿幕。
    
    Args:
        input_path: 输入视频路径
        output_path: 输出 GIF 路径
        height: GIF 高度（宽度自动计算保持比例）
        green_screen: 是否去除绿幕
        green_threshold: 绿色检测阈值
    """
    if not PIL_AVAILABLE:
        print("错误: 需要安装 Pillow: pip install Pillow")
        return False
    
    # 创建临时帧目录
    temp_dir = Path(tempfile.mkdtemp(prefix='video_to_gif_'))
    
    try:
        # 提取帧 - 保持原比例
        print(f'提取帧（高度={height}，保持比例）...')
        subprocess.run([
            'ffmpeg', '-i', input_path,
            '-vf', f'scale=-2:{height}:flags=neighbor',
            '-vsync', 'cfr',
            '-y', str(temp_dir / 'frame_%04d.png')
        ], capture_output=True, check=True)
        
        # 获取帧数
        frame_files = sorted(temp_dir.glob('frame_*.png'))
        if not frame_files:
            print('错误: 没有提取到帧')
            return False
        
        print(f'提取了 {len(frame_files)} 帧')
        
        # 检查实际尺寸
        sample = Image.open(frame_files[0])
        print(f'实际尺寸: {sample.size}')
        
        # 读取所有帧
        print('处理帧...')
        frames = []
        
        for frame_path in frame_files:
            img = Image.open(frame_path).convert('RGBA')
            
            # 去除绿幕
            if green_screen:
                pixels = img.load()
                for y in range(img.height):
                    for x in range(img.width):
                        r, g, b, a = pixels[x, y]
                        # 检测绿色（G > threshold, G > R, G > B）
                        if g > green_threshold and g > r and g > b:
                            pixels[x, y] = (0, 0, 0, 0)  # 设为透明
            
            frames.append(img)
        
        # 获取帧率
        result = subprocess.run([
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=r_frame_rate',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            input_path
        ], capture_output=True, text=True)
        
        # 计算帧延迟
        try:
            fps_str = result.stdout.strip()
            if '/' in fps_str:
                num, den = map(int, fps_str.split('/'))
                fps = num / den
            else:
                fps = float(fps_str)
            duration = int(1000 / fps)  # 毫秒
        except:
            duration = 41  # 默认 24fps
        
        print(f'帧延迟: {duration}ms (约 {1000/duration:.1f} fps)')
        
        # 保存为 GIF
        print('保存为 GIF...')
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=0,
            disposal=2
        )
        
        print(f'完成！输出: {output_path}')
        print(f'文件大小: {Path(output_path).stat().st_size / 1024:.1f} KB')
        return True
        
    except Exception as e:
        print(f'错误: {e}')
        return False
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)


import tempfile


def main():
    parser = argparse.ArgumentParser(description='将视频转换为 GIF')
    parser.add_argument('input', help='输入视频文件')
    parser.add_argument('output', help='输出 GIF 文件')
    parser.add_argument('--height', type=int, default=60, help='GIF 高度（默认 60）')
    parser.add_argument('--green-screen', action='store_true', help='去除绿幕')
    parser.add_argument('--green-threshold', type=int, default=150, help='绿色检测阈值（默认 150）')
    
    args = parser.parse_args()
    
    success = convert_video_to_gif(
        args.input,
        args.output,
        args.height,
        args.green_screen,
        args.green_threshold
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    import sys
    main()
