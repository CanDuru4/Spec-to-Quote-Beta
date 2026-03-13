"""
Layer 2 — Document parsing.
Extract text, tables, metadata from PDFs, images, Excel, email bodies.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional


def read_pdf(path: str | Path) -> str:
    """Extract text from PDF using PyPDF2."""
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        return f"[PDF not parsed: install PyPDF2] File: {path}"
    path = Path(path)
    if not path.exists():
        return ""
    try:
        reader = PdfReader(path)
        parts = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                parts.append(t)
        return "\n\n".join(parts) or f"[No text extracted from PDF] {path.name}"
    except Exception as e:
        return f"[PDF error: {e}] File: {path}"


def read_docx(path: str | Path) -> str:
    """Extract text from Word document."""
    try:
        from docx import Document
    except ImportError:
        return f"[DOCX not parsed: install python-docx] File: {path}"
    path = Path(path)
    if not path.exists():
        return ""
    try:
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs) or f"[No text in DOCX] {path.name}"
    except Exception as e:
        return f"[DOCX error: {e}] File: {path}"


def read_excel(path: str | Path) -> str:
    """Extract text from first sheet of Excel file."""
    try:
        import openpyxl
    except ImportError:
        return f"[Excel not parsed: install openpyxl] File: {path}"
    path = Path(path)
    if not path.exists():
        return ""
    try:
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.active
        if not ws:
            return f"[Empty workbook] {path.name}"
        rows = []
        for row in ws.iter_rows(values_only=True):
            row_str = "\t".join(str(c) if c is not None else "" for c in row)
            if row_str.strip():
                rows.append(row_str)
        wb.close()
        return "\n".join(rows) or f"[No data in sheet] {path.name}"
    except Exception as e:
        return f"[Excel error: {e}] File: {path}"


def read_image_text(path: str | Path) -> str:
    """Placeholder: OCR for images. Optional dependency (pytesseract)."""
    # Could add pytesseract + pdf2image for image-heavy PDFs
    return f"[Image file: no OCR in V1] {Path(path).name}"


def parse_document(path: str | Path) -> str:
    """Dispatch by extension and return extracted text."""
    path = Path(path)
    suf = path.suffix.lower()
    if suf == ".pdf":
        return read_pdf(path)
    if suf in (".docx", ".doc"):
        return read_docx(path)
    if suf in (".xlsx", ".xls"):
        return read_excel(path)
    if suf in (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"):
        return read_image_text(path)
    if suf == ".txt":
        return path.read_text(encoding="utf-8", errors="replace")
    if suf == ".eml" or ".eml" in path.name:
        return path.read_text(encoding="utf-8", errors="replace")
    # Default: try text
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return f"[Unsupported format] {path.name}"


def parse_inquiry_record(record: dict) -> dict:
    """Parse all artifacts in an inquiry record. Add 'combined_text' and per-file 'text'."""
    paths = record.get("paths") or []
    combined = []
    file_texts = []
    for p in paths:
        text = parse_document(p)
        combined.append(text)
        file_texts.append({"path": p, "text": text[:5000]})  # cap per file for context
    record["combined_text"] = "\n\n---\n\n".join(combined)
    record["file_texts"] = file_texts
    return record
