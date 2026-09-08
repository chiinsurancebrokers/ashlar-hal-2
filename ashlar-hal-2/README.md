# HAL 2.0 — Ashlar Assurance

HAL 2.0 is the modular quotation, policy-intelligence and evidence-constrained
recommendation platform for Ashlar Assurance.

## Principles

- LLMs do not calculate insurance premiums.
- Applicant conversations are converted into structured data.
- Insurer-specific rating logic is isolated behind adapters.
- Policy claims should be evidence-backed before HAL presents them as verified.
- Rates and product rules are versioned.
- Secrets belong in deployment environment variables, never in Git.
- Current carrier rates can be used as the baseline and replaced with 2026 versions
  when new files arrive.

## Architecture

```text
Client / Voice
      |
      v
Applicant Intelligence
      |
      +--------------------+
      |                    |
      v                    v
Eligibility Engine    Requirements Engine
      |                    |
      v                    v
Quote Orchestrator    Policy Intelligence
      |                    |
      v                    v
Insurer Adapters      Evidence Ledger
      |                    |
      +----------+---------+
                 v
        Verified Match Engine
                 |
                 v
        HAL Explanation Layer
```

## Local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload
```

Open:

- `GET /health`
- `GET /api/v1/carriers`
- `POST /api/v1/quotes/preview`

## Current-rate strategy

The first production data version should be labelled explicitly, for example:

- `morgan_price_2025_current`
- `april_2025_current`
- `img_2025_current`

When 2026 files arrive, add a new version and change the active version. Do not
overwrite historical rate versions.

## Deployment

- Railway: FastAPI backend, database and heavier processing.
- Netlify: public HAL web interface.
- Secrets: Railway/Netlify environment variables only.
