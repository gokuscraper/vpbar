# 视频进度条 CLI 工具

一个基于 Python 和 FFmpeg 的命令行工具，用于给视频添加双层动态进度条，效果类似抖音视频播放器。

## 功能特性

- ✅ **双层进度条**：底层静态条显示总时长，上层动态条显示播放进度
- ✅ **位置可配置**：支持顶部或底部显示
- ✅ **高度可配置**：自定义进度条高度（像素）
- ✅ **颜色可配置**：自定义背景色和前景色（十六进制）
- ✅ **自动检测**：自动获取视频时长和分辨率
- ✅ **音频保留**：自动复制音频流，无需重新编码
- ✅ **格式支持**：支持所有 FFmpeg 支持的视频格式（mp4, mov, avi, mkv 等）

## 依赖要求

- **Python**: 3.8 或更高版本
- **FFmpeg**: 系统已安装并添加到 PATH 环境变量

### 检查依赖

```bash
# 检查 Python 版本
python --version

# 检查 FFmpeg 是否安装
ffmpeg -version
ffprobe -version
```

## 安装

### 方式一：直接使用

克隆或下载项目后直接运行：

```bash
python add_progress_bar.py input.mp4
```

### 方式二：添加到系统 PATH（可选）

将脚本添加到系统 PATH 或创建别名：

```bash
# Linux/macOS
alias add-progress="python /path/to/add_progress_bar.py"

# Windows (PowerShell)
function add-progress { python L:\视频进度条\add_progress_bar.py $args }
```

## 使用方法

### 基本用法

最简单的用法，只需指定输入视频：

```bash
python add_progress_bar.py input.mp4
```

输出文件将自动命名为 `input_with_progress.mp4`，进度条显示在底部。

### 指定输出路径

```bash
python add_progress_bar.py input.mp4 -o output.mp4
```

### 自定义进度条位置

```bash
# 显示在顶部
python add_progress_bar.py input.mp4 -p top

# 显示在底部（默认）
python add_progress_bar.py input.mp4 -p bottom
```

### 自定义进度条高度

```bash
# 设置进度条高度为 10 像素
python add_progress_bar.py input.mp4 --height 10
```

### 自定义颜色

```bash
# 黑色背景 + 绿色前景
python add_progress_bar.py input.mp4 --bg-color 000000 --fg-color 00FF00

# 深灰背景 + 蓝色前景
python add_progress_bar.py input.mp4 --bg-color 333333 --fg-color 0066FF
```

### 完整示例

```bash
python add_progress_bar.py video.mp4 \
  -o result.mp4 \
  -p bottom \
  --height 8 \
  --bg-color 000000 \
  --fg-color FF0000
```

## 参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `input` | - | 输入视频文件路径（必需） | - |
| `--output` | `-o` | 输出视频文件路径 | `<input>_with_progress.<ext>` |
| `--position` | `-p` | 进度条位置（`top` 或 `bottom`） | `bottom` |
| `--height` | - | 进度条高度（像素） | `5` |
| `--bg-color` | - | 背景颜色（十六进制，不含 #） | `808080`（灰色） |
| `--fg-color` | - | 前景颜色（十六进制，不含 #） | `FF0000`（红色） |

## 性能

在 **Windows 11, i7-13700H, 32GB RAM** 上测试，`--segment-interval` 自动（目标 30 段）：

| 视频 | 时长 | 分辨率 | 耗时 | 倍率 |
|------|------|--------|------|------|
| 1.mkv | 11s | 1920×1080 | ~3s | ~0.3× |
| 竖屏测试.mp4 | 472s (7′52″) | 720×1280 | ~100s | ~1.7× |

瓶颈主要在 FFmpeg 编码阶段（`-preset medium` 默认）。加 `-preset ultrafast` 可缩至约 0.5× 实时，输出文件体积约 2-3 倍。

## 技术原理

### 工作流程

1. **获取视频信息**：使用 `ffprobe` 获取视频时长、宽度和高度
2. **生成滤镜链**：根据参数生成 FFmpeg `drawbox` 滤镜
3. **处理视频**：使用 FFmpeg 应用滤镜并输出新视频

### FFmpeg 滤镜实现

工具使用两个 `drawbox` 滤镜叠加实现双层进度条效果：

#### 底层（背景条）

绘制静态背景条，表示视频总时长：

```
drawbox=y=<position>:color=0x<bg_color>:w=iw:h=<height>:t=fill
```

- `y`: 垂直位置（顶部为 0，底部为 `ih-height`）
- `w=iw`: 宽度等于视频宽度
- `h`: 进度条高度
- `t=fill`: 填充模式

#### 上层（前景条）

绘制动态进度条，宽度随时间增长：

```
drawbox=y=<position>:color=0x<fg_color>:w='iw*t/<duration>':h=<height>:t=fill
```

- `w='iw*t/<duration>'`: 宽度随时间动态变化
  - `iw`: 视频宽度
  - `t`: 当前时间（秒）
  - `duration`: 视频总时长

#### 完整滤镜链示例

```bash
-vf "drawbox=y=ih-5:color=0x808080:w=iw:h=5:t=fill,drawbox=y=ih-5:color=0xFF0000:w='iw*t/60.5':h=5:t=fill"
```

### 音频处理

使用 `-c:a copy` 参数直接复制音频流，避免重新编码，提高处理速度。

## 常见问题

### FFmpeg 未找到

**错误信息**：`ffprobe not found. Please ensure FFmpeg is installed and ffprobe is in PATH.`

**解决方法**：
- 安装 FFmpeg：https://ffmpeg.org/download.html
- 确保 `ffmpeg` 和 `ffprobe` 命令在系统 PATH 中

### 输入文件不存在

**错误信息**：`Input video file not found: <path>`

**解决方法**：检查文件路径是否正确

### 视频格式不支持

**错误信息**：`No video stream found in the input file`

**解决方法**：确保输入文件是有效的视频文件

### 颜色格式错误

颜色参数应为 6 位十六进制数字（不含 #），例如：
- ✅ `FF0000`（红色）
- ✅ `00FF00`（绿色）
- ❌ `#FF0000`（不要包含 #）
- ❌ `red`（不要使用颜色名称）

## 示例效果

### 默认效果（底部灰色+红色）

```
原始视频 → 添加底部进度条（灰色背景 + 红色前景）
```

### 自定义效果（顶部黑色+绿色）

```bash
python add_progress_bar.py video.mp4 -p top --bg-color 000000 --fg-color 00FF00
```

## 开发

### 项目结构

```
L:\视频进度条\
├── add_progress_bar.py          # 主脚本
├── test_generate_command.py     # 测试脚本
├── README.md                    # 本文档
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-06-23-video-progress-bar-design.md  # 设计文档
```

### 运行测试

```bash
python test_generate_command.py
```

## 许可证

MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## 致谢

本工具基于 [FFmpeg](https://ffmpeg.org/) 强大的视频处理能力实现。
