# 视频进度条 CLI 工具实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建一个 Python CLI 工具，使用 FFmpeg 给视频添加双层进度条

**Architecture:** Python 脚本调用 FFmpeg 命令，通过 drawbox 滤镜绘制静态底层条和动态进度条，使用 FFprobe 获取视频时长信息

**Tech Stack:** Python 3.8+, FFmpeg, FFprobe

## Global Constraints

- 输入：单个视频文件
- 输出：添加进度条的视频文件
- 进度条：底层灰色静态条 + 上层红色动态条
- 位置：默认底部，可配置顶部
- 透明度：两层都不透明

---

### Task 1: 创建主脚本框架

**Files:**
- Create: `L:\视频进度条\add_progress_bar.py`

**Interfaces:**
- Produces: `add_progress_bar.py` 主脚本，包含命令行参数解析和主函数框架

- [ ] **Step 1: 创建主脚本文件**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频进度条添加工具
使用 FFmpeg 给视频添加双层进度条（底层静态 + 上层动态）
"""

import argparse
import subprocess
import sys
import os
import json
from pathlib import Path


def get_video_info(video_path):
    """使用 FFprobe 获取视频信息"""
    pass


def generate_ffmpeg_command(input_path, output_path, duration, position, height, bg_color, fg_color):
    """生成 FFmpeg 命令"""
    pass


def add_progress_bar(input_path, output_path=None, position='bottom', height=5, bg_color='808080', fg_color='FF0000'):
    """给视频添加进度条"""
    pass


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='给视频添加双层进度条',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python add_progress_bar.py input.mp4
  python add_progress_bar.py input.mp4 -o output.mp4 --position top --height 8
        '''
    )
    
    parser.add_argument('input', help='输入视频文件路径')
    parser.add_argument('-o', '--output', help='输出视频文件路径（默认：原文件名_with_progress.扩展名）')
    parser.add_argument('-p', '--position', choices=['top', 'bottom'], default='bottom', help='进度条位置（默认：bottom）')
    parser.add_argument('--height', type=int, default=5, help='进度条高度像素（默认：5）')
    parser.add_argument('--bg-color', default='808080', help='底层颜色十六进制（默认：808080 灰色）')
    parser.add_argument('--fg-color', default='FF0000', help='上层颜色十六进制（默认：FF0000 红色）')
    
    args = parser.parse_args()
    
    add_progress_bar(
        input_path=args.input,
        output_path=args.output,
        position=args.position,
        height=args.height,
        bg_color=args.bg_color,
        fg_color=args.fg_color
    )


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: 验证文件创建成功**

Run: `python "L:\视频进度条\add_progress_bar.py" --help`
Expected: 显示帮助信息

- [ ] **Step 3: 提交代码**

```bash
git add "L:\视频进度条\add_progress_bar.py"
git commit -m "feat: 创建主脚本框架"
```

---

### Task 2: 实现 FFprobe 视频信息获取

**Files:**
- Modify: `L:\视频进度条\add_progress_bar.py` (get_video_info 函数)

**Interfaces:**
- Consumes: 视频文件路径
- Produces: `get_video_info(video_path)` 返回包含 duration, width, height 的字典

- [ ] **Step 1: 实现 get_video_info 函数**

```python
def get_video_info(video_path):
    """使用 FFprobe 获取视频信息
    
    Args:
        video_path: 视频文件路径
        
    Returns:
        dict: 包含 duration, width, height 的字典
        
    Raises:
        RuntimeError: FFprobe 执行失败
    """
    cmd = [
        'ffprobe',
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        video_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        # 获取视频流信息
        video_stream = None
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
                break
        
        if not video_stream:
            raise RuntimeError('未找到视频流')
        
        duration = float(data.get('format', {}).get('duration', 0))
        width = int(video_stream.get('width', 0))
        height = int(video_stream.get('height', 0))
        
        return {
            'duration': duration,
            'width': width,
            'height': height
        }
        
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f'FFprobe 执行失败: {e.stderr}')
    except json.JSONDecodeError as e:
        raise RuntimeError(f'FFprobe 输出解析失败: {e}')
```

- [ ] **Step 2: 测试获取视频信息**

Run: `python -c "import sys; sys.path.insert(0, r'L:\视频进度条'); from add_progress_bar import get_video_info; print(get_video_info(r'L:\视频进度条\6月6日.mov'))"`
Expected: 输出视频的 duration, width, height 信息

- [ ] **Step 3: 提交代码**

```bash
git add "L:\视频进度条\add_progress_bar.py"
git commit -m "feat: 实现 FFprobe 视频信息获取"
```

---

### Task 3: 实现 FFmpeg 命令生成

**Files:**
- Modify: `L:\视频进度条\add_progress_bar.py` (generate_ffmpeg_command 函数)

**Interfaces:**
- Consumes: 输入路径、输出路径、视频时长、位置、高度、颜色
- Produces: `generate_ffmpeg_command()` 返回 FFmpeg 命令列表

- [ ] **Step 1: 实现 generate_ffmpeg_command 函数**

```python
def generate_ffmpeg_command(input_path, output_path, duration, position, height, bg_color, fg_color):
    """生成 FFmpeg 命令
    
    Args:
        input_path: 输入视频路径
        output_path: 输出视频路径
        duration: 视频时长（秒）
        position: 进度条位置（top/bottom）
        height: 进度条高度（像素）
        bg_color: 底层颜色（十六进制）
        fg_color: 上层颜色（十六进制）
        
    Returns:
        list: FFmpeg 命令参数列表
    """
    # 根据位置计算 y 坐标
    if position == 'bottom':
        y_pos = f'ih-{height}'
    else:
        y_pos = '0'
    
    # 构建滤镜链
    # 底层：静态灰色条
    bg_filter = f"drawbox=y={y_pos}:color=0x{bg_color}:w=iw:h={height}:t=fill"
    
    # 上层：动态进度条（宽度随时间增长）
    fg_filter = f"drawbox=y={y_pos}:color=0x{fg_color}:w='iw*t/{duration}':h={height}:t=fill"
    
    # 组合滤镜
    filter_complex = f"{bg_filter},{fg_filter}"
    
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-vf', filter_complex,
        '-c:a', 'copy',  # 音频直接复制，不重新编码
        '-y',  # 覆盖输出文件
        output_path
    ]
    
    return cmd
```

- [ ] **Step 2: 测试命令生成**

Run: `python -c "import sys; sys.path.insert(0, r'L:\视频进度条'); from add_progress_bar import generate_ffmpeg_command; cmd = generate_ffmpeg_command('input.mp4', 'output.mp4', 60, 'bottom', 5, '808080', 'FF0000'); print(' '.join(cmd))"`
Expected: 输出完整的 FFmpeg 命令

- [ ] **Step 3: 提交代码**

```bash
git add "L:\视频进度条\add_progress_bar.py"
git commit -m "feat: 实现 FFmpeg 命令生成"
```

---

### Task 4: 实现主处理函数

**Files:**
- Modify: `L:\视频进度条\add_progress_bar.py` (add_progress_bar 函数)

**Interfaces:**
- Consumes: 所有参数
- Produces: 完整的视频处理流程

- [ ] **Step 1: 实现 add_progress_bar 函数**

```python
def add_progress_bar(input_path, output_path=None, position='bottom', height=5, bg_color='808080', fg_color='FF0000'):
    """给视频添加进度条
    
    Args:
        input_path: 输入视频文件路径
        output_path: 输出视频文件路径（可选）
        position: 进度条位置（top/bottom）
        height: 进度条高度（像素）
        bg_color: 底层颜色（十六进制）
        fg_color: 上层颜色（十六进制）
    """
    # 检查输入文件
    input_path = Path(input_path)
    if not input_path.exists():
        print(f'错误：输入文件不存在: {input_path}', file=sys.stderr)
        sys.exit(1)
    
    # 生成默认输出路径
    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_with_progress{input_path.suffix}"
    else:
        output_path = Path(output_path)
    
    print(f'输入文件: {input_path}')
    print(f'输出文件: {output_path}')
    
    # 获取视频信息
    print('正在获取视频信息...')
    try:
        video_info = get_video_info(str(input_path))
        print(f'视频时长: {video_info["duration"]:.2f} 秒')
        print(f'视频分辨率: {video_info["width"]}x{video_info["height"]}')
    except RuntimeError as e:
        print(f'错误：{e}', file=sys.stderr)
        sys.exit(1)
    
    # 生成 FFmpeg 命令
    cmd = generate_ffmpeg_command(
        str(input_path),
        str(output_path),
        video_info['duration'],
        position,
        height,
        bg_color,
        fg_color
    )
    
    # 执行 FFmpeg
    print('正在添加进度条...')
    try:
        subprocess.run(cmd, check=True)
        print(f'完成！输出文件: {output_path}')
    except subprocess.CalledProcessError as e:
        print(f'错误：FFmpeg 执行失败', file=sys.stderr)
        sys.exit(1)
```

- [ ] **Step 2: 测试完整流程**

Run: `python "L:\视频进度条\add_progress_bar.py" "L:\视频进度条\6月6日.mov"`
Expected: 成功生成带进度条的视频文件

- [ ] **Step 3: 提交代码**

```bash
git add "L:\视频进度条\add_progress_bar.py"
git commit -m "feat: 实现主处理函数"
```

---

### Task 5: 创建 README 文档

**Files:**
- Create: `L:\视频进度条\README.md`

**Interfaces:**
- Produces: 使用说明文档

- [ ] **Step 1: 创建 README 文件**

```markdown
# 视频进度条添加工具

一个简单的 Python CLI 工具，使用 FFmpeg 给视频添加双层进度条（底层静态 + 上层动态）。

## 功能特性

- 双层进度条：底层灰色静态条 + 上层红色动态条
- 进度条位置可配置（顶部/底部）
- 进度条高度可配置
- 颜色可自定义
- 支持常见视频格式（mp4, mov, avi, mkv 等）

## 依赖

- Python 3.8+
- FFmpeg（需要已安装并添加到系统 PATH）

## 安装

无需安装，直接运行脚本即可。

## 使用方法

### 基本用法

```bash
python add_progress_bar.py input.mp4
```

这将在当前目录生成 `input_with_progress.mp4` 文件。

### 完整参数

```bash
python add_progress_bar.py input.mp4 \
  -o output.mp4 \
  --position bottom \
  --height 5 \
  --bg-color 808080 \
  --fg-color FF0000
```

### 参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| input | - | 输入视频文件路径 | 必需 |
| --output | -o | 输出视频文件路径 | input_with_progress.ext |
| --position | -p | 进度条位置（top/bottom） | bottom |
| --height | -h | 进度条高度（像素） | 5 |
| --bg-color | -bg | 底层颜色（十六进制） | 808080（灰色） |
| --fg-color | -fg | 上层颜色（十六进制） | FF0000（红色） |

## 示例

### 底部进度条

```bash
python add_progress_bar.py video.mp4 --position bottom --height 8
```

### 顶部进度条

```bash
python add_progress_bar.py video.mp4 --position top --height 5
```

### 自定义颜色

```bash
python add_progress_bar.py video.mp4 --bg-color 000000 --fg-color 00FF00
```

## 技术原理

工具使用 FFmpeg 的 `drawbox` 滤镜绘制进度条：

1. 底层静态条：固定宽度的灰色矩形
2. 上层动态条：宽度随时间增长的红色矩形

滤镜表达式：
```
drawbox=y=ih-h:color=gray:w=iw:h=5:t=fill,
drawbox=y=ih-h:color=red:w='iw*t/duration':h=5:t=fill
```

## 许可证

MIT License
```

- [ ] **Step 2: 提交文档**

```bash
git add "L:\视频进度条\README.md"
git commit -m "docs: 添加 README 使用说明"
```

---

### Task 6: 完整测试

**Files:**
- 无新文件

**Interfaces:**
- 验证整个工具的功能

- [ ] **Step 1: 测试默认参数**

Run: `python "L:\视频进度条\add_progress_bar.py" "L:\视频进度条\6月6日.mov"`
Expected: 生成 `6月6日_with_progress.mov`，进度条在底部

- [ ] **Step 2: 测试顶部进度条**

Run: `python "L:\视频进度条\add_progress_bar.py" "L:\视频进度条\6月6日.mov" -o "L:\视频进度条\test_top.mov" --position top`
Expected: 生成 `test_top.mov`，进度条在顶部

- [ ] **Step 3: 测试自定义高度和颜色**

Run: `python "L:\视频进度条\add_progress_bar.py" "L:\视频进度条\6月6日.mov" -o "L:\视频进度条\test_custom.mov" --height 10 --bg-color 000000 --fg-color 00FF00`
Expected: 生成 `test_custom.mov`，进度条高度 10px，黑色底层，绿色上层

- [ ] **Step 4: 清理测试文件**

Run: `Remove-Item "L:\视频进度条\test_*.mov" -ErrorAction SilentlyContinue`
Expected: 删除测试生成的临时文件
