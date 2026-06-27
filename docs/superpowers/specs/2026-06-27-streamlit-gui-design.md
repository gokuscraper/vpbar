# Streamlit GUI 设计规格

## 目标
为 vpbar CLI 构建一个功能完整的 Streamlit GUI，覆盖 CLI 全部能力，支持两种工作流模式。

## 架构概览

```
app.py (Streamlit 单文件)
├── 快捷模式 (Quick Mode)
│   └── 一键全自动: 上传 → 配置 → ETA → 生成 → 下载
└── 专业模式 (Pro Mode)
    ├── Step ① 转写: 视频 → SRT (可编辑)
    ├── Step ② 章节: SRT → AI 章节 → 手动编辑
    └── Step ③ 渲染: 章节 + 样式 → 成品视频
```

GUI 完全解耦，通过 `subprocess.run` / `Popen` 调用 CLI，不直接导入 CLI 模块。

## 布局

### 全局结构
- **侧边栏 (320px):** 上下文相关的配置参数
- **主区域:**
  - 顶部: 模式切换 Tab (快捷/专业)
  - 中部: 左右并排视频预览 (原始 | 结果)
  - 下部: ETA 展示 + 操作按钮 + 日志 + 结果下载

### Tab 切换
- `st.tabs(["快捷模式", "专业模式"])` 在顶部
- 专业模式内用 `st.tabs(["① 转写", "② 章节", "③ 渲染"])`

### 视频预览
- `st.columns(2)`: 左 = 原始视频 (uploaded), 右 = 结果视频 (生成后)
- 宽度 400px 左右，缩小显示以避免占用过多空间

## 功能模块

### 1. 侧边栏参数

**通用参数 (两种模式共享):**
- 转写引擎: `st.radio("funasr" / "whisper")`
- 输出文件名: `st.text_input`

**快捷模式独有:**
- GIF 拖拽头: `st.checkbox`
- AI 自动分章: `st.checkbox`
- 上传自定义 GIF: `st.file_uploader`
- 上传自定义 SRT: `st.file_uploader`

**专业模式 Step 1 (转写) 独有:**
- Whisper 模型: `st.selectbox("large-v3-turbo", "large-v3", "medium", "small", "base", "tiny")`
- 设备: `st.radio("auto" / "cuda" / "cpu")`
- 计算类型: `st.selectbox("default" / "float16" / "int8")`

**专业模式 Step 2 (章节) 独有:**
- 最小章节数: `st.number_input(2)`
- 最大章节数: `st.number_input(4)`
- 标签最大长度: `st.number_input(7)`

**专业模式 Step 3 (渲染) 独有:**
- 样式: `st.selectbox` (33 种)
- 位置: `st.radio("top" / "middle" / "bottom")`
- 高度: `st.slider(3-50)`
- 背景色: `st.color_picker`
- 前景色: `st.color_picker`
- 背景透明度: `st.slider(0.0-1.0)`
- 前景透明度: `st.slider(0.0-1.0)`
- 圆角: `st.slider(0-25)`
- 分段间隔: `st.number_input`
- 分隔线宽度: `st.number_input`
- 渐变色: `st.text_input` (逗号分隔十六进制)
- GIF 拖拽头 + 上传自定义 GIF
- 关闭 AI 分章 (使用 Step 2 编辑后的章节)

### 2. 快捷模式

**流程:**
1. 用户上传视频 → 保存到 TEMP_DIR
2. `ffprobe` 获取视频时长
3. ETA 计算: `视频时长 × 系数` (系数按引擎/GIF 查基准表)
4. 显示 ETA 在按钮上方
5. 点「一键生成」→ `subprocess.Popen` 调用 `vpbar progress add ...`
6. 实时日志显示在 `st.code` 中
7. 完成后展示结果视频 + 下载按钮

**命令行构造:**
```
vpbar progress add <input> -o <output> --engine <engine> --style <style>
  [--scrubber-image <gif>] [--srt <srt>]
```

### 3. 专业模式

**Step 1 — 转写:**
- 显示原始视频预览
- 用户可选择「上传已有 SRT」或「开始转写」
- 转写后 SRT 内容展示在 `st.text_area` 中，可手动编辑
- 保存到 session_state

**Step 2 — 章节:**
- 基于 Step 1 的 SRT 生成章节
- 点「AI 生成章节」→ 调用 `vpbar chapters generate --srt <srt>`
- 结果解析为 `[{"start": 0, "end": 50, "label": "答质疑"}, ...]`
- 展示在 `st.data_editor` 中，可增删改每行
- 也支持文本区域粘贴章节字符串
- 保存到 session_state

**Step 3 — 渲染:**
- 左右预览 (原始 | 待生成)
- 侧边栏展示所有样式参数
- 点「开始渲染」→ 调用 `vpbar progress add <input> -o <output> --style <style> --chapters <chapters_str>`
- 实时日志 → 结果预览 + 下载

### 4. ETA 估算

**系数表 (基准: 472s/7:52 视频, RTX 3060):**

| 引擎 | GIF | 系数 | 472s 预估 |
|------|-----|------|-----------|
| funasr | 否 | 0.42 | ~3:18 |
| funasr | 是 | 0.49 | ~3:52 |
| whisper | 否 | 0.82 | ~6:26 |
| whisper | 是 | 0.89 | ~7:00 |

**公式:** `ETA(s) = 视频时长(s) × 系数`
- 视频时长通过 `ffprobe` 获取
- 显示文案: `预计处理时间: ~3 分 52 秒`

## 状态管理 (session_state)

| Key | Type | 用途 |
|-----|------|------|
| `video_path` | str | 上传视频的临时路径 |
| `video_duration` | float | 视频时长(秒) |
| `srt_path` | str | SRT 文件路径 |
| `srt_content` | str | SRT 文本内容 (可编辑) |
| `chapters` | list[dict] | `[{start, end, label}]` |
| `output_path` | str | 渲染输出路径 |
| `gif_path` | str | 自定义 GIF 路径 |

## 错误处理

- CLI 返回非零 → 显示错误码 + 日志
- ffprobe 失败 → 显示警告，用文件大小粗估
- SRT 解析失败 → 显示错误提示
- 文件不存在 → 显示 "文件未找到"

## 部署注意事项

- Hugging Face Spaces 兼容: 所有路径用 `TEMP_DIR`
- 文件上传限制: `config.toml` 已设 `maxUploadSize = 500`
- `.env` 文件映射: 需在 HF Spaces Secrets 中设置 API key
