# HAL 2.0 v6 — Conversational + Voice Input + Provider Knowledge


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


## v6: Provider Knowledge Layer

HAL now maintains a separate source class for provider/company information.

Morgan Price official sources:
- About Us
- Individual
- Group
- Intermediaries
- Downloads

The backend refreshes provider pages from an explicit host allowlist and keeps:
- source URL
- final URL after redirect
- UTC fetch timestamp
- SHA-256 content hash
- cleaned page text for conversational context

Provider pages are **context only**. They cannot alter premiums, eligibility or policy
benefit truth. Those continue to come from rate engines and evidence documents.

Endpoints:

```text
GET  /api/v1/providers
GET  /api/v1/providers/morgan_price
POST /api/v1/providers/morgan_price/refresh
POST /api/v1/chat/turn
```

The refresh endpoint uses `X-Admin-Password` when `ADMIN_PASSWORD` is configured.

## v6: Conversational HAL

The public UI is now free-form conversational. Claude extracts applicant facts into
the structured Applicant schema. The deterministic quote engine then calculates
quotes. Claude never calculates premiums.

`ANTHROPIC_API_KEY` activates conversational extraction. `ANTHROPIC_MODEL` defaults
to `claude-sonnet-4-6` and can be overridden in Railway.

## Voice compatibility

HAL accepts either:
- `ELEVENLABS_VOICE_ID` as one shared voice, or
- `ELEVENLABS_VOICE_ID_EN` / `ELEVENLABS_VOICE_ID_EL` as language overrides.

Groq is not required by v6.


## v6 Voice Input / Transcription

HAL now supports push-to-talk transcription from the public web interface.

Flow:

```text
Browser microphone
  -> MediaRecorder
  -> POST /api/v1/transcribe
  -> Railway backend
  -> OpenAI transcription API
  -> transcript returned to browser
  -> user reviews/edits text
  -> Send to HAL
```

The OpenAI API key is server-side only. Audio is not intentionally written to HAL's
filesystem or database by this implementation.

Environment variables:

```text
OPENAI_API_KEY=
OPENAI_TRANSCRIBE_MODEL=gpt-4o-mini-transcribe
MAX_AUDIO_UPLOAD_MB=20
```

The browser recording is capped at 90 seconds per push-to-talk turn. The transcript
is not auto-submitted: the applicant sees it in the text box and can correct names,
medical terms, ages, currencies or amounts before sending it to HAL.

Endpoint:

```text
POST /api/v1/transcribe
multipart/form-data field: file
```
