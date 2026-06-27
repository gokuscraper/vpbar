# AI 自动分章节实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add AI-powered chapter generation from SRT subtitle files, with two usage modes.

**Architecture:** Three additions — `srt.py` (SRT parsing), `llm.py` (OpenCode API), and extending `chapters.py` (orchestration). CLI gets a new `chapters generate` subcommand and `--srt` flag on `progress add`.

**Tech Stack:** Python 3.8+, `openai` library, DeepSeek V4 Flash Free API

## Global Constraints

- API Key from env var `OPENCODE_API_KEY`
- Chapters: min 2, max 4, name ≤5 chars
- Output format matches `--chapters` syntax: `"0-120:开场,120-300:实战"`
- `openai>=1.0.0` added to `pyproject.toml`
- Don't delete or rename existing modules
- `--chapters` flag on `progress add` takes priority over `--srt`

---
### Task 1: SRT 文件解析模块

**Files:**
- Create: `vpbar/srt.py`

**Produces:**
- `parse_srt(path: str) -> tuple[list[dict], float]`
  - 返回值: `([{index, start_sec, end_sec, text}, ...], total_duration_sec)`

**Steps:**

- [ ] Step 1: 创建 `vpbar/srt.py`，写入 `parse_srt` 函数

```python
import re

def parse_srt(path: str) -> tuple[list, float]:
    with open(path, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    blocks = re.split(r'\n\n+', content.strip())
    entries = []
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        try:
            time_line = lines[1]
            match = re.match(
                r'(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})',
                time_line
            )
            if not match:
                continue
            def to_sec(h, m, s, ms):
                return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000
            start_sec = to_sec(*match.group(1,2,3,4))
            end_sec = to_sec(*match.group(5,6,7,8))
            text = '\n'.join(lines[2:])
            entries.append({
                'index': int(lines[0]),
                'start_sec': start_sec,
                'end_sec': end_sec,
                'text': text.strip()
            })
        except (ValueError, IndexError):
            continue
    if not entries:
        raise ValueError("No valid SRT entries found")
    total_duration = entries[-1]['end_sec']
    return entries, total_duration
```

- [ ] Step 2: 测试验证

```powershell
python -c "from vpbar.srt import parse_srt; e, d = parse_srt('6月27日.srt'); print(f'{len(e)} entries, {d:.1f}s')"
```

期望输出：`271 entries, 471.1s`（或类似，取决于 SRT 最后时间）

- [ ] Step 3: 处理边界：空文件、格式错误、UTF-8 BOM

`parse_srt` 已用 `utf-8-sig` 处理 BOM，空文件会触发 `ValueError`。无需额外改动。

- [ ] Step 4: Commit

```bash
git add vpbar/srt.py
git commit -m "feat: add SRT file parser"
```

---

### Task 2: LLM API 调用模块

**Files:**
- Create: `vpbar/llm.py`
- Modify: `pyproject.toml`（加 openai 依赖）

**Produces:**
- `call_llm(system_prompt: str, user_content: str) -> str | None`
- `parse_llm_json(response: str) -> list[dict] | None`

**Steps:**

- [ ] Step 1: 创建 `vpbar/llm.py`，写入 `call_llm` 和 `parse_llm_json`

```python
import json
import os

from openai import OpenAI

API_BASE = "https://opencode.ai/zen/v1"
MODEL = "deepseek-v4-flash-free"
TIMEOUT = 30
MAX_RETRIES = 2


def _get_api_key() -> str:
    key = os.environ.get("OPENCODE_API_KEY", "")
    if not key:
        raise RuntimeError(
            "OPENCODE_API_KEY not set. "
            "Run: $env:OPENCODE_API_KEY='sk-...'"
        )
    return key


def call_llm(system_prompt: str, user_content: str) -> str | None:
    key = _get_api_key()
    client = OpenAI(api_key=key, base_url=API_BASE, timeout=TIMEOUT)
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.3,
            )
            return resp.choices[0].message.content
        except Exception as e:
            if attempt < MAX_RETRIES:
                continue
            print(f"LLM API error after {MAX_RETRIES+1} attempts: {e}", file=__import__('sys').stderr)
            return None
    return None


def parse_llm_json(response: str) -> list[dict] | None:
    text = response.strip()
    if text.startswith("```"):
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, list):
        return None
    for item in data:
        if not isinstance(item, dict):
            return None
        if 'start' not in item or 'end' not in item or 'label' not in item:
            return None
        if not isinstance(item['start'], (int, float)):
            return None
        if not isinstance(item['end'], (int, float)):
            return None
        if not isinstance(item['label'], str):
            return None
        if item['start'] >= item['end']:
            return None
    return data
