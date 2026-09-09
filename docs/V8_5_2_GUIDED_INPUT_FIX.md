# HAL 8.5.2 — Guided numeric input fix

Live testing found that `€500 deductible` was displayed in the chat but did not
mark the deductible as answered.

Root cause:
- accidental double escaping of whitespace regexes in `_norm`, deductible parsing
  and budget parsing.

Fix:
- correct whitespace normalization;
- shared `_extract_amount()` helper;
- accepts €0, €500, €1,000, 500 deductible, Budget €3000 and Budget €5,000;
- preserves Flexible deductible and No fixed budget behavior.

No insurer rate, benefit or matching logic changes.
