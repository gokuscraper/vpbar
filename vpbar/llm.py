import json
import os
import re

from openai import OpenAI

API_BASE = "https://opencode.ai/zen/v1"
MODEL = "deepseek-v4-flash-free"
TIMEOUT = 120
MAX_RETRIES = 2


def _get_api_key() -> str:
    key = os.environ.get("OPENCODE_API_KEY", "")
    if not key:
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        if os.path.isfile(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("OPENCODE_API_KEY="):
                        key = line.split("=", 1)[1].strip().strip("\"'")
                        break
    if not key:
        raise RuntimeError(
            "OPENCODE_API_KEY not set. "
            "Create a .env file with OPENCODE_API_KEY=sk-... in project root, "
            "or run: $env:OPENCODE_API_KEY='sk-...'"
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
