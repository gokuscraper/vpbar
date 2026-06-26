### Task 2: Extract `config.py`

**Files:**
- Create: `vpbar/config.py`

**Interfaces:**
- Consumes: `config.json`, `styles.json` (file paths relative to project root)
- Produces: `load_config() -> dict`, `load_styles() -> dict`, `merge_with_style(cli_args: dict, style_name: str) -> dict`

- [ ] **Step 1: Create `vpbar/config.py`**

```python
"""Configuration loading from config.json and styles.json."""

import json
import sys
from pathlib import Path


def load_config() -> dict:
    config_path = Path(__file__).parent.parent / "config.json"
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load config file: {e}", file=sys.stderr)
    return {
        "position": "bottom",
        "height": 5,
        "bg_color": "808080",
        "fg_color": "FF0000",
        "segment_interval": 1
    }


def load_styles() -> dict:
    styles_path = Path(__file__).parent.parent / "styles.json"
    if styles_path.exists():
        try:
            with open(styles_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load styles file: {e}", file=sys.stderr)
    return {
        "styles": {
            "默认": {
                "bg_color": "808080",
                "bg_alpha": 1.0,
                "fg_color": "FF0000",
                "fg_alpha": 1.0,
                "height": 5,
                "position": "bottom"
            }
        },
        "default_style": "默认",
        "segment_interval": 1
    }


def merge_with_style(cli_args: dict, style_name: str, styles_config: dict) -> dict:
    """Merge CLI args with style config. CLI args override style values."""
    styles = styles_config.get("styles", {})
    style_config = styles.get(style_name, {})
    merged = {}
    for key in ("position", "height", "bg_color", "fg_color", "bg_alpha", "fg_alpha", "corner_radius"):
        merged[key] = cli_args.get(key) if cli_args.get(key) is not None else style_config.get(key)
    # handle gradient separately
    if cli_args.get("gradient"):
        merged["gradient"] = cli_args["gradient"]
    elif "gradient" in style_config:
        merged["gradient"] = style_config["gradient"]
    return merged
```

- [ ] **Step 2: Verify the module loads**

```bash
python -c "from vpbar.config import load_config, load_styles, merge_with_style; print('ok')"
```

- [ ] **Step 3: Commit**

```bash
git add vpbar/config.py
git commit -m "feat: extract config loading into vpbar/config.py"
```
