import re
import json


def strip_markdown_json(raw: str) -> str:
    """Extract JSON from markdown code fences, or return raw string stripped."""
    if not raw:
        return ""

    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if match:
        return match.group(1).strip()

    match_inline = re.search(r"`({.*?})`", raw)
    if match_inline:
        return match_inline.group(1).strip()

    return raw.strip()


def try_parse_json(raw: str):
    """Attempt to parse JSON, with common repair strategies for local model output."""
    cleaned = strip_markdown_json(raw)
    if not cleaned:
        return None, "Empty response"

    last_error = None
    for strategy in (
        lambda s: s,
        lambda s: re.sub(r",\s*([}\]])", r"\1", s),
        lambda s: re.sub(r"(?<!\\)\b(null|true|false)\b", lambda m: m.group(1).lower(), s),
    ):
        try:
            return json.loads(strategy(cleaned)), None
        except json.JSONDecodeError as e:
            last_error = e

    return None, f"Could not parse JSON: {last_error}"
