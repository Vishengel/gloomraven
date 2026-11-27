from pathlib import Path


def write_text_atomically(path: Path, text: str) -> None:
    """Write to a temporary file first, so a crash halfway never leaves a half-written file behind."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(".tmp")
    temporary_path.write_text(text, encoding="utf-8")
    temporary_path.replace(path)
