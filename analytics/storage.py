from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Protocol

class ObjectStorage(Protocol):
    def put_file(self, path: Path, key: str, sha256: str) -> str: ...

class LocalObjectStorage:
    """Filesystem sink used by tests; objects are immutable by content hash."""
    def __init__(self, root: str | Path): self.root = Path(root)
    def put_file(self, path: Path, key: str, sha256: str) -> str:
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != sha256: raise ValueError("object_hash_mismatch")
        target = self.root / key
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.read_bytes() != raw: raise ValueError("immutable_object_collision")
        if not target.exists(): target.write_bytes(raw)
        return f"file://{target.resolve()}"
