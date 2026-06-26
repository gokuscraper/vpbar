### Task 7: Extract `image.py`

**Files:**
- Create: `vpbar/image.py`

**Interfaces:**
- Produces: `create_rounded_rect(...)`, `create_gradient_bar(...)`, `create_rounded_bar_with_text(...)` (same signatures as original)

- [ ] **Step 1: Create `vpbar/image.py`**

Copy the three Pillow functions from `add_progress_bar.py`, changing the `prepare_fonts()` import to `from vpbar.fonts import prepare_fonts`.

```python
"""Pillow image generation for rounded corners, gradients, and chapter text."""

from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from vpbar.fonts import prepare_fonts


def create_rounded_rect(width: int, height: int, color: str, alpha: float, radius: int, output_path: str):
    if not PIL_AVAILABLE:
        raise ImportError("PIL/Pillow is required for rounded corners. Install with: pip install Pillow")
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)
    a = int(alpha * 255)
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, width - 1, height - 1], radius=radius, fill=(r, g, b, a))
    img.save(output_path, 'PNG')


def create_gradient_bar(width: int, height: int, colors: list, alpha: float = 1.0, radius: int = 0, output_path: str = None):
    if not PIL_AVAILABLE:
        raise ImportError("PIL/Pillow is required for gradient bars")
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rgb_colors = []
    for color in colors:
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        rgb_colors.append((r, g, b, int(alpha * 255)))
    num_segments = len(rgb_colors)
    segment_width = width // num_segments
    for i, color in enumerate(rgb_colors):
        x_start = i * segment_width
        x_end = (i + 1) * segment_width if i < num_segments - 1 else width
        if i < num_segments - 1:
            next_color = rgb_colors[i + 1]
            for x in range(x_start, x_end):
                ratio = (x - x_start) / (x_end - x_start)
                r = int(color[0] + (next_color[0] - color[0]) * ratio)
                g = int(color[1] + (next_color[1] - color[1]) * ratio)
                b = int(color[2] + (next_color[2] - color[2]) * ratio)
                a_val = int(color[3] + (next_color[3] - color[3]) * ratio)
                draw.line([(x, 0), (x, height - 1)], fill=(r, g, b, a_val))
        else:
            draw.rectangle([x_start, 0, x_end, height - 1], fill=color)
    if radius > 0:
        mask = Image.new('L', (width, height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([0, 0, width - 1, height - 1], radius=radius, fill=255)
        img.putalpha(mask)
    if output_path:
        img.save(output_path, 'PNG')
    return img


def create_rounded_bar_with_text(
    width: int, height: int, color: str, alpha: float, radius: int,
    output_path: str, chapters: list = None, duration: float = None,
    divider_width: int = 3, divider_height_ratio: float = 0.8, draw_text: bool = True
):
    if not PIL_AVAILABLE:
        raise ImportError("PIL/Pillow is required for rounded corners")
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)
    a = int(alpha * 255)
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, width - 1, height - 1], radius=radius, fill=(r, g, b, a))
    if chapters and duration:
        divider_height = int(height * divider_height_ratio)
        divider_y_offset = (height - divider_height) // 2
        font_size = max(10, int(height * 0.5))
        font_paths = prepare_fonts()
        has_chinese = any('\u4e00' <= char <= '\u9fff' for chapter in chapters if chapter.get('label') for char in chapter['label'])
        if has_chinese and 'chinese' in font_paths:
            font_path = font_paths['chinese']
        elif 'english' in font_paths:
            font_path = font_paths['english']
        else:
            font_path = Path("C:/Windows/Fonts/msyh.ttc")
        try:
            font = ImageFont.truetype(str(font_path), font_size)
        except:
            font = ImageFont.load_default()
        for i, chapter in enumerate(chapters[:-1]):
            divider_x = int(width * (chapter['end'] / duration))
            draw.rectangle(
                [divider_x - divider_width // 2, divider_y_offset,
                 divider_x + divider_width // 2, divider_y_offset + divider_height],
                fill=(0, 0, 0, 255)
            )
        if draw_text:
            for chapter in chapters:
                if not chapter.get('label'):
                    continue
                mid_time = (chapter['start'] + chapter['end']) / 2
                text_x = int(width * (mid_time / duration))
                draw.text((text_x, height // 2), chapter['label'], fill=(0, 0, 0, 255), font=font, anchor='mm')
    img.save(output_path, 'PNG')
```

- [ ] **Step 2: Verify**

```bash
python -c "from vpbar.image import create_rounded_rect, create_gradient_bar, create_rounded_bar_with_text; print('ok')"
```

- [ ] **Step 3: Commit**

```bash
git add vpbar/image.py
git commit -m "feat: extract Pillow image generation into vpbar/image.py"
```
