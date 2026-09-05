---
name: md-flat-file-profiling
description: Use when profiling a CSV, TSV, TXT, or XLSX file in this project and saving a column-level report under data/4_profiling.
---

# Flat-file profiling

This optional capability creates a column-level profiling report for a flat file in `data/1_raw`, `data/2_interim`, or `data/3_processed`.

## Run

From the repository root:

```powershell
uv run --extra profiling python .github/skills/md-flat-file-profiling/scripts/profile_file.py data/1_raw/source.csv
```

Use `--sheet` for a specific workbook sheet and `--delimiter` when delimiter detection for a text file needs an explicit value.

## Output

The script writes `data/4_profiling/<stage>/<stem>_profiling.csv` when the source is in a recognized data stage. Files outside the project data stages are written to `data/4_profiling/`.

## Notes

- Supported files are CSV, TSV, TXT, and XLSX.
- This capability is optional. Projects may ingest, transform, or validate data by another method.
- The report is descriptive only; it does not modify the source file or create a target dataset.
