# HAL 8.3 Adaptive Voice Adviser UI

The visual shell borrows selected interaction patterns from the supplied legacy deploy,
but all quotation, evidence, discovery, Gmail, comparison and plan-explanation logic
remains on the current HAL backend.

## Public journey

Welcome:
`Health Insurance | Travel Insurance -> speak/type`

Adviser:
`understand needs -> contextual choices -> shortlist -> compare -> proposal`

## Important UX rules

- Do not show the permanent shortcut menu on the main flow.
- Show only question-specific quick replies.
- Do not show a proposal CTA before HAL has produced useful guidance.
- Do not expose the full Policy Analyzer to applicants.
- Policy-document intelligence is an internal HAL capability.
- Voice recording can begin on the welcome screen without exposing API keys.
- The transcript is still reviewable before submission.
