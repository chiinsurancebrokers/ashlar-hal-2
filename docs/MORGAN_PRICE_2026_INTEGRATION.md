# Morgan Price Europe 2026 integration

## Rates

Source: `Rates.xlsx` supplied by Morgan Price and provided for HAL integration.
Normalized output: `data/rates/morgan_price_2026_official.csv`.
Version: `morgan_price_europe_2026_official`.

The workbook contains four geographic areas and five plan levels. Values are stored at the two-decimal values displayed by Excel; the raw floating value is retained in the CSV for audit.

### Geographic areas

1. Area 1 - Europe
2. Area 2 - Worldwide excluding USA, Singapore, Hong Kong and China
3. Area 3 - Worldwide excluding USA
4. Area 4 - Worldwide

### Plans

- Standard
- Standard Plus
- Comprehensive
- Premium
- Elite

## Official 2026 documents

Morgan Price's official downloads page identifies a document set for policies starting after 1 April 2026. HAL registers the official 2026 Table of Benefits, Policy Wording and plan IPIDs in `data/evidence/morgan_price_2026/documents.json`.

The Policy Wording content and core product-page comparison facts have been entered into the evidence ledger. The Table of Benefits and IPIDs are registered by official URL but remain `pending_binary_ingestion` until their actual PDF bytes are available to HAL. This is deliberate: HAL does not pretend it has page-level evidence it has not ingested.

## Evidence gate

Only claims with `status=verified` and `allow_generation=true` may be surfaced as verified facts. Exact sublimits and detailed plan conditions that require the 2026 Table of Benefits stay locked until that PDF is ingested and hashed.
