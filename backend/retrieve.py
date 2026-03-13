"""
Layer 4 — Retrieval.
Hybrid search: similar historical jobs + relevant coating/process docs.
RAG with citations (job IDs).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEMO_JOBS_PATH = Path(__file__).resolve().parent / "data" / "demo_jobs.json"


def load_demo_jobs() -> list[dict[str, Any]]:
    path = Path(os.environ.get("DEMO_JOBS_PATH", DEMO_JOBS_PATH))
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _text_for_similarity(job: dict) -> str:
    parts = [
        job.get("part_description") or "",
        job.get("substrate") or "",
        job.get("coating_family") or "",
        job.get("coating_type") or "",
        job.get("industry") or "",
        job.get("customer") or "",
    ]
    return " ".join(p for p in parts if p).lower()


def _score_job(job: dict, extracted: dict) -> float:
    """Simple keyword overlap score. Can be replaced with embedding similarity."""
    job_text = _text_for_similarity(job)
    score = 0.0
    substrate = (extracted.get("substrate") or "").lower()
    if substrate and substrate in job_text:
        score += 2.0
    industry = (extracted.get("industry") or "").lower()
    if industry and industry in job_text:
        score += 2.0
    coating = (extracted.get("requested_coating") or "").lower()
    if coating:
        if "e-coat" in coating or "ecoat" in coating:
            if "e-coat" in job_text:
                score += 2.0
        if "anodize" in coating and "anodize" in job_text:
            score += 2.0
        if "fluoropolymer" in coating or "coating" in coating:
            if "fluoropolymer" in job_text or "ptfe" in job_text:
                score += 2.0
    part = (extracted.get("part_description") or "").lower()[:200]
    if part:
        words = set(part.split())
        job_words = set(job_text.split())
        overlap = len(words & job_words) / max(len(words), 1)
        score += overlap * 1.5
    return score


def retrieve_similar_jobs(extracted: dict, top_k: int = 5) -> list[dict]:
    """Return top_k similar historical jobs with source references (job_id)."""
    jobs = load_demo_jobs()
    if not jobs:
        return []
    scored = [(_score_job(j, extracted), j) for j in jobs]
    scored.sort(key=lambda x: -x[0])
    out = []
    for s, j in scored[:top_k]:
        out.append({
            "job_id": j.get("job_id"),
            "score": round(s, 2),
            "customer": j.get("customer"),
            "industry": j.get("industry"),
            "part_description": j.get("part_description"),
            "substrate": j.get("substrate"),
            "coating_family": j.get("coating_family"),
            "coating_type": j.get("coating_type"),
            "quantity": j.get("quantity"),
            "quoted_price": j.get("quoted_price"),
            "turnaround_days": j.get("turnaround_days"),
            "actual_margin_pct": j.get("actual_margin_pct"),
            "rework_notes": j.get("rework_notes"),
            "quality_incidents": j.get("quality_incidents"),
        })
    return out
