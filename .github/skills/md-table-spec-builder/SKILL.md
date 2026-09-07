---
name: md-table-spec-builder
description: Builds or extends a Table Specification from profiling reports — one row per profiled column, capturing source-to-target mapping, load behavior, analytical role, canonical data type, key/PII flags, and HITL review status — before a later implementation workflow. Use when the user wants to move from a *_profiling.csv report to a spec file ready for review, append a second profiled extract to an existing target table spec, or check whether a spec is ready for implementation.
---

# Table specification builder

## Purpose

Turn a profiling report into a Table Specification: one row per profiled column, deterministically extracted by `scripts/build_table_spec.py`, then completed by a human. The finished spec is an implementation-handoff input for a later database workflow, with canonical formats defined in `references/canonical_type_mapping.csv`.

## The one rule that matters here

Stay deterministic — no free-form guessing. The script populates `Source Extract`, `Source Column`, `Target Table`, and `Format` mechanically from profiling fields, and then applies fixed threshold rules to pre-fill a **suggested** `Business Role`. Everything else — `Target Column Name`, `Type` overrides, `Primary/Unique Key`, `PII/Sensitivity`, `Description`, `Notes` validation, and final approval — is still human-reviewed.

## Workflow

1. **Locate the profiling file** the user wants spec'd (typically `*_profiling.csv`).
2. **Run the script** rather than reading the header yourself:
   ```
   python scripts/build_table_spec.py <input_file> [-o <output_spec_file>]
   ```
   If `-o` is omitted, the script converts `data/4_profiling/<stage>/<name>_profiling.csv` to `data/5_spec/<stage>/<name>.spec.csv`, preserving the source stage and stripping the `_profiling` suffix. Always go through the script, even for a file with only a couple of rows.
3. **Multiple sources feeding one target table:** run the script again against the second profiling file, pointing `-o` at the same spec file. It appends new rows, skips any `(Source Extract, Source Column)` pair already present (safe to re-run), and preserves everything already filled in on existing rows.
4. **Report the script's output back to the user**: delimiter detected, profile rows found, source extract inferred, any column-name adjustments (blank/duplicate names), suggested Business Role counts, and rows added vs. skipped.
5. **Hand off for completion**: `Target Column Name`, `Type`, `Primary/Unique Key`, `PII/Sensitivity`, `Allowed Values`, `Rejected Values`, `Description`, and `Notes` are the user's to finalize. `Business Role` and `Format` are auto-filled suggestions and should be reviewed. Point them to `references/column_spec_guide.md` for field definitions and the `Business Role` enum, and to `references/canonical_type_mapping.csv` for `Format` values.
6. **Approval gate:** a spec isn't ready for DDL generation until every row's `Status` is `Approved`.
7. **Whole-file lock:** once every row is `Approved`, the script refuses to extend that file further (it will error out rather than append). To change an approved spec, copy it forward to a new version (e.g. `orders.spec.v2.csv`) and reset that copy's rows to `Draft` — don't hand-edit an approved file in place.

## What the script handles for you

- **Delimiter auto-detection**: comma, semicolon, tab, and pipe, detected from the profiling file's own content.
- **Blank column names**: an unnamed profiled column becomes `Column_<position>`.
- **Duplicate column names**: a repeated name gets an incrementing suffix (`Amount`, `Amount` → `Amount`, `Amount_2`).
- **Row order** is always preserved exactly as it appears in the profiling file.
- **Target Table auto-fill** from Source Extract (`fact_balance_sheet_monthly.csv` → `stg_fact_balance_sheet_monthly`).
- **Format auto-fill** from `dtype` (e.g., `float64` → `DECIMAL(18,6)`, `int64` → `BIGINT`, `str` → `TEXT`, `bool` → `BOOLEAN`).
- **Business Role suggestion** from fixed thresholds using `Format`, `distinct_pct`, and `missing_values`.
- **Idempotent re-runs**: running the script twice on the same source against the same spec file adds nothing the second time.
- **Approved-file protection**: refuses to modify a spec where every row is already `Approved`.

If a column name gets adjusted, the script prints the before/after mapping — pass that along to the user rather than silently absorbing it.

## Business Role suggestion rules

The script applies these deterministic threshold rules:

- For numeric formats (`INTEGER`, `BIGINT`, `DECIMAL(18,6)`, `BOOLEAN`):
   - `distinct_pct >= 0.60` and `missing_values = 0` → `Measure`
   - `distinct_pct <= 0.02` and `missing_values = 0` → `Dimension`
   - otherwise → `Dimension Attribute`
- For temporal formats (`DATE`, `TIMESTAMP`):
   - `missing_values = 0` → `Dimension`
   - otherwise → `Dimension Attribute`
- For text-like formats (`TEXT` and fallback):
   - `distinct_pct >= 0.85` and `missing_values = 0` → `Degenerate Dimension`
   - `distinct_pct <= 0.02` and `missing_values = 0` → `Dimension`
   - otherwise → `Dimension Attribute`

These are **initial suggestions** only and must be reviewed.

## Output format

See `references/column_spec_guide.md` for full field definitions. Field names must match exactly:

`Source Extract, Source Column, Target Table, Target Column Name, Type, Business Role, Format, Primary/Unique Key, PII/Sensitivity, Allowed Values, Rejected Values, Description, Notes, Status`

**Type** — `Mandatory` (must exist, no blanks) / `Optional` (must exist, blanks OK, default) / `Ignore` (excluded from load).

## Naming

Call the output a **Table Specification** (e.g. `orders.spec.csv`), not an "Import Specification" — it describes schema, provenance, and analytical metadata for a target table, and that framing keeps it reusable for DDL generation, validation, and semantic modeling, not just the initial load.

## Explicitly out of scope

- Inferring `Type`, `Primary/Unique Key`, or `PII/Sensitivity` from column names or sample data
- Generating DDL directly — that's a separate step, once every row is `Approved`
- Reclassifying `Business Role` once the semantic/data model layer is built — that's a deliberate follow-up review, not something this skill does automatically
- Editing an `Approved` spec in place — copy it forward to a new version instead

## Supersedes

This skill merges and replaces `csv-column-spec-generator` and `column-spec-builder` for this workflow. Remove both from this repo's skills directory to avoid overlapping/conflicting triggers — `csv-column-spec-generator` only if you don't rely on it standalone elsewhere.
