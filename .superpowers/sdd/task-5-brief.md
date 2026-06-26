### Task 5: Extract `chapters.py`

**Files:**
- Create: `vpbar/chapters.py`

**Interfaces:**
- Produces: `parse_chapters(chapter_str: str | None) -> list[dict] | None`

- [ ] **Step 1: Create `vpbar/chapters.py`**

```python
"""Chapter string parsing."""


def parse_chapters(chapter_str: str | None) -> list[dict] | None:
    """Parse chapter string like '0-6:Intro,6-11:结尾' into list of dicts."""
    if not chapter_str:
        return None
    chapters = []
    for part in chapter_str.split(','):
        parts = part.strip().split(':')
        if len(parts) == 2:
            time_range, label = parts
            start, end = time_range.split('-')
            chapters.append({
                'start': float(start),
                'end': float(end),
                'label': label.strip()
            })
    return chapters if chapters else None
```

- [ ] **Step 2: Verify**

```bash
python -c "from vpbar.chapters import parse_chapters; print('ok')"
```

- [ ] **Step 3: Commit**

```bash
git add vpbar/chapters.py
git commit -m "feat: extract chapter parsing into vpbar/chapters.py"
```
