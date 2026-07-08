# vpbar · 视频进度条生成器

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) [![Python](https://img.shields.io/badge/Python-3.8+-brightgreen)]() [![Tests](https://img.shields.io/badge/Tests-96%20passed-brightgreen)]() [![CLI](https://img.shields.io/badge/CLI-yt--dlp%20style-blue)]() [![GUI](https://img.shields.io/badge/GUI-Streamlit-red)]()

一键给视频添加抖音风格的双层动态进度条。支持 FunASR / Whisper 双引擎转写、AI 自动分章、33 种样式、87 种 GIF 拖拽头、Streamlit GUI。

**English version:** [README.en.md](README.en.md)

## ✅ 适合 / ❌ 不适合

| 适合 | 不适合 |
|------|--------|
| 短视频批量加进度条 | 视频剪辑（这是渲染工具） |
| 长视频加章节提升完播率 | 实时视频流处理 |
| AI 语音转写 + 自动分章 | 替换水印或字幕 |
| GIF 动效拖拽头 | 非主流格式 |

## 🚀 在线使用

无需安装，浏览器打开即可：

**[👉 vpbar7.streamlit.app](https://vpbar7.streamlit.app/)**

上传视频 → 选引擎 → 等结果，全在网页上完成。

## 🚀 快速开始（本地 CLI）

```bash
# 一键全流程
vpbar progress add input.mp4 --transcribe --engine funasr --style 小A
```

### 安装

```bash
cd L:\vpbar
pip install -e .
# 然后 vpbar 命令全局可用，或双击 gui.bat 启动 GUI
```

### 分步

```bash
# 转写 → 分章 → 渲染
vpbar transcribe input.mp4 -o subtitle.srt --engine funasr
vpbar chapters generate --srt subtitle.srt
vpbar progress add input.mp4 --style 小A --chapters "0-50:介绍,50-168:核心"
```

## 🎨 引擎选择

| 引擎 | 速度 | 特点 | 推荐场景 |
|------|------|------|---------|
| **FunASR** ✅ | 5× 实时率 | 有标点、200M、纯 CPU 可用 | 中文、长视频、首选 |
| Whisper | 1.7× 实时率 | 多语言、1.5B、推荐 GPU | 多语言视频 |

## 文档

| 文件 | 内容 |
|------|------|
| [`GUIDE.md`](GUIDE.md) | 完整命令参数表、技术原理、FAQ、项目结构、测试 |
| [`BENCHMARKS.md`](BENCHMARKS.md) | 引擎对比、LLM 分章效果、全流程耗时、渲染性能 |
| [`README.en.md`](README.en.md) | English version |

## License

MIT © 2026 · Built on [FFmpeg](https://ffmpeg.org/)
