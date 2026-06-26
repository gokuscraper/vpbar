# 视频进度条 CLI 工具设计文档

## 1. 概述

一个 Python CLI 工具，使用 FFmpeg 给视频添加双层进度条（底层静态 + 上层动态），类似抖音的进度条效果。

## 2. 功能需求

### 2.1 核心功能
- 给视频添加双层进度条
  - 底层：静态灰色条，表示总时长
  - 上层：动态红色条，随视频播放进度增长
- 进度条位置可配置（顶部/底部）
- 进度条高度可配置

### 2.2 输入输出
- 输入：单个视频文件（支持常见格式：mp4, mov, avi, mkv 等）
- 输出：添加进度条后的视频文件
  - 默认输出路径：原文件名 + `_with_progress` 后缀
  - 可通过参数指定输出路径

## 3. 技术方案

### 3.1 技术栈
- **语言**：Python 3.8+
- **核心依赖**：FFmpeg（系统已安装）
- **Python 库**：
  - `argparse`：命令行参数解析
  - `subprocess`：调用 FFmpeg 命令
  - `json`：解析 FFprobe 输出

### 3.2 实现原理
使用 FFmpeg 滤镜链在视频上绘制进度条：

1. **获取视频信息**：用 FFprobe 获取视频时长、分辨率
2. **绘制底层条**：用 `drawbox` 滤镜绘制静态灰色条
3. **绘制上层条**：用 `drawbox` 滤镜 + `enable` 表达式绘制动态进度条
4. **合成输出**：FFmpeg 处理并输出新视频

### 3.3 FFmpeg 滤镜示例
```
drawbox=y=ih-h:color=gray@1:w=iw:h=5:t=fill,
drawbox=y=ih-h:color=red@1:w=iw*t/duration:h=5:t=fill:enable='lte(t,duration)'
```

## 4. 命令行接口

### 4.1 基本用法
```bash
python add_progress_bar.py input.mp4
```

### 4.2 完整参数
```bash
python add_progress_bar.py input.mp4 \
  -o output.mp4 \
  --position bottom \
  --height 5 \
  --bg-color 808080 \
  --fg-color FF0000
```

### 4.3 参数说明
| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| input | - | 输入视频文件路径 | 必需 |
| --output | -o | 输出视频文件路径 | input_with_progress.ext |
| --position | -p | 进度条位置（top/bottom） | bottom |
| --height | -h | 进度条高度（像素） | 5 |
| --bg-color | -bg | 底层颜色（十六进制） | 808080（灰色） |
| --fg-color | -fg | 上层颜色（十六进制） | FF0000（红色） |

## 5. 文件结构

```
L:\视频进度条\
├── add_progress_bar.py    # 主脚本
├── README.md              # 使用说明
├── requirements.txt       # Python 依赖（可选，仅文档作用）
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-06-23-video-progress-bar-design.md
```

## 6. 错误处理

- 检查 FFmpeg 是否安装
- 检查输入文件是否存在
- 检查输入文件是否为有效视频
- 检查输出路径是否可写
- FFmpeg 执行失败时显示错误信息

## 7. 测试计划

- 测试不同格式视频（mp4, mov, avi）
- 测试不同分辨率视频
- 测试顶部和底部位置
- 测试不同进度条高度
- 测试自定义颜色

## 8. 未来扩展（可选）

- 批量处理目录
- 进度条圆角效果
- 进度条渐变色
- 显示时间文字
- 多主题配置
