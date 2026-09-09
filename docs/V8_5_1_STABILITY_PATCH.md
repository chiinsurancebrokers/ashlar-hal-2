# HAL 8.5.1 — Journey / Composer / Voice Stability Patch

Fixes observed during live browser testing:

1. **Travel → IPMI / IPMI → Travel isolation**
   - switching product clears the previous conversation and journey-specific state;
   - explicit typed switches such as “I’m looking for international health insurance”
     also start a fresh journey;
   - backend independently resets state/history when a journey switch is detected.

2. **Guided-answer loop**
   - short answers to age, residence and coverage-area questions are parsed directly;
   - `Greece` and `in Greece` now satisfy a pending residence question;
   - bare `Europe`, worldwide excluding USA, and worldwide including USA answers
     satisfy the coverage-area question.

3. **Bottom composer**
   - the real adviser composer is moved into the stable single-interface view;
   - the old top welcome input is hidden once the adviser is active;
   - the composer remains sticky near the bottom while the conversation grows;
   - new messages scroll toward the composer automatically.

4. **HAL voice**
   - after each successful HAL response, the frontend automatically requests TTS;
   - automatic TTS failures do not pollute the chat;
   - the visible `Hear HAL` control remains available as a manual fallback;
   - the large orb records into the visible adviser composer once the conversation is active.

No travel or IPMI rating / benefit logic is changed by this patch.