```

需要 import re：

```python
import re
```

- [ ] Step 2: 修改 `pyproject.toml`

在 `dependencies` 中追加 `"openai>=1.0.0"`。

- [ ] Step 3: 测试 API 调用

```powershell
$env:OPENCODE_API_KEY = "sk-7VXEMHbHvk56xtJiQ6EzHO3jaqVX0eEqfbLs2PBV0Yp1I9Z18nRGoD71EWFYwx7R"
python -c "from vpbar.llm import call_llm, parse_llm_json; r=call_llm('Say hello in Chinese', 'Reply'); print(r)"
```

期望：打印 `你好` 或类似的 LLM 回复。

- [ ] Step 4: 测试 JSON 解析

```powershell
python -c "from vpbar.llm import parse_llm_json; d=parse_llm_json('[{\"start\":0,\"end\":10,\"label\":\"test\"}]'); print(d)"
```

期望：`[{'start': 0, 'end': 10, 'label': 'test'}]`

- [ ] Step 5: Commit

```bash
git add vpbar/llm.py pyproject.toml
git commit -m "feat: add LLM API caller and JSON parser"
```

---

### Task 3: 编排层 — srt + LLM → 章节字符串

**Files:**
- Modify: `vpbar/chapters.py`（追加 `generate_chapters_from_srt`）

**Interfaces:**
- Consumes: `parse_srt` from Task 1, `call_llm` / `parse_llm_json` from Task 2
- Produces: `generate_chapters_from_srt(srt_path, min_chapters=2, max_chapters=4, max_label_length=5) -> str | None`

**Steps:**

- [ ] Step 1: 读取现有 `vpbar/chapters.py`

```python
# vpbar/chapters.py 当前内容
```

确认现有函数和导入，然后在文件末尾追加新函数。

- [ ] Step 2: 在 `chapters.py` 末尾追加 `generate_chapters_from_srt`

```python
def generate_chapters_from_srt(
    srt_path: str,
    min_chapters: int = 2,
    max_chapters: int = 4,
    max_label_length: int = 5,
) -> str | None:
    from vpbar.srt import parse_srt
    from vpbar.llm import call_llm, parse_llm_json

    entries, duration = parse_srt(srt_path)
    subtitle_lines = "\n".join(
        f"{e['start_sec']:.1f} → {e['end_sec']:.1f} : {e['text']}"
        for e in entries
    )
    user_content = f"字幕内容如下（每行格式：开始时间 → 结束时间 : 文本）：\n\n{subtitle_lines}\n\n视频总时长：{duration:.1f} 秒"

    system_prompt = (
        "你是一个视频章节分析助手。根据用户提供的字幕内容（含时间戳），\n"
        f"将视频内容分成 {min_chapters} 到 {max_chapters} 个章节。\n\n"
        "要求：\n"
        f"- 每个章节起一个简短的名称（1-{max_label_length} 个字），\n"
        "  使用与字幕相同的语言，概括该段落的核心内容\n"
        "- 章节之间的边界要合理，不要打断一个完整的论述或句子\n"
        "- 第一个章节从 0 秒开始，最后一个章节到视频结束\n"
        "- 只返回 JSON 数组，不要多余的文字或解释\n\n"
        "JSON 格式：\n"
        '[\n'
        '  {"start": 0, "end": 108.5, "label": "开场"},\n'
        '  {"start": 108.5, "end": 300.0, "label": "实战"}\n'
        "]\n\n"
        "其中 start 和 end 为浮点数秒，label 为字符串。"
    )

    raw = call_llm(system_prompt, user_content)
    if raw is None:
        return None

    data = parse_llm_json(raw)
    if data is None:
        return None

    chapters_str = ",".join(
        f"{c['start']:.1f}-{c['end']:.1f}:{c['label']}"
        for c in data
    )
    return chapters_str
```

- [ ] Step 3: 测试完整流程

```powershell
$env:OPENCODE_API_KEY = "sk-..."
python -c "from vpbar.chapters import generate_chapters_from_srt; r=generate_chapters_from_srt('6月27日.srt'); print(r)"
```

期望：输出类似 `0.0-120.0:开场,120.0-300.0:实战,300.0-472.0:总结`

- [ ] Step 4: 处理 LLM 返回 None 的情况（API 失败）

无需额外代码——调用方检查 `None` 即可。

- [ ] Step 5: Commit

```bash
git add vpbar/chapters.py
git commit -m "feat: add AI chapter generation from SRT"
```

---

### Task 4: CLI — chapters generate 子命令 + --srt 参数

**Files:**
- Modify: `vpbar/cli.py`

**Interfaces:**
- Consumes: `generate_chapters_from_srt` from Task 3
- `chapters generate --srt 字幕.srt [-o output] [--min-chapters 2] [--max-chapters 4]`
- `progress add ... --srt 字幕.srt`

**Steps:**

- [ ] Step 1: 在 `cli.py` 中新增 `build_chapters_subparser`

```python
def build_chapters_subparser(subparsers):
    parser = subparsers.add_parser("chapters", help="Chapter operations")
    sub = parser.add_subparsers(dest="action", required=True)
    gen_parser = sub.add_parser("generate", help="Generate chapters from SRT using AI")
    gen_parser.add_argument("--srt", type=str, required=True, help="SRT subtitle file path")
    gen_parser.add_argument("-o", "--output", type=str, default=None, help="Save chapters to file")
    gen_parser.add_argument("--min-chapters", type=int, default=2, help="Minimum chapters")
    gen_parser.add_argument("--max-chapters", type=int, default=4, help="Maximum chapters")
    gen_parser.add_argument("--max-label-length", type=int, default=5, help="Max label characters")
    return gen_parser
