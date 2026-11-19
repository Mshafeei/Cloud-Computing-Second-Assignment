"""Queue stored as one name per line.

The HTTP server must call these functions. Tests call them directly,
with a temporary directory, and do not start Docker.
"""

from __future__ import annotations

from pathlib import Path


def join(path: str | Path, name: str) -> int:
    """Append one person and return the ticket number."""
    if "\n" in name or "\r" in name:
        raise ValueError("Name must not contain a newline")
    cleaned = name.strip()
    if not cleaned or len(cleaned) > 40:
        raise ValueError("Name must be between 1 and 40 characters")

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    existing = []
    if p.exists():
        existing = [line for line in p.read_text(encoding="utf-8").splitlines() if line]

    with p.open("a", encoding="utf-8") as f:
        f.write(f"{cleaned}\n")

    return len(existing) + 1


def take(path: str | Path) -> str:
    """Remove and return the first name."""
    p = Path(path)
    if not p.exists():
        raise LookupError("Queue file does not exist")

    lines = [line for line in p.read_text(encoding="utf-8").splitlines() if line]
    if not lines:
        raise LookupError("Queue is empty")

    first, rest = lines[0], lines[1:]
    p.write_text("".join(f"{line}\n" for line in rest), encoding="utf-8")
    return first
