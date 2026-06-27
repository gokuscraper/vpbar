# Task 1 Report: SRT 文件解析模块

## Implementation
Created `vpbar/srt.py` with `parse_srt(path: str) -> tuple[list, float]` function.

## Test Results
```
272 entries, 471.1s
```
- Duration matches expected (471.1s)
- Entry count is 272 vs expected ~271 (the file contains 272 valid entries, all parsed correctly)
- All indices 1-272 present, no gaps, no empty text entries

## Self-Review
1. ✅ **`,` and `.` separator**: Regex uses `[,.]` group, supporting both SRT (`,`) and alternative (`.`) formats
2. ✅ **UTF-8 BOM**: Handled via `utf-8-sig` encoding
3. ✅ **Malformed entries**: `try/except (ValueError, IndexError): continue` skips gracefully
4. ✅ **Regex groups**: All 8 groups extracted correctly via `match.group(1,2,3,4)` and `match.group(5,6,7,8)`
5. ✅ **Edge cases**: Empty file / no valid entries raises `ValueError("No valid SRT entries found")`

## Concerns
- Entry count is 272 instead of the brief's approximate "271" — the file genuinely has 272 valid entries, so the parser is correct
