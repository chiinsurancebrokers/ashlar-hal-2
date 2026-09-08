# Rate data

Do not commit confidential insurer pricing files to a public repository.

HAL 2.0 expects normalized CSV/XLS/XLSX rate files with these columns:

- carrier
- rate_version
- area
- age_min
- age_max
- product_code
- product_name
- annual_premium
- currency

For the first build, use the current rate versions already used by HAL and label
them explicitly as current/2025 data. When Morgan Price, APRIL and IMG provide
new rates, create new versions rather than overwriting old files.

Recommended production approach:
1. Keep this repository private.
2. Import proprietary rate files through an admin workflow.
3. Store normalized production data in PostgreSQL/private object storage.