```

- [ ] Step 2: 在 `progress add` 中加 `--srt` 参数

```python
add_parser.add_argument("--srt", type=str, default=None, help="SRT subtitle file for auto-chaptering")
```

- [ ] Step 3: 在 `main()` 中处理 `chapters generate`

```python
if args.command == "chapters":
    if args.action == "generate":
        from vpbar.chapters import generate_chapters_from_srt
        result = generate_chapters_from_srt(
            srt_path=args.srt,
            min_chapters=args.min_chapters,
            max_chapters=args.max_chapters,
            max_label_length=args.max_label_length,
        )
        if result is None:
            print("Failed to generate chapters", file=sys.stderr)
            sys.exit(1)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result)
            print(f"Chapters saved to: {args.output}")
        else:
            print(result)
        sys.exit(0)
```

- [ ] Step 4: 在 `progress add` 分支中处理 `--srt`

在 `progress add` 分支中，在调用 `add_progress_bar` 之前：

```python
chapters_str = args.chapters
if chapters_str is None and args.srt:
    from vpbar.chapters import generate_chapters_from_srt
    result = generate_chapters_from_srt(srt_path=args.srt)
    if result:
        chapters_str = result
        print(f"Auto-generated chapters: {result}")
    else:
        print("Warning: Failed to auto-generate chapters, proceeding without chapters", file=sys.stderr)
chapters = parse_chapters(chapters_str)
```

---


- [ ] Step 5: 测试 chapters generate

```powershell
$env:OPENCODE_API_KEY = "sk-..."
python -m vpbar chapters generate --srt 6月27日.srt
```

期望：输出自动分好的章节字符串。

- [ ] Step 6: 测试 chapters generate -o

```powershell
python -m vpbar chapters generate --srt 6月27日.srt -o test_outputs/chapters.txt
Get-Content test_outputs/chapters.txt
```

期望：文件内容与上一步输出一致。

- [ ] Step 7: 测试 progress add --srt

```powershell
python -m vpbar progress add 竖屏测试.mp4 --srt 6月27日.srt --style 小A --corner-radius 15 --position bottom --scrubber-image scrubbers/gif/bongo-cat-pixel.gif --height 35 -o test_outputs\竖屏_AI分章.mkv
```

期望：视频生成成功，进度条上显示 AI 分的章节。

- [ ] Step 8: Commit

```bash
git add vpbar/cli.py
git commit -m "feat: add chapters generate subcommand and --srt flag"
```

---

### Task 5: progress.py — --srt 支持接入

**Files:**
- Modify: `vpbar/progress.py`

实际上 `cli.py` 中已经处理了 `--srt` → `generate_chapters_from_srt` → `parse_chapters` 的逻辑，`progress.py` 本身不需要改动。如果希望 `progress.py` 也支持独立调用（被外部调用时传 SRT），可以加一个 `srt_path` 参数。

- [ ] Step 1: 给 `add_progress_bar` 加 `srt_path` 参数

```python
def add_progress_bar(
    ...,
    srt_path: str = None,
    ...
) -> bool:
```

在获取 `video_info` 之后，`build_bar_command` 之前：

```python
if srt_path and chapters is None:
    from vpbar.chapters import generate_chapters_from_srt
    result = generate_chapters_from_srt(srt_path=srt_path)
    if result:
        chapters = parse_chapters(result)
        print(f"Auto-generated chapters: {result}")
    else:
        print("Warning: Failed to auto-generate chapters", file=sys.stderr)
```

并把 `srt_path=srt_path` 加入参数传递——但 `build_bar_command` 不需要它，只需确保 `chapters` 变量已赋值。

- [ ] Step 2: 更新 `cli.py` 中调用 `add_progress_bar` 时传入 `srt_path`

```python
success = add_progress_bar(
    ...
    srt_path=args.srt,
    chapters=chapters,  # 已经是 parse_chapters 后的结果
)
```

注意：此时 `chapters` 已经在 cli.py 中解析好了（Task 4 Step 4），所以实际上 `progress.py` 不需要再做 SRT 处理。`progress.py` 加 `srt_path` 参数只是为了将来被其他代码直接调用时方便。如果 YAGNI，可以跳过这一步。

**建议：跳过这一步。** cli.py 已经处理了 SRT → chapters 的转换，保持了 `progress.py` 的纯粹性。

- [ ] Step 3: 确认整体流程正常

重新运行 Task 4 Step 7 测试，确保一切正常。

---
