# Task 9 Report: Extract `progress.py`

**Status:** Done
**Commit SHA:** 22e2467

Created `vpbar/progress.py` with the `add_progress_bar()` function that orchestrates the progress bar workflow:
- Validates input file existence
- Retrieves video info via `get_video_info`
- Routes to `build_rounded_command` or `build_square_command` based on corner_radius and PIL availability
- Executes FFmpeg and handles cleanup/errors
