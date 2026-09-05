---
name: md-table-spec-builder
description: Use when turning a profiling report into an optional, reviewable table specification for a warehouse or staging workflow.
---

# Table specification builder

This optional capability creates or extends a Table Specification from a profiling report. It supports a warehouse-style workflow without choosing a platform or deploying anything.

## Run

```powershell
uv run python .github/skills/md-table-spec-builder/scripts/build_table_spec.py data/4_profiling/2_interim/orders_profiling.csv
```

The default output is `data/5_spec/<stage>/<name>.spec.csv`. Use `--output` to choose a different location.

## Behavior

- Extracts source provenance and column names from the report.
- Suggests a canonical format and business role for review.
- Uses `stg_<source_name>` as a starting target-table name, following the optional staging convention.
- Adds only source-column pairs not already present, making repeat runs idempotent.
- Creates rows with `Status = Draft`.
- Does not lock an approved file or require version-copying. Governance enforcement belongs to the project-specific implementation selected later.

## Review

Review target names, requirements, business roles, formats, keys, sensitivity, descriptions, and status before using the specification as a project contract. See [references/column_spec_guide.md](references/column_spec_guide.md).
