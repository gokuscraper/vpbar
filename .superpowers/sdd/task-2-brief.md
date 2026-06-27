### Task 2: LLM API 调用模块

**Files:**
- Create: `vpbar/llm.py`
- Modify: `pyproject.toml`（加 openai 依赖）

**Produces:**
- `call_llm(system_prompt: str, user_content: str) -> str | None`
- `parse_llm_json(response: str) -> list[dict] | None`

**Steps:**

- [ ] **Step 1: 创建 `vpbar/llm.py`**

```python
import json
import os
import re

from openai import OpenAI

API_BASE = "https://opencode.ai/zen/v1"
MODEL = "deepseek-v4-flash-free"
TIMEOUT = 30
MAX_RETRIES = 2


def _get_api_key() -> str:
    key = os.environ.get("OPENCODE_API_KEY", "")
    if not key:
        raise RuntimeError(
            "OPENCODE_API_KEY not set. "
            "Run: \$env:OPENCODE_API_KEY='sk-...'"
        )
    return key


def call_llm(system_prompt: str, user_content: str) -> str | None:
    key = _get_api_key()
    client = OpenAI(api_key=key, base_url=API_BASE, timeout=TIMEOUT)
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.3,
            )
            return resp.choices[0].message.content
        except Exception as e:
            if attempt < MAX_RETRIES:
                continue
            print(f"LLM API error after {MAX_RETRIES+1} attempts: {e}", file=__import__('sys').stderr)
            return None
    return None


def parse_llm_json(response: str) -> list[dict] | None:
    text = response.strip()
    if text.startswith("```"):
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, list):
        return None
    for item in data:
        if not isinstance(item, dict):
            return None
        if 'start' not in item or 'end' not in item or 'label' not in item:
            return None
        if not isinstance(item['start'], (int, float)):
            return None
        if not isinstance(item['end'], (int, float)):
            return None
        if not isinstance(item['label'], str):
            return None
        if item['start'] >= item['end']:
            return None
    return data
```

- [ ] **Step 2: 修改 `pyproject.toml`**

在 `dependencies` 中追加 `"openai>=1.0.0"`。

- [ ] **Step 3: 测试 API 调用**

```powershell
\$env:OPENCODE_API_KEY = "sk-7VXEMHbHvk56xtJiQ6EzHO3jaqVX0eEqfbLs2PBV0Yp1I9Z18nRGoD71EWFYwx7R"
python -c "from vpbar.llm import call_llm, parse_llm_json; r=call_llm('Say hello in Chinese', 'Reply'); print(r)"
```

期望：打印 `你好` 或类似的 LLM 回复。

- [ ] **Step 4: 测试 JSON 解析**

```powershell
python -c "from vpbar.llm import parse_llm_json; d=parse_llm_json('[{\"start\":0,\"end\":10,\"label\":\"test\"}]'); print(d)"
```

期望：`[{'start': 0, 'end': 10, 'label': 'test'}]`

- [ ] **Step 5: Commit**

```bash
git add vpbar/llm.py pyproject.toml
git commit -m "feat: add LLM API caller and JSON parser"
```
