import re

def strip_markdown_json(raw: str) -> str:
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if match:
        return match.group(1).strip()
    return raw.strip()