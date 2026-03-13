# Risk Register and Mitigations — Spec-to-Quote Copilot

| Risk | Mitigation |
|------|------------|
| **Hallucinated technical recommendations** | Retrieval-first design; show sources (job IDs); confidence labels; no autonomous quoting; mandatory human approval. |
| **Poor data quality in historical jobs** | Start with cleaned subset; canonical coating taxonomy; human review of mappings; retrieval on documents plus structured fields. |
| **Experts refuse to trust it** | Start with shadow mode; show where it helps; collect and display precision metrics; let them edit and improve rules. |
| **ERP integration complexity** | Start with CSV / staging table export; do not block on full JobBOSS integration; integrate only after packet quality is proven. |
| **Compliance mistakes** | Compliance flags only, not compliance decisions; restricted templates; cert references from approved internal docs only. |
| **Users stop using it after pilot** | Measure user-level time saved; keep UI simple; eliminate duplicate entry; tie outputs directly into existing quote workflow. |
