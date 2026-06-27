# Task 2 Report: LLM API 调用模块

## What I implemented

- Created `vpbar/llm.py` with `call_llm()`, `parse_llm_json()`, and `_get_api_key()`
- Updated `pyproject.toml` to add `"openai>=1.0.0"` to dependencies

## Test Results

**LLM API call test:**
```
PS> $env:OPENCODE_API_KEY = "sk-7VXEMHbHvk56xtJiQ6EzHO3jaqVX0eEqfbLs2PBV0Yp1I9Z18nRGoD71EWFYwx7R"
PS> python -c "from vpbar.llm import call_llm, parse_llm_json; r=call_llm('Say hello in Chinese', 'Reply'); print(r)"
你好
```
API returned a Chinese greeting successfully.

**JSON parsing test:**
```
[{'start': 0, 'end': 10, 'label': 'test'}]  ← OK
```
All edge cases passed (markdown fences, start>=end, missing keys, non-list input).

## Self-review

- `call_llm` handles API errors with retry (max 2 retries, catches Exception, prints to stderr on final failure)
- `parse_llm_json` strips markdown code fences (` ```json `) before parsing
- `_get_api_key` raises a clear `RuntimeError` with instructions when key is missing
- `pyproject.toml` correctly comma-separates `"openai>=1.0.0"` in the dependencies list

## Concerns

None.
