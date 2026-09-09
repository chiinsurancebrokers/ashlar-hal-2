# HAL 8.3.2 — Single Interface

## Voice flow

First microphone tap:
`idle -> listening`

Second microphone tap:
`listening -> stop -> transcribing -> transcript ready`

The browser audio stream is explicitly closed after stop/error.

## UI flow

The initial HAL orb experience remains on screen throughout the advice journey.

Instead of switching to a second application-like panel, HAL progressively adds:
- conversation history;
- contextual answer buttons;
- structured needs;
- plan cards;
- comparison/proposal actions.

The applicant never experiences a visual app switch.
