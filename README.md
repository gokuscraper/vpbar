# 视频进度条 CLI 工具

一个基于 Python 和 FFmpeg 的命令行工具，用于给视频添加双层动态进度条，效果类似抖音视频播放器。

## 功能特性

- ✅ **双层动态进度条**：支持圆角/平角、渐变色、分段、章节标记
- ✅ **AI 章节自动生成**：根据字幕内容自动分章，命名清晰通顺
- ✅ **Whisper 语音转写**：一键从视频音频转录字幕，支持 GPU/CPU
- ✅ **多种样式**：位置（顶部/中间/底部）、颜色、透明度、高度可配置
- ✅ **拖拽头动画**：支持 GIF 拖拽头，增强视觉效果
- ✅ **自动检测**：自动获取视频时长和分辨率
- ✅ **音频保留**：自动复制音频流，无需重新编码

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

### AI 章节生成

```bash
# 从现有字幕文件生成章节
vpbar chapters generate --srt subtitle.srt

# 从视频直接转写+分章（一次性）
vpbar progress add video.mp4 --transcribe --style 小A
```

### Whisper 语音转写

```bash
# 独立转写为 SRT 字幕
vpbar transcribe video.mp4 -o subtitle.srt

# 指定模型和设备
vpbar transcribe video.mp4 --model large-v3-turbo --device cuda
```

### 完整示例

```bash
vpbar progress add video.mp4 \
  -o result.mp4 \
  -p bottom \
  --height 8 \
  --bg-color 000000 \
  --fg-color FF0000 \
  --corner-radius 15 \
  --scrubber-image scrubber.gif \
  --transcribe
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

### 进度条渲染

在 **Windows 11, i7-13700H, 32GB RAM** 上测试，`--segment-interval` 自动（目标 30 段）：

| 视频 | 时长 | 分辨率 | 耗时 | 倍率 |
|------|------|--------|------|------|
| 1.mkv | 11s | 1920×1080 | ~3s | ~0.3× |
| 竖屏测试.mp4 | 472s (7′52″) | 720×1280 | ~100s | ~1.7× |

瓶颈主要在 FFmpeg 编码阶段（`-preset medium` 默认）。加 `-preset ultrafast` 可缩至约 0.5× 实时，输出文件体积约 2-3 倍。

### Whisper 语音转写

**模型：** `large-v3-turbo` | **视频：** 472s（7′52″）720×1280 | **GPU：** NVIDIA RTX 3060

| 设备 | 耗时 | 实时率 | 备注 |
|------|------|--------|------|
| **GPU (CUDA float16)** | **44s** | **10.77×** | 推荐，速度快 12 倍 |
| CPU (float32) | 542s (9′) | 0.87× | 比实时还慢，不推荐 |

GPU 转录 8 分钟视频仅需 44 秒，准确率极高（中英文混合场景 300 条字幕，仅少量同音字误差）。

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
├── vpbar/                       # 核心模块
│   ├── cli.py                   # CLI 入口与子命令
│   ├── config.py                # 配置加载
│   ├── chapters.py              # 章节解析与 AI 生成
│   ├── ffmpeg.py                # FFmpeg 命令构建
│   ├── image.py                 # Pillow 图像处理
│   ├── llm.py                   # LLM API 调用
│   ├── progress.py              # 进度条逻辑
│   ├── srt.py                   # SRT 字幕解析
│   ├── transcribe.py            # Whisper 语音转写
│   └── scrubber.py              # GIF 拖拽头处理
├── models/                      # Whisper 模型缓存
├── config.json                  # 样式配置
├── styles.json                  # 样式定义
├── pyproject.toml               # 项目配置与依赖
└── README.md                    # 本文档
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
