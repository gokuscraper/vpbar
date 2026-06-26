# Task 8 Report: Extract ffmpeg.py

**Status:** Completed

**Commit:** `0ed597e` - feat: extract FFmpeg command generation into vpbar/ffmpeg.py

**Files created:**
- `vpbar/ffmpeg.py` — contains `build_square_command()` and `build_rounded_command()` functions

**Verification:** `python -c "from vpbar.ffmpeg import build_square_command, build_rounded_command; print('ok')"` → ok
