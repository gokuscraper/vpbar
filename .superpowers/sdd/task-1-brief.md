### Task 1: SRT 文件解析模块

**Files:**
- Create: `vpbar/srt.py`

**Produces:**
- `parse_srt(path: str) -> tuple[list[dict], float]`
  - 返回值: `([{index, start_sec, end_sec, text}, ...], total_duration_sec)`

**Steps:**

- [ ] **Step 1: 创建 `vpbar/srt.py`，写入 `parse_srt` 函数**

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

- [ ] **Step 2: 测试验证**

```powershell
python -c "from vpbar.srt import parse_srt; e, d = parse_srt('6月27日.srt'); print(f'{len(e)} entries, {d:.1f}s')"
```

期望输出：`271 entries, 471.1s`（或类似，取决于 SRT 最后时间）

- [ ] **Step 3: 处理边界：空文件、格式错误、UTF-8 BOM**

`parse_srt` 已用 `utf-8-sig` 处理 BOM，空文件会触发 `ValueError`。无需额外改动。

- [ ] **Step 4: Commit**

```bash
git add vpbar/srt.py
git commit -m "feat: add SRT file parser"
```
