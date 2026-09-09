# HAL 2.0 Migration Map

## ashlar-hall
Reuse:
- HAL chat/file UX
- bilingual language handling
- exclusions/terms analysis
- report-generation patterns

Do not migrate to the public client application:
- Lodge/private modules
- financial planner
- personal health/gym modules

## -ashlar-insurance-quote-engine
Reuse:
- public quotation flow
- ElevenLabs integration
- Whisper speech-to-text
- contact/proposal flow
- carrier admin concepts

Refactor:
- move hardcoded rates out of large HTML/JS files
- centralize AI/voice proxies and secrets server-side

## policyanalyzer
Make this the Policy Intelligence backend:
- extraction
- structured comparison
- caching
- recommendation support
- second-opinion verification

Strengthen with:
- page/clause/document hash provenance
- evidence statuses
- generation gate
- deterministic requirement scoring

## document_filler
Reuse:
- blank-form detection
- field coordinate detection
- source-data extraction
- PDF overlay/filling

Remove:
- any UI that persists API keys to local Streamlit secrets

## chi-quote-demo-app
Reuse only unique components not already present in ashlar-hall.

## insurance-comparator
Use mainly for bilingual UX/scoring inspiration; do not use as HAL 2.0's core
policy engine.
