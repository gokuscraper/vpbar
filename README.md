# 视频进度条 CLI 工具

一个基于 Python 和 FFmpeg 的命令行工具，用于给视频添加双层动态进度条，效果类似抖音视频播放器。

## 功能特性

- ✅ **双层动态进度条**：支持圆角/平角、渐变色、分段、章节标记
- ✅ **AI 章节自动生成**：根据字幕内容自动分章，命名清晰通顺
- ✅ **Whisper / FunASR 语音转写**：一键从视频音频转录字幕，支持 GPU/CPU，FunASR 快 3 倍且有标点
- ✅ **Streamlit GUI**：图形界面，支持双模式（快速/专业）、87种 GIF 拖拽头、一键生成
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

### 语音转写引擎对比

**测试视频：** 472s（7′52″）720×1280 中文独白 | **GPU：** NVIDIA RTX 3060

| 引擎 | 方案 | 耗时 | 实时率 | 字幕条数 | 备注 |
|------|------|------|--------|----------|------|
| **FunASR (ONNX int8)** | VAD + ct-punc 标点断句 | **95s** | **5.0×** | 103 | ct-punc 加标点后按句切分，有逗号句号问号 |
| FunASR (ONNX int8) | VAD 分段 → 逐段推理 | **73s** | **6.5×** | 30 | VAD 粗分段，无标点，长段达 60s |
| FunASR (ONNX int8) | 整段音频 | 247s | 1.9× | 30 | ONNX 对长音频算力浪费大 |
| Whisper large-v3-turbo | 整段音频（内部 30s 窗口） | 273s | 1.7× | 300 | 粒度最细但无标点，慢 2.9 倍 |

**说明：**
- FunASR + ct-punc（标点断句模型）加标点后按句切分，字幕从 30 条粗糙大段变成 103 条合理短句，平均 4.6s/条，适合展示。ct-punc 推理仅 ~0.1s/段，30 段共 ~3s，加载约 20s。
- FunASR ONNX GPU 测试：在 RTX 3050 Laptop 上 GPU vs CPU 推理时间几乎无差异（~1-2s vs ~2-3s），因为 200M 模型的计算量太小，瓶颈在 ffmpeg 音频分段提取而非推理。GPU 仅在大模型（Whisper large-v3）或批量场景才有收益。
- FunASR 模型仅 200M 参数，Whisper 1.5B 参数，后者天生的慢。
- FunASR 错误倾向：英文/技术词（"hook客" → "hook"、"搜售platform" → "social platform"）
- Whisper 错误倾向：中文同音字（"败花钱" → "白花钱"、"调调控控" → "条条框框"）

**推荐：** 用 `--engine funasr` 快 2.9 倍且有标点，字幕质量足够 LLM 分章。

### LLM 分章效果对比

同一段视频（472s 中文独白），分别用 FunASR（103 条）和 Whisper（300 条）出字幕，丢给 LLM 分章：

| 时间段 | FunASR 分章 | Whisper 分章 |
|--------|-------------|-------------|
| 0-50s | 答质疑 | 释疑 |
| 50-168s | 流量是关键 | 流量才是关键 |
| 168-390s | 号海战术 | 批量视频获客法 |
| 390-472s | 账号与投流 | 测试与建议 |

时间边界相差仅秒级，章节命名同样准确。FunASR 的 103 条字幕对 LLM 完全够用，多 200 条无额外收益。

### 全流程耗时（转写 → 分章 → 渲染）

**测试视频：** 472s（7′52″）720×1280 | **GPU：** NVIDIA RTX 3060

| 阶段 | 基础版 | 带样式+GIF |
|------|--------|-----------|
| 转写（FunASR + ct-punc） | ~85s | ~85s |
| LLM 分章 | ~2s | ~2s |
| FFmpeg 渲染 | ~113s | ~145s |
| **总计** | **~200s** | **~232s** |

FFmpeg 渲染是主要瓶颈（占 55-62%），复杂度主要来自 GIF 叠加和渐变渲染。

## 待实现

- [ ] **macOS MLX Whisper 支持** — 参考 bilinote，使用 `mlx-whisper` 在 Apple Silicon 上利用 MLX 框架加速转写

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
│   ├── transcribe.py            # 语音转写（Whisper + FunASR）
│   ├── scrubber.py              # GIF 拖拽头处理
│   ├── gif.py                   # GIF 生成
│   ├── fonts.py                 # 字体管理
│   ├── app.py                   # Streamlit GUI 入口
│   └── gui_utils.py             # GUI 纯函数工具
├── .streamlit/                  # Streamlit 配置
│   └── config.toml
├── models/                      # Whisper 模型缓存
├── config.json                  # 样式配置
├── styles.json                  # 样式定义
├── scrubbers/                   # GIF 拖拽头模板库（87种）
├── requirements.txt             # Python 依赖清单
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
