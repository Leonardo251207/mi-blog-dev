import hashlib
from pathlib import Path
from typing import Tuple

def calculate_sha256(data: bytes) -> str:
    hasher = hashlib.sha256()
    hasher.update(data)
    return hasher.hexdigest()

def save_bytes(path: Path, data: bytes) -> Tuple[int, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    sha = calculate_sha256(data)
    return len(data), sha

def read_bytes(path: Path) -> bytes:
    with open(path, "rb") as f:
        return f.read()

def verify_file_integrity(path: Path, expected_sha: str) -> bool:
    if not path.is_file():
        return False
    data = read_bytes(path)
    actual_sha = calculate_sha256(data)
    return actual_sha == expected_sha
