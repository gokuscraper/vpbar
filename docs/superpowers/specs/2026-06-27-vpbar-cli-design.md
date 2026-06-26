# vpbar CLI 工具设计文档

## 1. 概述

将现有的单体脚本 `add_progress_bar.py`（1086 行）和 `convert_video_to_gif.py`（158 行）重构为一个模块化的 CLI 工具 `vpbar`，支持子命令分发和后续功能扩展（如 AI 功能）。

## 2. 命令接口

```
vpbar progress add <input> [options]       # 给视频添加进度条
vpbar gif convert <input> <output> [options]  # 视频转 GIF
```

运行方式：
- `pip install .` 后直接 `vpbar progress add ...`
- 或者不安装：`python -m vpbar progress add ...`

## 3. 项目结构

```
L:\视频进度条\
├── pyproject.toml              # 项目元数据 + entry point
├── config.json                 # 全局配置
├── styles.json                 # 预定义样式表
├── fonts/                      # 字体文件
├── scrubbers/gif/              # 拖拽头动画 GIF 库
├── docs/superpowers/specs/     # 设计文档
├── docs/superpowers/plans/     # 实施计划
└── vpbar/                      # Python 包
    ├── __init__.py
    ├── __main__.py             # python -m vpbar 入口
    ├── cli.py                  # 命令分发（argparse subparsers）
    ├── config.py               # 加载 config.json / styles.json
    ├── fonts.py                # 字体准备
    ├── video.py                # ffprobe 获取视频元数据
    ├── image.py                # Pillow 图片生成
    ├── chapters.py             # 章节字符串解析
    ├── scrubber.py             # 拖拽头 GIF 处理
    ├── ffmpeg.py               # FFmpeg 命令构建
    ├── progress.py             # 进度条主流程编排
    └── gif.py                  # 视频转 GIF
```

## 4. 模块职责

### 4.1 `cli.py` — 命令分发

使用 `argparse` 的 `subparsers` 实现子命令结构。解析参数后调用 `progress.add_progress_bar()` 或 `gif.convert_video_to_gif()`。

### 4.2 `config.py` — 配置加载

- `load_config()` — 读 `config.json`
- `load_styles()` — 读 `styles.json`
- `merge_with_style(cli_args, style_name)` — CLI 参数与样式合并，CLI 优先

### 4.3 `fonts.py` — 字体管理

- `prepare_fonts() -> dict` — 复制字体到临时路径，规避中文路径问题

### 4.4 `video.py` — 视频元数据

- `get_video_info(input_path) -> dict` — ffprobe 获取 duration、width、height

### 4.5 `image.py` — 图片生成

- `create_rounded_rect()` — 圆角矩形 PNG
- `create_gradient_bar()` — 渐变条 PNG
- `create_rounded_bar_with_text()` — 带章节的圆角条 PNG

纯图片生成，不涉及 FFmpeg。

### 4.6 `chapters.py` — 章节解析

- `parse_chapters(chapter_str) -> list[dict]` — 解析 `"0-6:Intro,6-11:结尾"`

### 4.7 `scrubber.py` — 拖拽头处理

- `get_gif_info(gif_path) -> dict` — 获取 GIF 总时长
- `calculate_loop_count(gif_duration, video_duration) -> int` — 计算循环次数

### 4.8 `ffmpeg.py` — FFmpeg 命令生成

- `build_square_command()` — 方角模式，使用 drawbox
- `build_rounded_command()` — 圆角模式，使用 filter_complex + PNG 叠加

### 4.9 `progress.py` — 进度条编排

- `add_progress_bar(...) -> bool` — 编排流程，依次调用 video/image/scrubber/ffmpeg 模块

### 4.10 `gif.py` — 视频转 GIF

- `convert_video_to_gif(...) -> bool` — 从 `convert_video_to_gif.py` 搬入

## 5. 数据流

### progress add
```
cli.py → config.py → progress.py → video.py → image.py → scrubber.py → ffmpeg.py → subprocess.run
```

### gif convert
```
cli.py → gif.py → video.py → ffmpeg (extract frames) → Pillow (compose GIF)
```

## 6. 依赖关系

```
cli.py
 ├─ progress.py → video.py, config.py, ffmpeg.py, image.py, fonts.py, chapters.py, scrubber.py
 └─ gif.py → video.py
```

所有依赖单向，无循环。

## 7. `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "vpbar"
version = "0.1.0"
requires-python = ">=3.8"
dependencies = []

[project.scripts]
vpbar = "vpbar.cli:main"

[tool.setuptools.packages.find]
include = ["vpbar*"]
```

## 8. 向后兼容

- 现有的 `add_progress_bar.py` 和 `convert_video_to_gif.py` 保留不动，不删除
- 新结构完全独立，互不影响

## 9. 设计原则

- **单一职责** — 每个模块只做一件事
- **单向依赖** — 无循环引用
- **接口稳定** — 函数参数传递，不共享全局状态
- **可扩展** — 新功能只需加新模块 + 注册子命令
