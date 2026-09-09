# HAL 2.0 v6.5 — Gmail Lead Delivery


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


## v6 Education + Destination Intelligence

HAL now has a balanced educational layer for:
- International vs local private health insurance
- IPMI vs travel insurance
- Public healthcare vs private insurance
- Destination-specific healthcare-system context

Initial curated destination: **Greece**.

Endpoints:

```text
GET /api/v1/knowledge/international-vs-local
GET /api/v1/knowledge/destinations/GR
```

The knowledge layer is not allowed to override rate or policy evidence. Provider
marketing/education sources can explain concepts; plan benefits still require official
policy evidence.

HAL is explicitly instructed to argue with facts and trade-offs rather than pressure:
it may recommend local insurance when that is the better fit.


## v6 HNWI / Affluent Local Intelligence

HAL now recognises that international health insurance is not only an expatriate
product. Affluent local nationals may have a strong IPMI use case when they require
international provider choice, higher limits, cross-border treatment, long-term
portability, direct billing or a broad comprehensive contract.

Endpoint:

```text
GET /api/v1/knowledge/hnwi-ipmi
```

The HNWI layer also corrects the interpretation of Greece's out-of-pocket spending:
OOP is aggregate household direct healthcare expenditure, not evidence of claim
denials or lack of insurance.


## v6.1 Stability Fix

This build addresses two production issues observed on iOS/Railway.

### 1. ElevenLabs echo / overlapping speech

The browser now has exactly one audio player. New playback cancels and cleans the
previous player. Starting microphone recording stops HAL speech first.

Voice selection prefers one shared multilingual `ELEVENLABS_VOICE_ID`. Language-
specific IDs are only fallbacks when the shared ID is absent.

### 2. `...` replies / JSON parser failures / missing knowledge

HAL no longer requires perfect JSON from the LLM.

- plain-language model responses are accepted;
- empty / ellipsis replies are rejected;
- a bare age such as `51` is extracted deterministically;
- common needs such as outpatient and mental-health cover are extracted deterministically;
- Morgan Price, Greece healthcare, International-vs-Local and HNWI prompts are served
  directly from curated knowledge;
- if the LLM fails, HAL asks the next useful question rather than returning an error.

The end user should no longer see `Expecting value: line 1 column 1`.

## v6.2 — Evidence-led private insurance advocacy

HAL now translates destination-system evidence into an insurance recommendation.

It explicitly supports private insurance when current evidence shows:
- access constraints;
- unmet medical needs;
- material waiting-list pressure;
- high direct household healthcare spending.

The prompt remains balanced:
- the public system is recognised as an essential social safety net;
- private insurance is positioned as complementary;
- waiting-list evidence is treated as a major decision factor;
- affluent/HNWI clients receive a more direct explanation of the value of
  comprehensive private/IPMI cover.

## v6.3
HAL now uses pro-IPMI, outpatient-first comprehensive positioning with evidence-locked product claims.

Endpoint: `GET /api/v1/knowledge/ipmi-value`

## v6.4

HAL now routes prospects between:
- International Health Insurance (IPMI)
- Travel Insurance
- Local-vs-International broker review

It can open a lead form and deliver the enquiry through Gmail API without collecting
detailed medical history in the public form.

Endpoint:

```text
POST /api/v1/leads
```

## v6.5 — Gmail API lead delivery

Gmail API replaces EmailJS for lead-form delivery. HAL uses the narrow `gmail.send` OAuth scope and sends from Railway.

Required Railway variables:

```text
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
GMAIL_REFRESH_TOKEN=
GMAIL_SENDER_EMAIL=
GMAIL_LEAD_RECIPIENT=
```
