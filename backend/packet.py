"""
Assemble six-section Quote Review Packet (HTML and PDF export).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_packet(reasoning: dict[str, Any]) -> dict[str, Any]:
    """Return packet as structured dict (six sections)."""
    return {
        "1_inquiry_summary": reasoning.get("inquiry_summary") or {},
        "2_extracted_technical_facts": reasoning.get("extracted_technical_facts") or {},
        "3_similar_historical_jobs": reasoning.get("similar_jobs") or [],
        "4_recommended_coating_paths": reasoning.get("recommended_coating_paths") or [],
        "5_risk_missing_info_flags": reasoning.get("risk_missing_info_flags") or [],
        "6_quote_prep_checklist": reasoning.get("quote_prep_checklist") or [],
    }


def packet_to_html(packet: dict[str, Any], inquiry_id: str = "") -> str:
    """Render packet as HTML for view and print."""
    def row(k: str, v: Any) -> str:
        if v is None or v == "":
            return ""
        return f"<tr><td><strong>{k}</strong></td><td>{v}</td></tr>"

    html = ['<!DOCTYPE html><html><head><meta charset="utf-8"><title>Quote Review Packet</title>']
    html.append("<style>body{font-family:sans-serif;max-width:900px;margin:2em auto;padding:1em;} table{border-collapse:collapse;} th,td{border:1px solid #ccc;padding:8px;text-align:left;} th{background:#f5f5f5;} section{margin:1.5em 0;} h2{color:#333;border-bottom:1px solid #ccc;}</style>")
    html.append(f"</head><body><h1>Quote Review Packet</h1><p>Inquiry ID: {inquiry_id}</p>")

    # 1. Inquiry summary
    summary = packet.get("1_inquiry_summary") or {}
    html.append("<section><h2>1. Inquiry Summary</h2><table>")
    for k, v in summary.items():
        html.append(row(k.replace("_", " ").title(), v))
    html.append("</table></section>")

    # 2. Extracted technical facts
    facts = packet.get("2_extracted_technical_facts") or {}
    html.append("<section><h2>2. Extracted Technical Facts</h2><table>")
    for k, v in facts.items():
        if isinstance(v, list):
            v = ", ".join(str(x) for x in v) if v else ""
        html.append(row(k.replace("_", " ").title(), v))
    html.append("</table></section>")

    # 3. Similar historical jobs
    jobs = packet.get("3_similar_historical_jobs") or []
    html.append("<section><h2>3. Similar Historical Jobs (with source job IDs)</h2><table>")
    html.append("<tr><th>Job ID</th><th>Customer</th><th>Industry</th><th>Part</th><th>Substrate</th><th>Coating</th><th>Qty</th><th>Price</th><th>Turnaround</th></tr>")
    for j in jobs:
        html.append(f"<tr><td>{j.get('job_id','')}</td><td>{j.get('customer','')}</td><td>{j.get('industry','')}</td><td>{j.get('part_description','')}</td><td>{j.get('substrate','')}</td><td>{j.get('coating_family','')}</td><td>{j.get('quantity','')}</td><td>{j.get('quoted_price','')}</td><td>{j.get('turnaround_days','')} days</td></tr>")
    html.append("</table></section>")

    # 4. Recommended coating paths
    paths = packet.get("4_recommended_coating_paths") or []
    html.append("<section><h2>4. Recommended Coating Paths</h2>")
    for p in paths:
        html.append(f"<div style='margin:1em 0;padding:1em;background:#f9f9f9;border-radius:6px;'>")
        html.append(f"<strong>Rank {p.get('rank', '')} — {p.get('coating_family', '')}</strong><br/>")
        html.append(f"Why fit: {p.get('why_fit', '')}<br/>Why fail: {p.get('why_fail', '')}<br/>")
        html.append(f"Uncertainty: {p.get('uncertainty', '')} | Review by: {p.get('review_by', '')}</div>")
    html.append("</section>")

    # 5. Risk / missing-info flags
    flags = packet.get("5_risk_missing_info_flags") or []
    html.append("<section><h2>5. Risk / Missing-Info Flags</h2><ul>")
    for f in flags:
        html.append(f"<li>{f}</li>")
    html.append("</ul></section>")

    # 6. Quote-prep checklist
    checklist = packet.get("6_quote_prep_checklist") or []
    html.append("<section><h2>6. Draft Quote-Prep Checklist</h2><ul>")
    for c in checklist:
        html.append(f"<li>{c}</li>")
    html.append("</ul></section>")

    html.append("</body></html>")
    return "".join(html)


def packet_to_pdf(packet: dict[str, Any], inquiry_id: str = "", output_path: str | Path | None = None) -> bytes:
    """Generate PDF of packet. Returns PDF bytes."""
    html = packet_to_html(packet, inquiry_id)
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        from io import BytesIO
        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph("Quote Review Packet", styles["Title"]))
        story.append(Paragraph(f"Inquiry ID: {inquiry_id}", styles["Normal"]))
        story.append(Spacer(1, 12))

        summary = packet.get("1_inquiry_summary") or {}
        story.append(Paragraph("1. Inquiry Summary", styles["Heading2"]))
        data = [[k.replace("_", " ").title(), str(v)] for k, v in summary.items()]
        if data:
            t = Table(data)
            t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey), ("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
            story.append(t)
        story.append(Spacer(1, 12))

        jobs = packet.get("3_similar_historical_jobs") or []
        story.append(Paragraph("3. Similar Historical Jobs", styles["Heading2"]))
        if jobs:
            headers = ["Job ID", "Customer", "Part", "Substrate", "Coating", "Qty", "Price"]
            data = [[str(j.get(h.lower().replace(" ", "_"), "")) for h in headers] for j in jobs]
            data = [headers] + data
            t = Table(data)
            t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey), ("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
            story.append(t)
        story.append(Spacer(1, 12))

        paths = packet.get("4_recommended_coating_paths") or []
        story.append(Paragraph("4. Recommended Coating Paths", styles["Heading2"]))
        for p in paths:
            story.append(Paragraph(f"{p.get('coating_family', '')}: {p.get('why_fit', '')}", styles["Normal"]))
        story.append(Spacer(1, 12))

        flags = packet.get("5_risk_missing_info_flags") or []
        story.append(Paragraph("5. Risk / Missing-Info Flags", styles["Heading2"]))
        for f in flags:
            story.append(Paragraph(f"• {f}", styles["Normal"]))
        story.append(Spacer(1, 12))

        checklist = packet.get("6_quote_prep_checklist") or []
        story.append(Paragraph("6. Quote-Prep Checklist", styles["Heading2"]))
        for c in checklist:
            story.append(Paragraph(f"• {c}", styles["Normal"]))

        doc.build(story)
        return buf.getvalue()
    except Exception:
        # Fallback: return empty or minimal PDF
        from reportlab.pdfgen import canvas
        from io import BytesIO
        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        c.drawString(72, 720, "Quote Review Packet")
        c.drawString(72, 700, f"Inquiry ID: {inquiry_id}")
        c.drawString(72, 660, "See HTML export for full packet.")
        c.save()
        return buf.getvalue()
