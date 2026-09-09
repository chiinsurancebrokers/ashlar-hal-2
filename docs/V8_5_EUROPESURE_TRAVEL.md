# HAL 8.5 — Europesure Travel Engine

## Source
User-supplied legacy HAL Quote Engine v26 archive.

## Travel tiers retained from the source
| Tier | Emergency medical | Cancellation | Baggage | Legacy positioning |
|---|---:|---:|---:|---|
| Silver | €1,000,000 | €1,500 | €750 | Entry level / short EU / budget |
| Gold | €3,500,000 | €3,000 | €5,000 | Most popular / balanced |
| Platinum | €10,000,000 | €10,000 | €7,500 | Premium / worldwide |

Legacy source also states:
- Single Trip and Annual Multi-Trip
- Annual Multi-Trip from approximately €53.52
- maximum age 79
- travel delay, missed departure, personal accident, legal expenses
- optional Winter Sports, Business, Gadget, COVID-19 and Car Hire Excess add-ons

## Verification rule
These are legacy HAL values, not verified current 2026 Europesure terms.
The public card therefore says that current terms and price must be confirmed in the
Europesure quotation portal.

## Deterministic discovery
1. Single trip or annual multi-trip
2. Destination
3. Age of oldest traveller
4. Cover preference: budget / balanced / highest limits

OpenAI may extract those facts from natural language but cannot change the plan data,
eligibility flag or recommendation rules.

## Product-fit guard
Long-term relocation or a travel duration above 180 days triggers a one-time warning
that International Health Insurance may be the more appropriate product. The user may
still continue with Travel.

## API
- `GET /api/v1/travel/europesure`
- `POST /api/v1/travel/europesure/recommend`
