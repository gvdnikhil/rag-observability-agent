import re
from pathlib import Path


def chunk_text(text: str, max_words: int = 120) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks = []
    for p in paragraphs:
        words = p.split()
        if len(words) <= max_words:
            chunks.append(p)
            continue
        for i in range(0, len(words), max_words):
            chunks.append(" ".join(words[i : i + max_words]))
    return chunks


def load_docs(docs_dir: Path) -> list[dict]:
    chunks = []
    for path in sorted(docs_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for i, chunk in enumerate(chunk_text(text)):
            chunks.append({"id": f"{path.stem}-{i}", "text": chunk, "source": path.name})
    return chunks
