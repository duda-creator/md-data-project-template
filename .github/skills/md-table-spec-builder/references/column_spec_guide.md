# Table specification — field guide

## Where this fits

`data/<stage>/<file>` → profiling report (`data/4_profiling/<stage>/*_profiling.csv`) → **`scripts/build_table_spec.py`** → Table Specification (`data/5_spec/<stage>/<source>.spec.csv`) → later database implementation.

The script handles the deterministic part (column extraction, provenance, `Target Table` inference from `Source Extract`, `Format` from `dtype`, Business Role suggestion from threshold rules, append/idempotency, and the approved-file lock). Humans still review and finalize all judgment fields.

## Fields

| Field | Meaning | Values / notes |
|---|---|---|
| Source Extract | Which source file this row came from | Inferred automatically from the profiling filename (e.g. `fact_ftp_daily_profiling.csv` → `fact_ftp_daily.csv`) |
| Source Column | Original column name in the source extract | Populated automatically from profiling `column` |
| Target Table | Initial target staging table name | Auto-filled as `stg_<source_extract_stem>` (e.g. `fact_balance_sheet_monthly.csv` → `stg_fact_balance_sheet_monthly`) |
| Target Column Name | Name in the destination table | snake_case recommended |
| Type | Load behavior | `Mandatory` (must exist, no blanks) / `Optional` (must exist, blanks OK — script default) / `Ignore` |
| Business Role | Analytical role | Auto-suggested by deterministic thresholds using `Format`, `distinct_pct`, and `missing_values`; review required |
| Format | Canonical technical type — **not** an implementation-specific type | Auto-filled from profiling `dtype`; review required |
| Primary/Unique Key | Marks grain-defining columns | `Y` / `N` — feeds table-level PK constraints and, later, join-key identification in the semantic layer |
| PII/Sensitivity | Governance flag, captured while the column is in front of you | e.g. `None` / `PII` / `Confidential` — adjust the vocabulary to match your actual data-classification policy |
| Allowed Values | Inclusion filter | Optional |
| Rejected Values | Exclusion filter | Optional |
| Description | Business meaning | — |
| Notes | Implementation/technical notes, kept separate from Description | e.g. open questions for the data owner |
| Status | HITL gate | `Draft` / `Reviewed` / `Approved` — a later implementation workflow should require every row to be `Approved` |

## Business Role — enum

- **Dimension** — a key/attribute that joins out to a separate dimension table.
- **Dimension Attribute** — a descriptive (non-key) column living on a dimension table.
- **Degenerate Dimension** — an identifier that stays on the fact table with no separate dimension table behind it (e.g. an invoice or transaction number).
- **Measure** — a numeric fact/metric.

This classification is a first pass, not final — the semantic layer may reclassify some of these once relationships across multiple sources are mapped. Cheap to revisit; not worth blocking on.

## Business Role suggestion thresholds

The script uses these fixed rules:

- Numeric formats (`INTEGER`, `BIGINT`, `DECIMAL(18,6)`, `BOOLEAN`):
	- `distinct_pct >= 0.60` and `missing_values = 0` => `Measure`
	- `distinct_pct <= 0.02` and `missing_values = 0` => `Dimension`
	- otherwise => `Dimension Attribute`
- Temporal formats (`DATE`, `TIMESTAMP`):
	- `missing_values = 0` => `Dimension`
	- otherwise => `Dimension Attribute`
- Text-like formats (`TEXT` and fallback):
	- `distinct_pct >= 0.85` and `missing_values = 0` => `Degenerate Dimension`
	- `distinct_pct <= 0.02` and `missing_values = 0` => `Dimension`
	- otherwise => `Dimension Attribute`

These values are intended as reproducible defaults and should be tuned later if your data model requires different cutoffs.

## Approval and the whole-file lock

Once every row's `Status` is `Approved`, the spec file as a whole is considered locked — the script itself enforces this by refusing to append further rows to a fully-approved file. If an approved spec needs to change, don't edit it in place: copy it forward to a new version (e.g. `orders.spec.v2.csv`) and reset that copy's rows to `Draft` for re-review. This keeps the original approved version, and anything already generated from it, intact and traceable.

## Files

- `scripts/build_table_spec.py` — deterministic extraction from profiling rows, `Target Table` inference, `Format` auto-fill, Business Role suggestion thresholds, append/idempotency, and the approved-file lock.
- `column_spec_template.csv` — the field layout for reference, or for building a spec by hand when there's no source file to run the script against.
- `canonical_type_mapping.csv` — canonical `Format` values and their intended meanings.
