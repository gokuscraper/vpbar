# vpbar · Video Progress Bar Generator

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) [![Python](https://img.shields.io/badge/Python-3.8+-brightgreen)]() [![Tests](https://img.shields.io/badge/Tests-96%20passed-brightgreen)]() [![CLI](https://img.shields.io/badge/CLI-yt--dlp%20style-blue)]() [![GUI](https://img.shields.io/badge/GUI-Streamlit-red)]()

Add Douyin-style dual-layer animated progress bars to videos. Supports FunASR / Whisper dual-engine transcription, AI chapter generation, 33 styles, 87 GIF scrubbers, and a Streamlit GUI.

**Read this in:** [中文](README.md)

## ✅ When to use / ❌ When not to

| Use for | Not for |
|---------|---------|
| Batch progress bars on videos | Video editing (render-only tool) |
| Chapter markers for long videos | Real-time video streams |
| AI speech-to-text + chapter gen | Replacing watermarks/subtitles |
| GIF scrubber animations | Non-standard formats |

## 🚀 Quick Start

```bash
# One-command full pipeline
vpbar progress add input.mp4 --transcribe --engine funasr --style 小A
```

### Install

```bash
cd L:\vpbar
pip install -e .
# Then `vpbar` is available globally. Or double-click gui.bat for the GUI.
```

### Step by step

```bash
# Transcribe → chapters → render
vpbar transcribe input.mp4 -o subtitle.srt --engine funasr
vpbar chapters generate --srt subtitle.srt
vpbar progress add input.mp4 --style 小A --chapters "0-50:Intro,50-168:Core"
```

## 🎨 Engine Choice

| Engine | Speed | Key Traits | Best for |
|--------|-------|-----------|----------|
| **FunASR** ✅ | 5× realtime | Punctuation, 200M, CPU-only | Chinese, long videos, **default** |
| Whisper | 1.7× realtime | Multilingual, 1.5B, GPU recommended | Multilingual content |

## Docs

| File | Contents |
|------|----------|
| [`GUIDE.md`](GUIDE.md) | Full command reference, tech details, FAQ, project structure, tests |
| [`BENCHMARKS.md`](BENCHMARKS.md) | Engine comparison, LLM chapter quality, end-to-end timing, render perf |
| [`README.md`](README.md) | 中文版本 |

## License

MIT © 2026 · Built on [FFmpeg](https://ffmpeg.org/)
