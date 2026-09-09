# HAL 8.5 — OpenAI Adviser + Europesure Travel Engine


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

## HAL 2.7

The client-facing shortlist now:
- excludes verified plans that fail a MUST-HAVE benefit;
- shows a provider-diverse shortlist when matching carrier rates are loaded;
- uses original-style comparison cards;
- removes evidence/source labels from the card UI;
- keeps backend evidence and all-plan analysis available internally.

`Get proposal` opens the Gmail-backed enquiry form.
`Tell me more` asks HAL about the selected card.

## HAL v8 UX

- 3-stage progress: Understand needs → Compare plans → Request proposal
- editable `Your needs` chips with deterministic re-quoting
- mobile swipe/snap plan cards
- smart fit badges and verified must-have ticks
- client-safe explanation of plans excluded by MUST-HAVE filters
- select 2+ plans for Quick Compare
- Advanced Policy Analyzer hand-off for document-level comparison
- `Send me this comparison` via Gmail API using server-recomputed plan data
- sticky composer, richer loading states and 24-hour browser preference restore
- HNWI/private-client CTA adapts to `Request a private consultation`

The advanced analyzer URL can be overridden with `POLICY_ANALYZER_URL`.

## v8.1 Guided Adviser

HAL no longer produces a client shortlist as soon as age/residence/area are known. It completes a deterministic discovery flow covering deductible, inpatient-vs-outpatient, maternity where age-relevant, dental, mental health, evacuation and budget.

The public UI now keeps comparison inside HAL. The standalone Policy Analyzer remains an internal/broker-grade tool and is not exposed to applicants.

`Tell me more` calls a deterministic plan-details endpoint. Morgan Price details are built from the verified 2026 Table of Benefits; other carrier details stay limited to currently loaded data until their current benefit evidence is loaded.

## v8.2 — Intent-first conversation

A country name is treated as applicant context, not as a request for a healthcare-system
lecture.

Example:
`My name is Chris, I'm 51, I live in Greece and I want international health insurance`

HAL now:
1. greets Chris by name;
2. recognises a long-term IPMI enquiry;
3. acknowledges Greece briefly without discussing OECD/public-system statistics;
4. asks the next missing advice question;
5. opens Destination Healthcare Intelligence only when the applicant explicitly asks
   about the Greek healthcare system, public hospitals, waiting lists or why private
   insurance is useful in Greece.

HAL also avoids asking for information the applicant already supplied.

## v8.2.1
Root requirements are self-contained for reliable Railway/Nixpacks builds.

## v8.3 — Adaptive Voice Adviser UI

The public experience now has two visual phases:

1. Minimal welcome experience
   - animated voice ring
   - Health / Travel entry choice
   - voice-first interaction
   - one short introductory message

2. Guided adviser experience
   - one question at a time
   - contextual quick-reply buttons
   - editable needs summary
   - plan cards only after needs discovery
   - inline light comparison
   - Gmail-backed proposal / comparison handoff

The full Policy Analyzer remains internal and is not exposed to applicants.

## v8.3.1 — Male HAL voice

HAL now uses one consistent male multilingual ElevenLabs voice for both Greek and
English.

Default:
`Adam` (`pNInz6obpgDQGcFmaJgB`)

Override in Railway:
`HAL_MALE_VOICE_ID=<your preferred ElevenLabs male voice ID>`

The TTS delivery is tuned for a calm insurance-adviser style:
- moderate stability;
- low style exaggeration;
- slightly slower speech;
- speaker boost enabled.

No API key or private credential is stored in the repository.

## v8.3.2 — Single Interface + microphone fix

- HAL no longer changes to a second UI after the first message.
- The animated HAL screen remains the primary interface throughout the journey.
- Conversation history, needs and plan cards progressively appear beneath it.
- Microphone is a real toggle: first tap starts recording; second tap stops and transcribes.
- Media tracks are always closed after stop/error.
- The transcript remains reviewable before sending.
- Inline favicon removes the browser `/favicon.ico` 404.

## v8.4 — OpenAI Adviser Engine

HAL's conversational layer now uses the OpenAI Responses API.

Default conversational model:
`gpt-5.6-terra`

Architecture:
`Applicant -> OpenAI language understanding -> deterministic discovery/rating/evidence -> OpenAI explanation`

OpenAI may understand natural English/Greek, extract applicant facts, acknowledge what
the applicant has already told HAL, and explain verified results naturally.

OpenAI may not calculate premiums, create benefits, bypass MUST-HAVE exclusions,
determine underwriting acceptance, or replace HAL's deterministic evidence/rating logic.

Public applicant Responses API calls use `store=false`.
The same `OPENAI_API_KEY` can also power the existing transcription endpoint.
HAL v8.4 no longer calls Anthropic.

## v8.5 — Europesure Travel Engine

Travel Insurance is now a separate deterministic product journey rather than a generic
lead-routing response.

Legacy Europesure product knowledge imported from the user-supplied HAL v26 source:
- Silver: €1M emergency medical / €1,500 cancellation / €750 baggage
- Gold: €3.5M emergency medical / €3,000 cancellation / €5,000 baggage
- Platinum: €10M emergency medical / €10,000 cancellation / €7,500 baggage
- Single Trip and Annual Multi-Trip
- legacy maximum age 79
- legacy optional add-ons: Winter Sports, Business, Gadget, COVID-19, Car Hire Excess

Important: this dataset is explicitly marked `legacy_unverified_current`.
HAL uses it for indicative product matching only. Current benefits, eligibility, wording
and premium must be confirmed through the Europesure portal before purchase.

Travel and IPMI discovery are separated before parsing, preventing travel answers from
being interpreted as health-insurance deductibles or benefits.
