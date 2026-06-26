# Task 1 Report: 合并 build_square_command 和 build_rounded_command

## 实现内容

### 修改文件

1. **`vpbar/ffmpeg.py`** — 完全重写
   - 删除 `build_square_command` 和 `build_rounded_command` 两个旧函数
   - 写入单一的 `build_bar_command` 函数，通过 `corner_radius=0`（方角）/ `corner_radius>0`（圆角）统一处理
   - 始终使用 Pillow PNG + overlay 方式（不再使用 drawbox 滤镜）
   - 返回 `(cmd, None)`，使用内联 `-filter_complex`，不再写 filter 文件
   - 支持所有参数：bg/fg color/alpha、segments、corner_radius、chapters（drawbox/drawtext）、gradient、scrubber
   - 移除了不再需要的 `create_rounded_bar_with_text` import

2. **`vpbar/progress.py`** — 简化
   - 删除 `PIL_AVAILABLE` 检测块（lines 10-14）
   - 删除 `use_rounded` 分支判断（line 40-64）
   - 直接调用 `build_bar_command`，传入所有参数
   - import 从 `build_square_command, build_rounded_command` 改为 `build_bar_command`

3. **`pyproject.toml`** — 依赖变更
   - `dependencies` 从空列表改为 `["Pillow>=10.0.0"]`
   - Pillow 从可选依赖变为必需依赖

### 未修改文件
   - `vpbar/image.py` — 不变（`create_rounded_rect`, `create_gradient_bar` 等函数保留，它们均已接受 radius 参数）
   - 其他辅助模块不变

## 测试结果

使用 `1.mkv`（11.02s, 1920x1080）进行测试，5 个场景全部通过：

| 测试 | 位置 | corner_radius | 样式 | 拖拽头 | 章节 | 时长 |
|------|------|---------------|------|--------|------|------|
| 01_bottom | bottom | 0 | 经典红 | bongo-cat-pixel | 前奏/高潮/尾声 | 11.034s ✓ |
| 02_middle | middle | 0 | 经典红 | bongo-cat-pixel | 前奏/高潮/尾声 | 11.034s ✓ |
| 03_top | top | 0 | 经典红 | bongo-cat-pixel | 前奏/高潮/尾声 | 11.034s ✓ |
| 04_rainbow_square | bottom | 0 | 彩虹(渐变) | bongo-cat-pixel | 前奏/高潮/尾声 | 11.034s ✓ |
| 05_rounded | bottom | 15 | 经典红 | bongo-cat-pixel | 前奏/高潮/尾声 | 11.034s ✓ |

所有输出均可正常播放，时长正确，进度条位置正确，拖拽头和章节正常。

## 自审

- `build_bar_command` 完全沿用了 `build_rounded_command` 的 overlay 链结构和章节处理逻辑
- `corner_radius=0` 时 `create_rounded_rect` 创建的是平角矩形，效果等价于原 `build_square_command`
- bg bar 使用 `create_rounded_rect` 替代原来的 `create_rounded_bar_with_text(..., draw_text=False)`，更简洁
- 移除了写入 filter 文件的逻辑（原 `build_square_command` 的 `filter_script` 方式），全部使用内联 `-filter_complex`
- 临时目录清理逻辑未变（仅在 `progress.py` 中尝试删除 `filter_file`，现在 `filter_file` 始终为 `None`，该分支只是跳过）

## 问题与风险

无。所有测试通过，功能完整。
