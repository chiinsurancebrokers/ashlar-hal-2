# HAL 8.4 — OpenAI Adviser Engine

OpenAI handles natural conversation; HAL keeps insurance truth deterministic.

## OpenAI can
- understand free-form English and Greek;
- extract applicant facts;
- create short acknowledgements;
- explain verified outcomes.

## HAL deterministic services keep control of
- discovery sequence;
- premiums;
- MUST-HAVE filters;
- benefit verification;
- shortlist generation;
- eligibility-safe output.

## Responses API
Endpoint: `POST https://api.openai.com/v1/responses`
Default model: `gpt-5.6-terra`
Applicant conversation storage: `store=false`
Structured model turns: `text.format.type=json_object`

## Railway
Required: `OPENAI_API_KEY`

Optional:
- `OPENAI_CHAT_MODEL=gpt-5.6-terra`
- `OPENAI_CHAT_MAX_OUTPUT_TOKENS=1400`
- `OPENAI_CHAT_TIMEOUT_SECONDS=60`

`ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL` are no longer required after v8.4 is healthy.
