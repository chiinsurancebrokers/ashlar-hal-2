# HAL 2.0 - Ashlar Assurance (v4 / Morgan Price 2026)

This build upgrades Morgan Price Europe from the temporary HAL table to the official 2026 rate workbook and registers the official 2026 policy-document set in the evidence layer.

## Live endpoints

- `/` - HAL client quotation interface
- `/health` - service health/version
- `/docs` - FastAPI docs
- `/api/v1/carriers` - carrier/data status
- `/api/v1/rates/versions` - active rate versions
- `/api/v1/rates/morgan-price/2026/source` - source audit metadata
- `/api/v1/quotes/preview` - deterministic quotation engine
- `/api/v1/evidence/morgan-price/2026` - registered documents + verified evidence
- `/api/v1/evidence/morgan-price/2026/{plan}` - plan evidence
- `/api/v1/voice/tts` - ElevenLabs TTS

## Data status

- Morgan Price Europe: **official 2026 rates**
- APRIL: legacy current/2025 table, awaiting replacement
- IMG: legacy current/2025 table, awaiting replacement

For geographic Areas 2-4, HAL currently quotes only Morgan Price because the official Morgan Price 2026 area definitions are verified and should not be mixed with older carrier-specific area labels.

## Evidence policy

HAL separates price calculation from policy assertions. Premiums come from deterministic rate records. Policy statements are gated by evidence status. Exact sublimits remain unavailable until the official 2026 Table of Benefits PDF is ingested and hashed.

## Railway

Keep repository root `/`; Nixpacks; the existing `railway.json` start command is valid.

## Secrets

Configure API keys only in Railway environment variables. Never commit `.env` or deployment secrets.


## Morgan Price 2026 evidence upgrade (v5)

The official Evolution Health Plan (EU) Table of Benefits has been ingested from all 9 supplied pages (document code `EU/EVO/SI/TOB/04/26`).

- Verified benefit rows: 65
- Source pages: 9
- Every benefit row stores its source page and SHA-256 hash.
- HAL now matches outpatient, routine maternity, routine dental, mental health, wellness, optical, medical evacuation and chronic-condition requirements against the official table.
- Precise Table-of-Benefits data supersedes broad marketing summaries where the two differ.
