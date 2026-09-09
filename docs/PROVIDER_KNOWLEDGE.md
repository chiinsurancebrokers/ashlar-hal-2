# Provider Knowledge Architecture

Provider knowledge is intentionally isolated from rating and policy evidence.

## Trust classes

1. **Rates** — official spreadsheet/API, deterministic calculations only.
2. **Policy evidence** — official policy wording/Table of Benefits/IPIDs with page/document provenance.
3. **Provider knowledge** — official company About/Individual/Group/News/Downloads pages.
4. **Marketing/external sources** — not trusted for policy or price truth unless explicitly approved.

## Refresh design

Each provider has an allowlist of official domains and explicit source URLs.
HAL periodically fetches those URLs and records the fetch time and SHA-256 hash.
Redirects outside the allowlist are rejected.

The default refresh TTL is 24 hours (`PROVIDER_REFRESH_HOURS`).

## Safety boundary

About Us or marketing pages may explain who a provider is, its regulatory description,
history, services or positioning. They must never be used to infer an unlisted benefit,
premium, underwriting decision or eligibility rule.

## Adding another provider

Add a provider entry to `data/providers/providers.json` with:
- canonical name
- aliases
- allowed hosts
- official source URLs
- optional verified seed facts

No arbitrary user URL is fetched by the provider endpoint.
