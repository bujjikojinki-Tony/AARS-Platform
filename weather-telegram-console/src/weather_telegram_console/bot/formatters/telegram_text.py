from __future__ import annotations


def safe_text(value: object) -> str:
    if value is None:
        return "-"
    text = str(value).replace("\r", " ").replace("\n", " ").strip()
    if not text:
        return "-"
    return text.replace("`", "'")


def md_code(value: object) -> str:
    return f"`{safe_text(value)}`"


def md_line(label: str, value: object) -> str:
    return f"*{safe_text(label)}:* {md_code(value)}"
