# HAL v8 — Premium adviser UX

The v8 flow borrows proven concepts from three earlier Ashlar/CHI projects:

- the original quote engine's strong client-facing cards, mobile layout and quick-email flow;
- Policy Analyzer's structured comparison categories and document-grounded escalation path;
- chi-quote-demo-app's quote-sent email concept, now delivered with the Gmail API.

## Quick Compare vs Advanced Policy Analyzer

Quick Compare is for the current HAL shortlist: price, annual limit, coverage summary,
deductible, evacuation, needs-fit and verified must-have ticks.

Advanced Policy Analyzer is for source-document analysis: policy wording, waiting
periods, underwriting basis, exclusions and critical limitations.

## Email security

The comparison email endpoint does not trust browser-supplied premiums. It receives
selected plan keys, rebuilds the shortlist server-side from the applicant state and
then sends the validated plans through Gmail.

## Session restore

Only structured insurance preferences, shortlist and selected comparison keys are
stored in localStorage for up to 24 hours. The full chat transcript is not persisted.
