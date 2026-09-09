# HAL Voice Input

HAL v6 uses push-to-talk browser recording and server-side transcription.

## Why push-to-talk

Insurance conversations contain high-value structured facts such as ages, names,
medical conditions, deductibles and monetary amounts. HAL therefore shows the
transcription to the applicant before it is submitted to the conversational engine.

## Security boundary

- `OPENAI_API_KEY` exists only in Railway environment variables.
- The browser never receives the API key.
- HAL does not intentionally persist the raw recording to disk or database.
- File size is limited server-side.
- Recording duration is limited client-side to 90 seconds.

## Output voice

Speech-to-text is independent of HAL's response voice:
- OpenAI: transcription
- Anthropic: conversational reasoning / applicant extraction
- deterministic HAL services: price and evidence
- ElevenLabs: text-to-speech output
