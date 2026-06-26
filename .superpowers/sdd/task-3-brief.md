### Task 3: Extract `fonts.py`

**Files:**
- Create: `vpbar/fonts.py`

**Interfaces:**
- Produces: `prepare_fonts() -> dict`

- [ ] **Step 1: Create `vpbar/fonts.py`**

```python
"""Font preparation - copy fonts to short ASCII temp path to avoid Chinese path issues."""

import shutil
import tempfile
from pathlib import Path


def prepare_fonts() -> dict:
    temp_font_dir = Path(tempfile.gettempdir()) / "deveco" / "fonts"
    temp_font_dir.mkdir(parents=True, exist_ok=True)
    script_dir = Path(__file__).parent.parent
    project_font_dir = script_dir / "fonts"
    fonts = {
        'chinese': 'SourceHanSansSC-Regular.otf',
        'english': 'Roboto-Regular.ttf',
    }
    font_paths = {}
    for name, font_file in fonts.items():
        src_path = project_font_dir / font_file
        dst_path = temp_font_dir / font_file
        if src_path.exists():
            if not dst_path.exists() or src_path.stat().st_mtime > dst_path.stat().st_mtime:
                shutil.copy2(src_path, dst_path)
            font_paths[name] = dst_path
        elif dst_path.exists():
            font_paths[name] = dst_path
    return font_paths
```

- [ ] **Step 2: Verify**

```bash
python -c "from vpbar.fonts import prepare_fonts; print('ok')"
```

- [ ] **Step 3: Commit**

```bash
git add vpbar/fonts.py
git commit -m "feat: extract font preparation into vpbar/fonts.py"
```
