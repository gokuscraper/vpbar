### Task 4: CLI — chapters generate 子命令 + --srt 参数

**Files:**
- Modify: `vpbar/cli.py`

**Interfaces:**
- Consumes: `generate_chapters_from_srt(srt_path, min_chapters, max_chapters, max_label_length) -> str | None` from `vpbar.chapters`
- Consumes: `parse_chapters(chapter_str) -> list[dict] | None` from `vpbar.chapters`

**Changes:**

#### 1. 新增 `build_chapters_subparser`

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

#### 2. 修改 `build_progress_subparser` — 加 `--srt` 参数

在 `add_parser.add_argument("--scrubber-image"...` 之后加上：

```python
add_parser.add_argument("--srt", type=str, default=None, help="SRT subtitle file for auto-chaptering")
```

#### 3. 修改 `main()` — 注册 `chapters` 子命令

```python
subparsers = parser.add_subparsers(dest="command", required=True)
build_progress_subparser(subparsers)
build_gif_subparser(subparsers)
build_chapters_subparser(subparsers)  # 新增
```

#### 4. 修改 `main()` — 处理 `chapters generate`

在 `if args.command == "progress"` 之前（或 elif 链中）添加：

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

#### 5. 修改 `progress add` 分支 — 支持 `--srt` 自动分章节

现有代码：
```python
chapters = parse_chapters(args.chapters)
```

改为：
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

**Steps:**

- [ ] **Step 1: 编辑 `vpbar/cli.py`**，应用上述 5 处改动

- [ ] **Step 2: 测试 chapters generate**

```powershell
$env:OPENCODE_API_KEY = "sk-7VXEMHbHvk56xtJiQ6EzHO3jaqVX0eEqfbLs2PBV0Yp1I9Z18nRGoD71EWFYwx7R"
python -m vpbar chapters generate --srt 6月27日.srt
```

期望：输出 `0.0-33.3:回应质疑,33.3-170.7:流量为王,170.7-471.1:多号实战` 或类似的章节字符串

- [ ] **Step 3: 测试 chapters generate -o**

```powershell
python -m vpbar chapters generate --srt 6月27日.srt -o test_outputs/chapters.txt
Get-Content test_outputs/chapters.txt
```

期望：文件内容与上一步输出一致

- [ ] **Step 4: 测试 progress add --srt**

```powershell
python -m vpbar progress add 竖屏测试.mp4 --srt 6月27日.srt --style 小A --corner-radius 15 --position bottom --scrubber-image scrubbers/gif/bongo-cat-pixel.gif --height 35 -o test_outputs\竖屏_AI分章.mkv
```

期望：视频生成成功，进度条上显示 AI 分的章节

- [ ] **Step 5: 测试 --chapters 优先于 --srt**

```powershell
python -m vpbar progress add 竖屏测试.mp4 --srt 6月27日.srt --chapters "0-100:手动,100-472:覆盖" ...
```

期望：使用手动传入的章节，不调 LLM

- [ ] **Step 6: Commit**

```bash
git add vpbar/cli.py
git commit -m "feat: add chapters generate subcommand and --srt flag"
```
