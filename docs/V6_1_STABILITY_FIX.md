# HAL v6.1 Stability Fix

## JSON/parser failure

The previous chat service expected every Anthropic response to be valid JSON. A
plain-text or ellipsis response could therefore raise a JSON decoding error.

v6.1 accepts plain text, rejects meaningless ellipsis replies and falls back to
deterministic intake or curated knowledge.

## Voice echo

The prior web UI created a new `Audio()` object on each click and did not retain the
previous player. Multiple requests could overlap.

v6.1 uses one global player, aborts an in-flight request, revokes old object URLs and
stops playback before microphone recording.

## ElevenLabs voice priority

1. `ELEVENLABS_VOICE_ID`
2. `ELEVENLABS_VOICE_ID_EL` only when the shared ID is absent and Greek is requested
3. `ELEVENLABS_VOICE_ID_EN` only when the shared ID is absent and English is requested

Using one multilingual `ELEVENLABS_VOICE_ID` is recommended.
