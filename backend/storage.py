"""Persistent paths and crash-safe writes."""
import os
import re
import tempfile
from pathlib import Path

def data_root() -> Path:
    root = Path(os.environ.get("R8D_DATA_DIR", str(Path(__file__).parent / "data")))
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()

def safe_component(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}", value):
        raise ValueError("Invalid identifier")
    return value

def atomic_write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".write-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)
