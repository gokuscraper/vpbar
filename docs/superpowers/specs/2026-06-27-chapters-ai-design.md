# AI 自动分章节设计文档

**版本:** v1
**日期:** 2026-06-27

---

## 1. 概述

利用大模型（DeepSeek V4 Flash Free）根据 SRT 字幕文件自动为视频分章节，支持两种使用模式：

1. **模式A — 先分章后微调：** `vpbar chapters generate --srt 字幕.srt` 输出章节字符串到终端或文件，用户可手动编辑后再传入 `--chapters`
2. **模式B — 一步到位：** `vpbar progress add video.mp4 --srt 字幕.srt` 内部自动分章节并直接加进度条

两种模式共享同一套 LLM 分章节逻辑。

---

## 2. CLI 接口

### 模式A: chapters generate 子命令

```bash
vpbar chapters generate --srt 字幕.srt [-o 输出文件] [--min-chapters 2] [--max-chapters 4]
```

| 参数 | 默认 | 说明 |
|------|------|------|
| `--srt` | 必填 | SRT 字幕文件路径 |
| `-o, --output` | 无（输出到终端） | 保存章节字符串到文件 |
| `--min-chapters` | 2 | 最少章节数 |
| `--max-chapters` | 4 | 最多章节数 |
| `--max-label-length` | 5 | 章节名最大字数 |

输出格式：`0-108:开场,108-300:实战,300-472:总结`（与 `--chapters` 参数兼容）

### 模式B: progress add 扩展 --srt

```bash
vpbar progress add video.mp4 --srt 字幕.srt --style 小A ...
```

| 参数 | 说明 |
|------|------|
| `--srt` | SRT 字幕文件路径，自动分章节后再叠加进度条 |
| `--chapters` | 如果同时传了 `--chapters`，则 `--chapters` 优先（手动覆盖自动） |

---

## 3. 模块设计

### vpbar/srt.py — SRT 文件解析

```
parse_srt(path: str) -> tuple[list[dict], float]
```

- 输入：SRT 文件路径
- 输出：(字幕列表, 总时长秒数)
  - 每条字幕：`{index, start_sec, end_sec, text}`
  - 总时长 = 最后一条字幕的 end_sec
- 标准 SRT 格式：序号 → `HH:MM:SS,mmm --> HH:MM:SS,mmm` → 文本 → 空行
- 容错：跳过格式异常的行，能处理空行不一致

### vpbar/llm.py — LLM API 调用

```
call_llm(system_prompt: str, user_content: str) -> str | None
```

- 使用 `openai` 库，`base_url="https://opencode.ai/zen/v1"`
- API Key 从环境变量 `OPENCODE_API_KEY` 读取
- 模型：`deepseek-v4-flash-free`
- 超时：120 秒（大 SRT 文件需要更长时间）
- 重试：最多 2 次
- 返回：LLM 回复的原始文本，或 None（全部失败时）

```
parse_llm_json(response: str) -> list[dict] | None
```

- 去掉 markdown 代码块标记（` ```json ` 等）
- `json.loads` 解析
- 验证每个元素包含 `start`（数字）、`end`（数字）、`label`（字符串）
- 验证 start < end
- 失败返回 None

### vpbar/chapters.py（扩展）— 分章节编排

```
generate_chapters_from_srt(srt_path: str, min_chapters=2, max_chapters=4, max_label_length=5) -> str | None
```

- 调 `parse_srt` 获取字幕和时长
- 构建用户消息：包含时间戳的字幕全文
- 构建系统提示词（见下文）
- 调 `call_llm`
- 调 `parse_llm_json`
- 将 JSON 转为 `"0-108:开场,108-300:实战,300-472:总结"` 格式
- 返回章节字符串，或 None

### vpbar/progress.py（改动）— --srt 支持

- 如果传了 `--srt` 且没有传 `--chapters`，调 `generate_chapters_from_srt`
- 如果 LLM 返回 None，打印警告，不加章节继续

### vpbar/cli.py（改动）— 注册 chapters 子命令 + --srt 参数

- 新增 `chapters generate` 子命令
- `progress add` 加 `--srt` 参数

---

## 4. 提示词设计

### 系统提示词

```
你是一个视频章节分析助手。根据用户提供的字幕内容（含时间戳），
将视频内容分成 {min_chapters} 到 {max_chapters} 个章节。

要求：
- 每个章节起一个简短的名称（1-{max_label_length} 个字），
  使用与字幕相同的语言，概括该段落的核心内容
- 章节之间的边界要合理，不要打断一个完整的论述或句子
- 第一个章节从 0 秒开始，最后一个章节到视频结束
- 只返回 JSON 数组，不要多余的文字或解释

JSON 格式：
[
  {"start": 0, "end": 108.5, "label": "开场"},
  {"start": 108.5, "end": 300.0, "label": "实战"}
]

其中 start 和 end 为浮点数秒，label 为字符串。
```

### 用户消息

```
字幕内容如下（每行格式：开始时间 → 结束时间 : 文本）：

0.0 → 2.0 : hello大家好
2.0 → 3.5 : 上期视频
3.5 → 5.0 : 我简单介绍一下
...
视频总时长：472.0 秒
```

---

## 5. 错误处理

| 情况 | 处理方式 |
|------|----------|
| `OPENCODE_API_KEY` 未设置 | 打印错误，返回 None |
| SRT 文件不存在 | 报错退出 |
| SRT 格式解析失败 | 报错退出 |
| LLM API 超时/返回空 | 重试 2 次，全部失败则打印警告，返回 None |
| LLM 返回非 JSON | 重试 1 次，仍失败则打印警告，返回 None |
| JSON 结构不完整 | 重试 1 次，仍失败则打印警告，返回 None |

---

## 6. 依赖

新增 Python 依赖：

| 包 | 用途 |
|----|------|
| `openai>=1.0.0` | LLM API 调用 |

对应修改 `pyproject.toml`。

---

## 7. 后续扩展

- **语音转文字模式：** `vpbar progress add video.mp4 --transcribe` — 调用 Whisper 等本地 STT 引擎，转写后再走同一套 LLM 分章节逻辑
- **更多 LLM 提供商：** 在 `llm.py` 中增加 fallback 链（如 SiliconFlow），类似 悟空项目的设计
