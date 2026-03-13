"""
Layer 3 — Structured extraction.
LLM produces JSON: customer_name, part_name, part_description, industry, substrate,
requested_coating, required_performance, dimensions, quantity, cert_requirements,
turnaround, ambiguity_flags, missing_fields.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any


EXTRACTION_SCHEMA = {
    "customer_name": "string or null",
    "part_name": "string or null",
    "part_description": "string or null",
    "industry": "string or null",
    "substrate": "string or null",
    "requested_coating": "string or null",
    "required_performance": "string or null",
    "dimensions": "string or null",
    "quantity": "string or number or null",
    "cert_requirements": "string or null",
    "turnaround": "string or null",
    "ambiguity_flags": "list of strings",
    "missing_fields": "list of strings",
}


def _fallback_extract(combined_text: str) -> dict[str, Any]:
    """Rule-based extraction when no LLM is available."""
    text = (combined_text or "").lower()
    out = {
        "customer_name": None,
        "part_name": None,
        "part_description": None,
        "industry": None,
        "substrate": None,
        "requested_coating": None,
        "required_performance": None,
        "dimensions": None,
        "quantity": None,
        "cert_requirements": None,
        "turnaround": None,
        "ambiguity_flags": [],
        "missing_fields": [],
    }
    # Customer: X
    m = re.search(r"customer\s*:\s*([^\n,]+)", combined_text or "", re.I)
    if m:
        out["customer_name"] = m.group(1).strip()
    # Part: X / Part description: X
    for pat in [r"part\s*:\s*([^\n.]+)", r"part\s+description\s*:\s*([^\n.]+)", r"part\s+([^:\n]+?)(?:\s*\.|$|\n)"]:
        m = re.search(pat, combined_text or "", re.I)
        if m:
            out["part_description"] = m.group(1).strip()[:500]
            break
    # Quantity
    m = re.search(r"quantity\s*:\s*(\d+)", combined_text or "", re.I)
    if m:
        out["quantity"] = int(m.group(1))
    m = re.search(r"(\d+)\s*pieces?", combined_text or "", re.I)
    if m and out["quantity"] is None:
        out["quantity"] = int(m.group(1))
    # Substrate
    for sub in ["aluminum", "stainless steel", "steel", "cast iron", "titanium", "bronze", "316", "6061"]:
        if sub in text:
            out["substrate"] = sub
            break
    # Coating / e-coat / anodize
    if "e-coat" in text or "ecoat" in text:
        out["requested_coating"] = "e-coat"
    if "anodize" in text or "anodizing" in text:
        out["requested_coating"] = out["requested_coating"] or "anodize"
    if "fluoropolymer" in text or "ptfe" in text or "coating" in text:
        out["requested_coating"] = out["requested_coating"] or "fluoropolymer / coating"
    # Industry
    for ind in ["semiconductor", "medical", "aerospace", "automotive", "industrial", "marine", "defense", "food"]:
        if ind in text:
            out["industry"] = ind
            break
    # Turnaround
    m = re.search(r"turnaround\s*:\s*([^\n.]+)", combined_text or "", re.I)
    if m:
        out["turnaround"] = m.group(1).strip()
    m = re.search(r"(\d+)\s*weeks?", combined_text or "", re.I)
    if m and not out["turnaround"]:
        out["turnaround"] = f"{m.group(1)} weeks"
    # Cert
    if "iso" in text or "cert" in text or "13485" in text:
        out["cert_requirements"] = "ISO / certification mentioned"
    if not out["substrate"]:
        out["missing_fields"].append("substrate")
    if not out["quantity"] and "quantity" not in text:
        out["missing_fields"].append("quantity")
    if not out["part_description"] and "part" in text:
        out["part_description"] = "(see raw text)"
    return out


def extract_structured(record: dict) -> dict:
    """Produce structured JSON from parsed inquiry. Uses OpenAI GPT if API key set, else Anthropic, else fallback."""
    combined = record.get("combined_text") or ""
    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if openai_key:
        try:
            return _openai_extract(combined, openai_key)
        except Exception:
            pass
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if anthropic_key:
        try:
            return _anthropic_extract(combined, anthropic_key)
        except Exception:
            pass
    return _fallback_extract(combined)


def _parse_llm_json(text: str) -> dict:
    """Parse JSON from LLM response (strip markdown code blocks if present)."""
    text = (text or "{}").strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)


def _openai_extract(combined_text: str, api_key: str) -> dict[str, Any]:
    from openai import OpenAI
    prompt = f"""Extract structured fields from this customer inquiry (text from uploaded documents).
Output a single JSON object with exactly these keys: customer_name, part_name, part_description, industry, substrate, requested_coating, required_performance, dimensions, quantity, cert_requirements, turnaround, ambiguity_flags (array of strings), missing_fields (array of strings).
Use null for unknown. For ambiguity_flags list things that are unclear (e.g. "substrate unclear"). For missing_fields list critical info not stated (e.g. "dimensions", "cert requirements").
Inquiry text:
---
{combined_text[:12000]}
---
JSON only, no markdown:"""
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    text = (resp.choices[0].message.content or "{}") if resp.choices else "{}"
    data = _parse_llm_json(text)
    for k in EXTRACTION_SCHEMA:
        if k not in data:
            data[k] = [] if "flags" in k or "fields" in k else None
    return data


def _anthropic_extract(combined_text: str, api_key: str) -> dict[str, Any]:
    import anthropic
    prompt = f"""Extract structured fields from this customer inquiry (text from uploaded documents).
Output a single JSON object with exactly these keys: customer_name, part_name, part_description, industry, substrate, requested_coating, required_performance, dimensions, quantity, cert_requirements, turnaround, ambiguity_flags (array of strings), missing_fields (array of strings).
Use null for unknown. For ambiguity_flags list things that are unclear (e.g. "substrate unclear"). For missing_fields list critical info not stated (e.g. "dimensions", "cert requirements").
Inquiry text:
---
{combined_text[:12000]}
---
JSON only, no markdown:"""
    client = anthropic.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.content[0].text if resp.content else "{}"
    data = _parse_llm_json(text)
    for k in EXTRACTION_SCHEMA:
        if k not in data:
            data[k] = [] if "flags" in k or "fields" in k else None
    return data
