"""
Spec-to-Quote Copilot — FastAPI app.
Routes: upload, process (full pipeline), get packet, clarify email, escalate, export.
"""
from __future__ import annotations

import os
from pathlib import Path

# Load .env from project root so OPENAI_API_KEY etc. are available
_env_file = Path(__file__).resolve().parent.parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            if _k.strip():
                os.environ.setdefault(_k.strip(), _v.strip().strip("'\""))

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Backend modules (run from repo root or backend dir)
try:
    from ingest import save_upload, get_inquiry_record, get_inquiry_dir, list_inquiry_files
    from parse import parse_inquiry_record, parse_document
    from extract import extract_structured
    from retrieve import retrieve_similar_jobs
    from reason import build_reasoning
    from packet import build_packet, packet_to_html, packet_to_pdf
except ImportError:
    # When running as python -m backend.main
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from ingest import save_upload, get_inquiry_record, get_inquiry_dir, list_inquiry_files
    from parse import parse_inquiry_record, parse_document
    from extract import extract_structured
    from retrieve import retrieve_similar_jobs
    from reason import build_reasoning
    from packet import build_packet, packet_to_html, packet_to_pdf

app = FastAPI(title="Spec-to-Quote Copilot", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# In-memory store for packet and edits (V1; use DB in production)
_store: dict[str, dict] = {}
# Human-in-the-loop: feedback log for metrics (corrections, outcomes)
_feedback_log: list[dict] = []


class ProcessResponse(BaseModel):
    inquiry_id: str
    packet: dict
    raw_extracted: dict
    similar_jobs: list


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    """Upload inquiry file(s). V1: single file; returns inquiry_id."""
    content = await file.read()
    iid = save_upload(content, file.filename or "document")
    return {"inquiry_id": iid, "filename": file.filename}


@app.post("/api/process/{inquiry_id}")
async def process(inquiry_id: str) -> ProcessResponse:
    """Run full pipeline: parse -> extract -> retrieve -> reason -> packet."""
    record = get_inquiry_record(inquiry_id)
    if not record.get("paths"):
        raise HTTPException(status_code=400, detail="No files for this inquiry")
    record = parse_inquiry_record(record)
    extracted = extract_structured(record)
    similar_jobs = retrieve_similar_jobs(extracted, top_k=5)
    reasoning = build_reasoning(extracted, similar_jobs, record.get("combined_text", ""))
    packet = build_packet(reasoning)
    _store[inquiry_id] = {
        "packet": packet,
        "reasoning": reasoning,
        "extracted": extracted,
        "similar_jobs": similar_jobs,
        "combined_text": record.get("combined_text", ""),
        "feedback": None,
    }
    return ProcessResponse(
        inquiry_id=inquiry_id,
        packet=packet,
        raw_extracted=extracted,
        similar_jobs=similar_jobs,
    )


@app.get("/api/packet/{inquiry_id}")
async def get_packet(inquiry_id: str):
    """Return stored packet for inquiry."""
    if inquiry_id not in _store:
        raise HTTPException(status_code=404, detail="Packet not found; run process first")
    return _store[inquiry_id]["packet"]


@app.get("/api/parsed/{inquiry_id}")
async def get_parsed(inquiry_id: str):
    """Return parsed text for inquiry (for parsed viewer)."""
    record = get_inquiry_record(inquiry_id)
    if not record.get("paths"):
        raise HTTPException(status_code=404, detail="No files")
    record = parse_inquiry_record(record)
    return {"combined_text": record.get("combined_text", ""), "file_texts": record.get("file_texts", [])}


@app.get("/api/packet/{inquiry_id}/html")
async def get_packet_html(inquiry_id: str) -> HTMLResponse:
    """Return packet as HTML page."""
    if inquiry_id not in _store:
        raise HTTPException(status_code=404, detail="Packet not found")
    html = packet_to_html(_store[inquiry_id]["packet"], inquiry_id)
    return HTMLResponse(html)


@app.get("/api/packet/{inquiry_id}/pdf")
async def get_packet_pdf(inquiry_id: str) -> Response:
    """Download packet as PDF."""
    if inquiry_id not in _store:
        raise HTTPException(status_code=404, detail="Packet not found")
    pdf_bytes = packet_to_pdf(_store[inquiry_id]["packet"], inquiry_id)
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=quote_packet_{inquiry_id}.pdf"})


@app.post("/api/clarify-email/{inquiry_id}")
async def generate_clarify_email(inquiry_id: str):
    """One-click: generate draft customer clarification email."""
    if inquiry_id not in _store:
        raise HTTPException(status_code=404, detail="Packet not found")
    data = _store[inquiry_id]
    packet = data["packet"]
    flags = packet.get("5_risk_missing_info_flags") or []
    checklist = packet.get("6_quote_prep_checklist") or []
    summary = packet.get("1_inquiry_summary") or {}
    customer = summary.get("customer") or "Customer"
    lines = [
        f"Dear {customer},",
        "",
        "Thank you for your inquiry. To prepare an accurate quote, we need to confirm the following:",
        "",
    ]
    for f in flags[:5]:
        lines.append(f"• {f}")
    for c in checklist[:5]:
        lines.append(f"• {c}")
    lines.extend(["", "Please provide the above at your earliest convenience.", "", "Best regards"])
    body = "\n".join(lines)
    return {"subject": "Clarification needed for your coating quote request", "body": body}


@app.post("/api/escalate/{inquiry_id}")
async def escalate(inquiry_id: str):
    """One-click: escalate to technical lead (log only in V1)."""
    if inquiry_id not in _store:
        raise HTTPException(status_code=404, detail="Packet not found")
    # In production: create ticket, notify technical lead
    return {"status": "escalated", "inquiry_id": inquiry_id, "message": "Flagged for technical lead review"}


class FeedbackBody(BaseModel):
    corrections: list[dict] = []  # [{ "field": str, "old_value": str, "new_value": str }]
    outcome: str = "approved"  # approved | rejected | escalated
    notes: str = ""


@app.post("/api/record-feedback/{inquiry_id}")
async def record_feedback(inquiry_id: str, body: FeedbackBody):
    """Record human corrections and final outcome for pilot metrics."""
    if inquiry_id not in _store:
        raise HTTPException(status_code=404, detail="Packet not found")
    _store[inquiry_id]["feedback"] = {
        "corrections": body.corrections,
        "outcome": body.outcome,
        "notes": body.notes,
    }
    _feedback_log.append({
        "inquiry_id": inquiry_id,
        "corrections": body.corrections,
        "outcome": body.outcome,
        "notes": body.notes,
    })
    return {"status": "recorded", "inquiry_id": inquiry_id}


@app.get("/api/metrics")
async def get_metrics():
    """Pilot metrics: inquiries processed, corrections, outcomes.
    Outcomes count only the latest status per inquiry (not historical entries)."""
    total = len(_store)
    with_feedback = sum(1 for v in _store.values() if v.get("feedback"))
    # Latest feedback entry per inquiry (last occurrence in log)
    latest_by_inquiry: dict[str, dict] = {}
    for e in _feedback_log:
        iid = e.get("inquiry_id") or ""
        latest_by_inquiry[iid] = e
    outcomes = {}
    for e in latest_by_inquiry.values():
        out = e.get("outcome") or ""
        outcomes[out] = outcomes.get(out, 0) + 1
    correction_count = sum(len(e.get("corrections") or []) for e in _feedback_log)
    return {
        "inquiries_processed": total,
        "inquiries_with_feedback": with_feedback,
        "total_corrections": correction_count,
        "outcomes": outcomes,
        "feedback_log_count": len(_feedback_log),
    }


@app.get("/api/dashboard")
async def get_dashboard():
    """Dashboard data: metrics plus recent feedback for scaled rollout."""
    metrics = await get_metrics()
    recent = _feedback_log[-20:] if _feedback_log else []
    return {"metrics": metrics, "recent_feedback": list(reversed(recent))}


@app.get("/api/export-approved/{inquiry_id}")
@app.post("/api/export-approved/{inquiry_id}")
async def export_approved(inquiry_id: str):
    """One-click: export approved packet (CSV/staging format for JobBOSS)."""
    if inquiry_id not in _store:
        raise HTTPException(status_code=404, detail="Packet not found")
    data = _store[inquiry_id]
    packet = data["packet"]
    summary = packet.get("1_inquiry_summary") or {}
    facts = packet.get("2_extracted_technical_facts") or {}
    # Staging export: key fields for quote handoff (job_class = industry/segment for limited pilot)
    extracted = data.get("extracted") or {}
    job_class = extracted.get("industry") or summary.get("industry") or "general"
    row = {
        "inquiry_id": inquiry_id,
        "job_class": job_class,
        "customer": summary.get("customer"),
        "part": summary.get("part"),
        "quantity": summary.get("quantity"),
        "turnaround": summary.get("requested_turnaround"),
        "substrate": facts.get("substrate"),
        "requested_coating": facts.get("requested_coating"),
    }
    import csv
    from io import StringIO
    buf = StringIO()
    w = csv.DictWriter(buf, fieldnames=list(row.keys()))
    w.writeheader()
    w.writerow(row)
    csv_content = buf.getvalue()
    return Response(content=csv_content, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=approved_packet_{inquiry_id}.csv"})


# Serve frontend at / (API routes are under /api so they take precedence)
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
else:
    @app.get("/")
    async def root():
        return {"message": "Spec-to-Quote Copilot API", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
