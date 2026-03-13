"""
Layer 5 — Reasoning.
LLM creates technical summary, candidate coating paths (ranked, why fit/fail/uncertainty),
risk flags, questions for customer, quote-prep checklist.
"""
from __future__ import annotations

import json
import os
from typing import Any


def build_reasoning(
    extracted: dict[str, Any],
    similar_jobs: list[dict],
    combined_text: str,
) -> dict[str, Any]:
    """Build summary, coating paths, risks, checklist. Uses OpenAI GPT if API key set, else Anthropic, else template."""
    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if openai_key:
        try:
            return _openai_reason(extracted, similar_jobs, combined_text, openai_key)
        except Exception:
            pass
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if anthropic_key:
        try:
            return _anthropic_reason(extracted, similar_jobs, combined_text, anthropic_key)
        except Exception:
            pass
    return _template_reason(extracted, similar_jobs)


def _template_reason(extracted: dict, similar_jobs: list[dict]) -> dict:
    """Template-based reasoning when no LLM."""
    job_ids = [j.get("job_id") for j in similar_jobs if j.get("job_id")]
    coating = (extracted.get("requested_coating") or "coating").lower()
    paths = []
    if "e-coat" in coating or "ecoat" in coating:
        paths.append({
            "rank": 1,
            "coating_family": "e-coat",
            "why_fit": "Customer requested e-coat; similar jobs used epoxy e-coat.",
            "why_fail": "Part geometry may limit racking; high temp may be an issue.",
            "uncertainty": "medium",
            "review_by": "technical lead if high temp or complex masking",
        })
    if "anodize" in coating:
        paths.append({
            "rank": len(paths) + 1,
            "coating_family": "anodize",
            "why_fit": "Customer requested anodize; suitable for aluminum and titanium.",
            "why_fail": "Not for steel or cast iron; thickness/cosmetic requirements may vary.",
            "uncertainty": "low if substrate is Al or Ti",
            "review_by": "standard",
        })
    if "fluoropolymer" in coating or "ptfe" in coating or not paths:
        paths.append({
            "rank": len(paths) + 1,
            "coating_family": "fluoropolymer",
            "why_fit": "Chemical/corrosion resistance often addressed with fluoropolymer; similar jobs 1842, 1979, 2133.",
            "why_fail": "Temperature limits; adhesion on some substrates; cost.",
            "uncertainty": "medium",
            "review_by": "technical lead if substrate unclear",
        })

    risks = []
    if not extracted.get("substrate"):
        risks.append("Substrate unclear — confirm material before quoting.")
    if extracted.get("cert_requirements"):
        risks.append("Cert requirement detected — verify against approved internal docs.")
    if not extracted.get("quantity"):
        risks.append("Quantity missing — affects pricing tier and process.")
    # Margin/rework risk from similar jobs (Phase 4)
    rework_jobs = [j for j in similar_jobs if j.get("rework_notes")]
    low_margin_jobs = [j for j in similar_jobs if isinstance(j.get("actual_margin_pct"), (int, float)) and j["actual_margin_pct"] < 28]
    if rework_jobs:
        risks.append(f"Similar jobs had rework: {', '.join(str(j.get('job_id')) for j in rework_jobs[:3])} — review process assumptions.")
    if low_margin_jobs:
        risks.append(f"Similar jobs had margin below 28%: {', '.join(str(j.get('job_id')) for j in low_margin_jobs[:3])} — consider complexity and pricing.")
    risks.append("Human must confirm all assumptions before sending quote.")

    checklist = [
        "Confirm substrate/material",
        "Confirm part geometry and dimensions",
        "Confirm quantity",
        "Confirm target performance (temp, chemical, wear)",
        "Confirm cert needs",
        "Confirm testing required",
        "Confirm packing/shipping/turnaround assumptions",
    ]

    return {
        "inquiry_summary": {
            "customer": extracted.get("customer_name"),
            "part": extracted.get("part_description") or extracted.get("part_name"),
            "quantity": extracted.get("quantity"),
            "end_use": extracted.get("required_performance"),
            "requested_turnaround": extracted.get("turnaround"),
            "key_requirements": extracted.get("cert_requirements") or "See extracted fields",
        },
        "extracted_technical_facts": {k: v for k, v in extracted.items() if k not in ("ambiguity_flags", "missing_fields")},
        "similar_jobs": similar_jobs,
        "recommended_coating_paths": paths,
        "risk_missing_info_flags": risks,
        "quote_prep_checklist": checklist,
    }


def _parse_llm_json(text: str) -> dict:
    text = (text or "{}").strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)


def _openai_reason(extracted: dict, similar_jobs: list[dict], combined_text: str, api_key: str) -> dict[str, Any]:
    from openai import OpenAI
    jobs_str = json.dumps(similar_jobs[:5], indent=2)
    prompt = f"""You are a quote-prep assistant for a specialty coatings manufacturer.
Given:
1) Extracted fields from a customer inquiry: {json.dumps(extracted, indent=2)}
2) Similar historical jobs (with job_id): {jobs_str}
3) Raw inquiry text (excerpt): {combined_text[:4000]}

Produce a JSON object with exactly these keys:
- inquiry_summary: object with customer, part, quantity, end_use, requested_turnaround, key_requirements
- extracted_technical_facts: object (subset of extracted fields, technical ones)
- similar_jobs: use the same list provided (with job_id for citations)
- recommended_coating_paths: array of objects, each with rank, coating_family, why_fit, why_fail, uncertainty, review_by (e.g. "technical lead"). Reference job IDs where relevant.
- risk_missing_info_flags: array of strings (e.g. "Substrate unclear", "Cert requirement detected")
- quote_prep_checklist: array of strings (what human must confirm before sending quote)

Output valid JSON only, no markdown."""
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    text = (resp.choices[0].message.content or "{}") if resp.choices else "{}"
    data = _parse_llm_json(text)
    if "similar_jobs" not in data:
        data["similar_jobs"] = similar_jobs
    return data


def _anthropic_reason(extracted: dict, similar_jobs: list[dict], combined_text: str, api_key: str) -> dict[str, Any]:
    import anthropic
    jobs_str = json.dumps(similar_jobs[:5], indent=2)
    prompt = f"""You are a quote-prep assistant for a specialty coatings manufacturer.
Given:
1) Extracted fields from a customer inquiry: {json.dumps(extracted, indent=2)}
2) Similar historical jobs (with job_id): {jobs_str}
3) Raw inquiry text (excerpt): {combined_text[:4000]}

Produce a JSON object with exactly these keys:
- inquiry_summary: object with customer, part, quantity, end_use, requested_turnaround, key_requirements
- extracted_technical_facts: object (subset of extracted fields, technical ones)
- similar_jobs: use the same list provided (with job_id for citations)
- recommended_coating_paths: array of objects, each with rank, coating_family, why_fit, why_fail, uncertainty, review_by (e.g. "technical lead"). Reference job IDs where relevant.
- risk_missing_info_flags: array of strings (e.g. "Substrate unclear", "Cert requirement detected")
- quote_prep_checklist: array of strings (what human must confirm before sending quote)

Output valid JSON only, no markdown."""
    client = anthropic.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.content[0].text if resp.content else "{}"
    data = _parse_llm_json(text)
    if "similar_jobs" not in data:
        data["similar_jobs"] = similar_jobs
    return data
