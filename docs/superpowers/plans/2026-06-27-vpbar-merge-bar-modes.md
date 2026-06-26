# 方角圆角模式统一实现计划

> **For agentic workers:** Use superpowers:subagent-driven-development to implement task-by-task.

**目标:** 将 `build_square_command` 和 `build_rounded_command` 合并为一个 `build_bar_command`，支持所有功能的双模式（方角/圆角），使拖拽头和梯度在方角模式下也正常工作。

**架构:** 删除 drawbox 方案，统一走 Pillow 生成 PNG + overlay 路线。corner_radius=0 即方角，>0 即圆角。image.py 的 `create_rounded_rect` 和 `create_gradient_bar` 传 radius=0 即为方角。

**技术栈:** Python 3.8+, FFmpeg, Pillow (变为必需)

## 全局约束

- 不修改 `config.py`、`styles.json`、`scrubber.py`、`video.py`、`fonts.py`
- 不修改 `gif.py`、`cli.py`（它们不关心方角还是圆角）
- `vpbar/__main__.py` 不变
- 所有已有命令行参数不变
- Pillow 变为必需依赖（`pyproject.toml` 中从 optional 移入 `dependencies`）

---

### Task 1: 合并 build_square_command 和 build_rounded_command

**Files:**
- Modify: `vpbar/ffmpeg.py`（全部重写，只保留一个函数）
- Modify: `vpbar/progress.py:54-64`（调用方式）
- Modify: `pyproject.toml`（Pillow 移入必需依赖）

**旧接口（删除）:**
- `build_square_command(input_path, output_path, position, height, video_info, bg_color, fg_color, bg_alpha, fg_alpha, segment_interval, chapters, divider_width, divider_height_ratio)`
- `build_rounded_command(input_path, output_path, position, height, video_info, bg_color, fg_color, bg_alpha, fg_alpha, segment_interval, corner_radius, chapters, divider_width, divider_height_ratio, gradient, scrubber_image)`

**新接口:**
```python
def build_bar_command(
    input_path: str, output_path: str, position: str, height: int,
    video_info: dict,
    bg_color: str = "000000", fg_color: str = "ff0000",
    bg_alpha: float = 0.7, fg_alpha: float = 1.0,
    segment_interval: int = 2,
    corner_radius: int = 0,
    chapters: list = None,
    divider_width: int = 3, divider_height_ratio: float = 0.8,
    gradient: list = None, scrubber_image: str = None
) -> tuple:
```

**实现要点:**

- `corner_radius=0` 即原方角模式，`corner_radius>0` 即原圆角模式
- bg bar: `create_rounded_rect(width, height, bg_color, bg_alpha, corner_radius, bg_img_path)`
- progress 段：`create_rounded_rect(...)` 或 `create_gradient_bar(..., radius=corner_radius)` — 两函数均已接受 radius 参数
- overlay 链结构（沿用 `build_rounded_command` 现有方案）：
  ```
  [0:v][1:v]overlay=y={bar_y}:x=0[v0]
  [v0][2:v]overlay=y={bar_y}:x=0:enable='between(t,{t0},{t1})'[v1]
  ...
  ```
- 拖拽头：同 `build_rounded_command` 逻辑（`get_gif_info` → `calculate_loop_count` → `scale` → `overlay`）
- 章节线/文字：同 `build_rounded_command` 逻辑（FFmpeg drawbox/drawtext 在 overlay 链后追加）
- 返回 `(cmd, None)`，用内联 `-filter_complex`，不再写 filter 文件

**vbar/progress.py 修改:**
```python
# 删除 PIL_AVAILABLE 判断
cmd, filter_file = build_bar_command(
    input_path=input_path, output_path=output_path,
    position=position, height=height,
    bg_color=bg_color, fg_color=fg_color,
    bg_alpha=bg_alpha, fg_alpha=fg_alpha,
    segment_interval=segment_interval,
    corner_radius=corner_radius,
    chapters=chapters, divider_width=divider_width,
    divider_height_ratio=divider_height_ratio,
    gradient=gradient, scrubber_image=scrubber_image,
    video_info=video_info
)
```

**pyproject.toml 修改:**
```toml
dependencies = [
    "Pillow>=10.0.0",
]
```
（删除 `[project.optional-dependencies]` 中的 Pillow 条目）

- [ ] **Step 1: 重写 `vpbar/ffmpeg.py`，删除两个旧函数，写入一个 `build_bar_command`**

将合并后的代码写入 `vpbar/ffmpeg.py`. 保留 import 部分（继续导入 image.py/fonts.py/scrubber.py 的函数），删除全部旧逻辑，写入新函数。

- [ ] **Step 2: 修改 `vpbar/progress.py` 调用方式**

`add_progress_bar` 函数中删除 `use_rounded` 分支，直接调用 `build_bar_command(corner_radius=corner_radius, gradient=gradient, scrubber_image=scrubber_image, ...)`。

- [ ] **Step 3: 修改 `pyproject.toml` 依赖**

Pillow 从 optional → required。

- [ ] **Step 4: 冒烟测试**

```powershell
# 方角 + 拖拽头
Remove-Item -LiteralPath test_outputs -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path test_outputs -Force | Out-Null

python -m vpbar progress add 1.mkv `
  --style 经典红 --corner-radius 0 --position bottom `
  --scrubber-image scrubbers/gif/bongo-cat-pixel.gif `
  --chapters "0-4:前奏,4-8:高潮,8-11:尾声" `
  -o test_outputs/01_bottom.mkv

python -m vpbar progress add 1.mkv `
  --style 经典红 --corner-radius 0 --position middle `
  --scrubber-image scrubbers/gif/bongo-cat-pixel.gif `
  --chapters "0-4:前奏,4-8:高潮,8-11:尾声" `
  -o test_outputs/02_middle.mkv

python -m vpbar progress add 1.mkv `
  --style 经典红 --corner-radius 0 --position top `
  --scrubber-image scrubbers/gif/bongo-cat-pixel.gif `
  --chapters "0-4:前奏,4-8:高潮,8-11:尾声" `
  -o test_outputs/03_top.mkv

# 验证
Get-ChildItem test_outputs/*.mkv | % {
  $dur = ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $_.FullName
  "$($_.Name): ${dur}s"
}
```

期望：三个文件均可播放，进度条在对应位置，拖拽头（bongo cat）可见，章节线/文字正常。

- [ ] **Step 5: 梯度 + 方角 + 拖拽头 交叉测试**

```powershell
python -m vpbar progress add 1.mkv `
  --style 彩虹 --corner-radius 0 --position bottom `
  --scrubber-image scrubbers/gif/bongo-cat-pixel.gif `
  --chapters "0-4:前奏,4-8:高潮,8-11:尾声" `
  -o test_outputs/04_rainbow_square.mkv
```
期望：方角进度条，渐变色正常，拖拽头正常。

- [ ] **Step 6: 圆角模式回归测试**

```powershell
python -m vpbar progress add 1.mkv `
  --style 经典红 --corner-radius 15 --position bottom `
  --scrubber-image scrubbers/gif/bongo-cat-pixel.gif `
  --chapters "0-4:前奏,4-8:高潮,8-11:尾声" `
  -o test_outputs/05_rounded.mkv
```
期望：与重构前效果一致（圆角 + 拖拽头 + 章节）。

---
