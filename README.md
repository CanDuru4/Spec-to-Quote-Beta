# Spec-to-Quote Copilot

An **AI-assisted technical intake and quote-prep system** for a specialty coatings manufacturer. It helps humans respond faster, quote more consistently, and avoid margin leakage — from customer inquiry through human approval.

**Product in one sentence:** AI drafts a six-section Quote Review Packet from uploaded inquiry documents; the human approves, edits, requests clarification, or escalates. No autonomous quoting or ERP writeback without approval.

---

## Problem

New inquiries today require: reading emails and attachments, interpreting drawings/specs, figuring out substrate and requirements, selecting coating families or prior analogous jobs, identifying missing info, checking compliance, and packaging everything into a quote. Tribal knowledge accumulates here; mistakes at intake hurt win rate and margin.

**P&L context:** Modest improvements in quote accuracy, turnaround time, and bad-job avoidance have meaningful dollar impact.

---

## Run instructions

### Option A: Docker (safe, reproducible environment)

Prerequisites: Docker and Docker Compose.

```bash
cd spec-to-quote-copilot
docker compose up --build
```

Open **http://localhost:8000**. Optional: set `OPENAI_API_KEY` (or `ANTHROPIC_API_KEY`) in a `.env` file for LLM extraction and reasoning (GPT preferred).

- The image uses Python 3.11 slim, runs as a non-root user, and does not copy `.env` or secrets (see `.dockerignore`).
- Uploads are stored inside the container by default; for persistence you can add a volume in `docker-compose.yml` and adjust permissions if needed.

### Option B: Local Python

#### Prerequisites

- Python 3.11+
- pip

#### Setup

```bash
cd spec-to-quote-copilot
pip install -r requirements.txt
cp .env.example .env
# Optional: set OPENAI_API_KEY (or ANTHROPIC_API_KEY) in .env for LLM extraction and reasoning (otherwise rule-based fallback is used)
```

#### Generate sample inquiry PDFs (if not already present)

```bash
python backend/data/generate_sample_inquiries.py
```

#### Start the app

From the repo root:

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Or from the `backend` directory:

```bash
cd backend && python main.py
```

Open in browser: **http://localhost:8000**

- **Upload** a PDF, Word, or Excel inquiry (or use sample PDFs in `backend/data/sample_inquiries/`).
- Click **Process inquiry → Generate packet** to run the pipeline and see the six-section Quote Review Packet.
- Use **View packet (HTML)**, **Download packet (PDF)**, **Generate clarification email**, **Escalate to technical lead**, **Export approved packet**, and **Record outcome** (Approved/Rejected/Escalated) for pilot metrics.
- **Dashboard:** http://localhost:8000/dashboard.html — metrics and recent feedback.

### API docs

- Swagger UI: http://localhost:8000/docs  
- ReDoc: http://localhost:8000/redoc  

---

## Demo flow

1. Open http://localhost:8000
2. Drag-and-drop or select `backend/data/sample_inquiries/inquiry_semiconductor_wafer_chuck.pdf` (or `inquiry_medical_housing.pdf`)
3. Click **Process inquiry → Generate packet**
4. Review left panel (parsed text) and right panel (six-section packet: summary, technical facts, similar jobs with job IDs, coating paths, risk flags, checklist)
5. Click **Generate clarification email** to get a draft customer email
6. Click **Export approved packet** to download CSV for staging/JobBOSS
7. Click **Approved** or **Escalate** under “Record outcome” to log pilot feedback
8. Open **Dashboard** to see metrics and recent feedback

---

## Impact metrics (prove impact)

- **Speed:** Median time inquiry → first response; inquiry → quote draft; % same-day response; hours saved per estimator.
- **Quality:** Extraction accuracy; % quotes requiring major rework; % missing critical info caught before quote; % AI-retrieved analog jobs judged relevant; human override rate.
- **Business:** Quote win rate; gross margin on quoted jobs vs baseline; rework/scrap incidence; % jobs later labeled underquoted.

**Target ranges (not guarantees):** Reduce quote-prep time 30–50%; increase same-day technical response; reduce avoidable underquote/missing-info on pilot jobs.

---

## Voiceover outline (10–15 min Loom)

- **Min 1–2:** Business context — company wins complex coating work; front-end bottleneck is expert interpretation and quote prep.
- **Min 3–4:** Why it matters to P&L — prototype → production; mistakes at intake hurt win rate and margin.
- **Min 5–8:** Demo — upload inquiry, extracted facts, similar historical jobs, risk flags, draft clarification email, approved packet export.
- **Min 9–11:** Implementation and deployment — pilot, human-in-loop, JobBOSS integration, monitoring.
- **Min 12–13:** Change management — who uses it, how work changes, why experts will trust it.
- **Min 14–15:** Risks — hallucinations, data quality, expert trust, staged rollout.

---

## Repo structure

- `backend/` — FastAPI app, ingest, parse, extract, retrieve, reason, packet; `data/demo_jobs.json`, `data/sample_inquiries/`
- `frontend/` — Approval UI (index.html, dashboard.html)
- `docs/` — DISCOVERY.md, CHANGE_MANAGEMENT.md, RISK_REGISTER.md

---

## Docs

- [Discovery (Phase 0)](docs/DISCOVERY.md) — Workflow map, pain points, Quote Review Packet definition
- [Change Management](docs/CHANGE_MANAGEMENT.md) — Users, before/after, training, adoption
- [Risk Register](docs/RISK_REGISTER.md) — Six risks and mitigations
