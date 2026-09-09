# HAL 8.3.1 — Male multilingual adviser voice

HAL uses one male voice across English and Greek to keep the personality consistent.

## Voice priority

1. `HAL_MALE_VOICE_ID`
2. `ELEVENLABS_VOICE_ID`
3. language-specific legacy fallback

The code ships with ElevenLabs Adam as a non-secret default voice ID.

## Railway

Optional override:

```text
HAL_MALE_VOICE_ID=<copy a male Voice ID from ElevenLabs>
```

The ElevenLabs API key remains only in:

```text
ELEVENLABS_API_KEY
```

## Delivery settings

- model: `eleven_multilingual_v2`
- speed: 0.96
- stability: 0.58
- similarity boost: 0.78
- style: 0.12
- speaker boost: true

These settings aim for calm, confident adviser speech rather than dramatic narration.
