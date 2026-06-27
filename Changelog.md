# Changelog

## 0.5.0 — 2026-06-28

### Added
- 7 integration tests for progress bar rendering and GIF conversion (opt-in with `--integration`)
- Test fixture files: `test.mp4` (175s), `green.mp4` (10s), `test.srt` (72 entries), `scrubber.gif`

### Changed
- Replaced test SRT with actual transcription from `test.mp4`

### Fixed
- ONNX model path in `_get_onnx_model_dir`: removed extra `models/` segment
- `os.makedirs(onnx_dir, exist_ok=True)` added before BPE model copy

## 0.4.0 — 2026-06-27

### Added
- 96-unit test suite covering CLI, pure functions, error handling, and edge cases
- `TestCustomTypes`, `TestHelpAndVersion`, `TestHandlers`, `TestErrorHandling`, `TestValidateOptions`, `TestVersion`
- Test coverage for `parse_hex`, `seconds_to_srt_time`, `calculate_loop_count`, `parse_chapters`, `parse_llm_json`, `merge_with_style`, `parse_srt`

## 0.3.0 — 2026-06-27

### Changed
- Full CLI refactor following yt-dlp architecture:
  - `main(argv=None) -> int` for testability
  - Dict dispatch (`COMMANDS`) instead of if/elif chains
  - Custom argument types: `hex_color`, `gradient_list`, `existing_file`
  - Option groups for `progress add --help`
  - Centralized `validate_options()` 
  - `logging` to stderr for status, `print()` only for data to stdout
  - `try/except` in `main()` with proper exit codes
  - `sys.exit(main())` in `__main__.py`
- Hex color validation centralized to `_parse_hex()` in `image.py`

### Fixed
- Hex color validation: `_parse_hex()` strips `#`, checks length and character set

### Removed
- Dead `hex_no_hash` from `gui_utils.py` and `app.py`

## 0.2.0 — 2026-06-26

### Added
- Streamlit GUI (`vpbar/app.py`) with dual-mode workflow:
  - **Quick mode**: one-click generate with transcribe + chapters + render
  - **Pro mode**: three-step wizard (transcribe → chapters → render)
  - GIF scrubber selector with 87 template GIFs
  - SRT preview and editing
  - Chapter data editor with dynamic rows
  - Style selector with `[圆角]/[方角]` display prefixes
- `gui_utils.py`: `parse_chapters`, `fmt_chapters`, `save_upload`, `list_scrubbers`, `estimate_eta`
- Style display names with `[圆角]/[方角]` prefix based on `corner_radius`
- Download button in result preview area

### Changed
- Pro mode: replaced `st.tabs` with `st.button` step navigation (no `st.segmented_control` in 1.37)
- `fmt_chapters` uses comma separator to match CLI `parse_chapters`
- Slider defaults match style default values
- SRT upload moved from transcribe tab to chapters tab
- FunASR options hidden in pro mode when Whisper not selected

### Fixed
- Download button: passes `open(op, "rb").read()` (bytes) instead of file object
- SRT upload: `save_upload` called before reading content (was empty file)
- Widget key conflicts in pro mode step navigation

## 0.1.0 — 2026-06-25

### Added
- FunASR ONNX transcription engine with VAD + ct-punc punctuation restoration
- Whisper transcription engine (faster-whisper)
- AI chapter generation from SRT via LLM API
- LLM API caller (`vpbar/llm.py`) with JSON response parser
- SRT parser (`vpbar/srt.py`)
- `chapters generate` CLI subcommand
- `--srt` and `--transcribe` flags for `progress add`
- `--compute-type` option for CPU int8 quantization
- `--gradient` option for multi-color progress bars
- Auto segment interval based on video duration
- GPU benchmark data in README

### Changed
- `spec timeout` increased to 120s for LLM API calls
- JSON parse retry on first failure in chapter generation

### Fixed
- Chapter naming prompt: requires coherent phrases, max 7 chars
- Short-segment label length limited to prevent overflow

## 0.0.2 — 2026-06-24

### Added
- CLI entry point with subcommand dispatch (`vpbar progress add`, `vpbar gif convert`)
- Package structure: `pyproject.toml`, `setup.cfg`, modular layout
- Module extraction: `config.py`, `fonts.py`, `video.py`, `chapters.py`, `scrubber.py`, `image.py`, `ffmpeg.py`, `progress.py`, `gif.py`
- Chapter divider lines and text labels
- Rounded corner mode support (both square and rounded progress bars)
- Gradient progress bar with dynamic scrubber overlay
- GIF scrubber with proper scaling, looping, and centering
- Style system with 33 predefined styles from `styles.json`
- Configurable opacity (`--bg-alpha`, `--fg-alpha`)
- Auto fallback for gradient-only styles in `merge_with_style()`
- `config.json` for default parameter extraction
- Benchmark data in README

### Fixed
- Rounded mode respects `--position` parameter (top/middle/bottom)
- Output duration limited to video length in rounded mode
- Scrubber size and alignment fixes
- Progress bar timing: uses `start_time` for width calculation (was 1s off)
- Chapter text and divider rendered on top layer
- GIF ghosting and animation speed issues

## 0.0.1 — 2026-06-23

### Added
- Initial prototype: `add_progress_bar.py` with argparse CLI
- FFmpeg `drawbox`-based dual-layer progress bar (background + foreground)
- `get_video_info()` via ffprobe
- Position (top/bottom), height, color customization
- Audio stream copy without re-encoding
