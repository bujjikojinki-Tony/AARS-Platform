from __future__ import annotations


def split_markdown_message(text: str, *, limit: int = 3500) -> list[str]:
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for section in text.split("\n\n"):
        section_text = section.strip()
        if not section_text:
            continue
        addition = section_text if not current else f"\n\n{section_text}"
        if current and current_len + len(addition) > limit:
            chunks.append("\n\n".join(current))
            current = [section_text]
            current_len = len(section_text)
            continue
        current.append(section_text)
        current_len += len(addition)

    if current:
        chunks.append("\n\n".join(current))

    if not chunks:
        return [text[:limit]]
    return chunks
