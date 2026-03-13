"""
Layer 1 — Ingestion.
V1: manual upload only; creates Inquiry Record and stores raw artifacts.
"""
from __future__ import annotations

import hashlib
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def inquiry_id() -> str:
    return str(uuid4())[:8]


def save_upload(file_content: bytes, filename: str, inquiry_id_param: Optional[str] = None) -> str:
    """Save uploaded file; create inquiry dir if needed. Returns inquiry_id."""
    iid = inquiry_id_param or inquiry_id()
    dest_dir = UPLOAD_DIR / iid
    dest_dir.mkdir(parents=True, exist_ok=True)
    safe_name = os.path.basename(filename) or "document"
    dest_path = dest_dir / safe_name
    dest_path.write_bytes(file_content)
    return iid


def get_inquiry_dir(iid: str) -> Path:
    return UPLOAD_DIR / iid


def list_inquiry_files(iid: str) -> list[dict]:
    """List stored artifacts for an inquiry (name, path, size)."""
    d = get_inquiry_dir(iid)
    if not d.exists():
        return []
    out = []
    for f in d.iterdir():
        if f.is_file():
            out.append({"name": f.name, "path": str(f), "size": f.stat().st_size})
    return out


def get_inquiry_record(iid: str) -> dict:
    """Return minimal inquiry record for downstream layers."""
    files = list_inquiry_files(iid)
    return {
        "inquiry_id": iid,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "artifacts": [{"name": f["name"], "size": f["size"]} for f in files],
        "paths": [f["path"] for f in files],
    }
