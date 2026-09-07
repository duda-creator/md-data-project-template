---
name: md-source-extract-profiling
description: "Use when profiling a CSV, TSV, TXT, or XLSX file in this project and saving a {stem}_profiling.csv report under data/4_profiling."
disable-model-invocation: true
---

# Project File Profiling

Use this skill when the user wants to turn a selected data file in this repository into a profiling report.

The bundled script for this skill is [scripts/profile_file.py](scripts/profile_file.py).

## Inputs

- A single local file path inside the project.
- Supported extensions: `.csv`, `.tsv`, `.txt`, `.xlsx`.

## Workflow

1. Load the selected file into `df` with pandas.
   - `.csv` -> `pd.read_csv(path)`
   - `.tsv` -> `pd.read_csv(path, sep="\t")`
   - `.txt` -> `pd.read_csv(path, sep=None, engine="python")`
   - `.xlsx` -> `pd.read_excel(path)`
2. Build a single profile table. File-level metrics are repeated on each column row so everything stays in one `{stem}_profiling.csv` output:

```python
profile = pd.DataFrame({
    "row_count": len(df),
    "dtype": df.dtypes.astype(str),
    "distinct_values": df.nunique(),
    "distinct_pct": df.nunique().div(len(df)).fillna(0).round(4),
    "missing_values": df.isna().sum(),
    "missing_pct": df.isna().sum().div(len(df)).fillna(0).round(4),
    "blank_string_count": ...,   # string columns only
    "zero_count": ...,           # numeric columns only
    "negative_count": ...,       # numeric columns only
    "constant_column": df.nunique().le(1),
    "min_length": ...,           # string columns only
    "max_length": ...,           # string columns only
    "min": df.min(numeric_only=False),
    "max": df.max(numeric_only=False),
    "duplicate_row_count": int(df.duplicated().sum()),
}).reset_index().rename(columns={"index": "column"})
```

3. Create `data/4_profiling/{stage}` if the source file lives under `data/{stage}` and `{stage}` is one of `1_raw`, `2_interim`, or `3_processed`. Otherwise, create `data/4_profiling`.
4. Save the output as `data/4_profiling/{stage}/{stem}_profiling.csv` for staged data files, or `data/4_profiling/{stem}_profiling.csv` otherwise.
5. Confirm the file was written and report the output path.

## Run

From the repository root:

```powershell
uv run --extra profiling python .github/skills/md-source-extract-profiling/scripts/profile_file.py data/1_raw/source.csv
```

Optional flags:

- `--sheet` for a specific Excel sheet name or index.
- `--delimiter` for `.txt` files when delimiter inference is not reliable.

## Checks

- Preserve the source file name stem exactly.
- Preserve the source stage folder when the input path is under `data/1_raw`, `data/2_interim`, or `data/3_processed`.
- If the file has multiple sheets and the user does not specify one, use the first sheet.
- If pandas cannot infer a `.txt` delimiter, ask the user what delimiter to use.
- If `openpyxl` is missing in the active environment, install it before reading `.xlsx` files.

## Example prompts

- `/md-source-extract-profiling data/1_raw/fact_balance_sheet_monthly.csv`
- `/md-source-extract-profiling data/2_interim/customer_dump.xlsx`
- `/md-source-extract-profiling profile the selected TSV and save the report`