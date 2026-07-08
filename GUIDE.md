# vpbar 使用指南

## 完整命令参考

### `vpbar progress add` — 渲染进度条

```bash
vpbar progress add <input> [-o <output>] [选项]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `input` | 输入视频路径（必需） | — |
| `-o, --output` | 输出视频路径 | `<input>_with_progress.mp4` |
| `--style` | 样式名称（见 styles.json） | `默认` |
| `-p, --position` | 位置：`top`/`middle`/`bottom` | 样式默认 |
| `--height` | 高度（像素） | 样式默认 |
| `--bg-color` | 背景色（6位十六进制） | 样式默认 |
| `--fg-color` | 前景色（6位十六进制） | 样式默认 |
| `--bg-alpha` | 背景透明度 0-1 | 样式默认 |
| `--fg-alpha` | 前景透明度 0-1 | 样式默认 |
| `--corner-radius` | 圆角半径（像素） | 样式默认 |
| `--gradient` | 渐变色：`FF0000,00FF00,0000FF` | 无 |
| `--chapters` | 章节：`0-6:介绍,6-11:结尾` | 无 |
| `--divider-width` | 章节分隔线宽度 | `3` |
| `--divider-height-ratio` | 分隔线高度比例 0-1 | `0.8` |
| `--segment-interval` | 分段间隔秒数（0=自动） | `0` |
| `--scrubber-image` | GIF 拖拽头路径 | 无 |
| `--transcribe` | 先转写（可选模型大小） | 无 |
| `--engine` | 转写引擎：`whisper`/`funasr` | `whisper` |
| `--srt` | 外部 SRT 字幕文件 | 无 |

### `vpbar transcribe` — 语音转写

```bash
vpbar transcribe <input> [-o <output>] [选项]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `input` | 输入视频路径（必需） | — |
| `-o, --output` | 输出 SRT 路径 | `<input>.srt` |
| `--engine` | 引擎：`whisper`/`funasr` | `whisper` |
| `--model` | Whisper 模型大小 | `large-v3-turbo` |
| `--device` | 设备：`auto`/`cpu`/`cuda` | `auto` |
| `--compute-type` | 计算类型：`default`/`float16`/`int8` | `default` |

### `vpbar chapters generate` — AI 分章

```bash
vpbar chapters generate --srt <file> [选项]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--srt` | SRT 字幕路径（必需） | — |
| `-o, --output` | 保存到文件 | 标准输出 |
| `--min-chapters` | 最小章节数 | `2` |
| `--max-chapters` | 最大章节数 | `4` |
| `--max-label-length` | 标签最大字数 | `7` |

### `vpbar gif convert` — 视频转 GIF

```bash
vpbar gif convert <input> <output> [选项]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `input` | 输入视频路径（必需） | — |
| `output` | 输出 GIF 路径（必需） | — |
| `--height` | GIF 高度 | `60` |
| `--green-screen` | 启用去绿幕 | `False` |
| `--green-threshold` | 绿幕阈值 0-255 | `150` |

## 技术原理

### 工作流程

1. **获取视频信息**：使用 `ffprobe` 获取视频时长、宽度和高度
2. **生成滤镜链**：根据参数生成 FFmpeg `drawbox` 滤镜
3. **处理视频**：使用 FFmpeg 应用滤镜并输出新视频

### FFmpeg 滤镜实现

使用两个 `drawbox` 滤镜叠加实现双层进度条效果：

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

#### 完整示例

```bash
-vf "drawbox=y=ih-5:color=0x808080:w=iw:h=5:t=fill,drawbox=y=ih-5:color=0xFF0000:w='iw*t/60.5':h=5:t=fill"
```

### 音频处理

使用 `-c:a copy` 参数直接复制音频流，避免重新编码，提高处理速度。

## 常见问题

### FFmpeg 未找到

**错误信息：** `ffprobe not found. Please ensure FFmpeg is installed and ffprobe is in PATH.`

**解决方法：**
- 安装 FFmpeg：https://ffmpeg.org/download.html
- 确保 `ffmpeg` 和 `ffprobe` 命令在系统 PATH 中

### 输入文件不存在

**错误信息：** `Input video file not found: <path>`

**解决方法：** 检查文件路径是否正确

### 视频格式不支持

**错误信息：** `No video stream found in the input file`

**解决方法：** 确保输入文件是有效的视频文件

### 颜色格式错误

颜色参数应为 6 位十六进制数字（不含 #），例如：
- ✅ `FF0000`（红色）
- ✅ `00FF00`（绿色）
- ❌ `#FF0000`（不要包含 #）
- ❌ `red`（不要使用颜色名称）

## 项目结构

```
vpbar/
├── vpbar/                       # 核心模块
│   ├── cli.py                   # CLI 入口与子命令（main(argv) → int）
│   ├── __main__.py              # python -m vpbar 入口
│   ├── config.py                # 样式配置加载与合并
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
├── tests/                       # 测试
│   ├── test_cli.py              # CLI 单元测试（44 个）
│   ├── test_pure.py             # 纯函数单元测试（52 个）
│   ├── test_integration.py      # 集成测试（7 个，opt-in）
│   └── fixtures/                # 测试用视频/字幕
├── .streamlit/                  # Streamlit 配置
├── models/                      # Whisper/FunASR 模型缓存
├── styles.json                  # 33 种进度条样式定义
├── scrubbers/                   # 87 种 GIF 拖拽头模板
├── fonts/                       # 字体文件
├── pyproject.toml               # 项目配置与依赖
├── BENCHMARKS.md                # 性能基准数据
├── README.md                    # 快速入门（本文档）
└── gui.bat                      # Windows 一键启动 GUI
```

## 开发 & 测试

### 运行测试

```bash
# 单元测试（96 个，1.2s）
pytest tests/ -v

# 集成测试（需要 ffmpeg）
pytest tests/ -v --integration

# 指定模块
pytest tests/test_cli.py -v
pytest tests/test_pure.py -v -k "test_parse_chapters"
```

### 测试架构

- **单元测试**（默认）— mock 掉所有外部依赖，纯逻辑验证
- **集成测试**（`--integration`）— 需要 ffmpeg 和真实视频文件
