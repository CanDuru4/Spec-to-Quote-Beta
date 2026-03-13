# Change Management — Spec-to-Quote Copilot

## Primary users

- **Estimator / quote coordinator** — Day-to-day use: upload inquiries, review packet, approve or request clarification.
- **Owner / CTO / technical lead** — Escalations, rule refinement, and sign-off on packet quality before full rollout.
- **Secondary:** Sales or customer service on intake; production planning, quality/compliance, ops manager for handoff.

## Before (current state)

- Read messy customer files manually.
- Rely on memory and old emails for similar jobs.
- Ask senior person repeatedly for interpretation.
- Build quote context from scratch for each inquiry.

## After (with Copilot)

- AI assembles a first-pass Quote Review Packet (six sections).
- Human edits, approves, or escalates only when needed.
- Fewer repetitive interpretation tasks.
- Senior expert spends more time on true exceptions and edge cases.

## Training plan

- **Week 1 — "AI drafts only"**  
  No system writeback; team reviews all AI output. Focus: what the packet contains, where it helps, where it is wrong.

- **Week 2 — Use on selected inquiries**  
  Run Copilot in parallel with normal workflow; collect corrections in the UI (Record outcome: Approved / Rejected / Escalated).

- **Week 3 — Approved packet export**  
  Allow approved packet export into the quote workflow (CSV/staging for JobBOSS). Human approval still required for every quote.

**Materials:** 30-minute walkthrough, one-page quick guide, examples of good vs bad AI packets, escalation rules.

## Adoption positioning

Do **not** position as "AI replacing expert judgment."  

Position as: **faster intake, better memory, fewer dropped details** — and a tool that helps new people get closer to expert-level prep while experts focus on exceptions and quality.
