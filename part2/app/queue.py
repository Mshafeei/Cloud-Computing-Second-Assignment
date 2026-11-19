import fcntl
import os
import tempfile
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
    lock_path = p.parent / "queue.lock"

    with open(lock_path, "a+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            existing = []
            if p.exists():
                existing = [
                    line for line in p.read_text(encoding="utf-8").splitlines() if line
                ]

            with p.open("a", encoding="utf-8") as f:
                f.write(f"{cleaned}\n")

            return len(existing) + 1
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def take(path: str | Path) -> str:
    """Remove and return the first name."""
    p = Path(path)
    if not p.parent.exists():
        raise LookupError("Queue file does not exist")

    lock_path = p.parent / "queue.lock"

    with open(lock_path, "a+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            if not p.exists():
                raise LookupError("Queue file does not exist")

            lines = [
                line for line in p.read_text(encoding="utf-8").splitlines() if line
            ]
            if not lines:
                raise LookupError("Queue is empty")

            first, rest = lines[0], lines[1:]

            tmp_fd, tmp_name = tempfile.mkstemp(dir=p.parent, text=True)
            try:
                with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmp_file:
                    tmp_file.writelines(f"{line}\n" for line in rest)
                os.replace(tmp_name, p)
            except Exception:
                if os.path.exists(tmp_name):
                    os.unlink(tmp_name)
                raise

            return first
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)