#!/usr/bin/env python3
"""
Build or extend a Table Specification from a profiling report.

Reads a *_profiling.csv report and produces (or extends) a metadata
specification CSV — one row per source column — ready for human review before
it is handed to a later database implementation workflow.

Deterministic enrichments applied by this script:
- Source Extract and Source Column from profiling metadata.
- Target Table inferred from Source Extract as stg_<extract_name_without_extension>.
- Format from profiling dtype.
- Business Role suggestion from threshold rules based on Format,
  distinct_pct, and missing_values.

If the output spec already exists, new rows are appended (existing rows,
including anything already filled in, are preserved). If every existing row
is already Approved, the file is treated as immutable and the script refuses
to touch it — copy it forward to a new version first.

Usage:
    python build_table_spec.py <profiling_file> [-o <output_spec_file>]

Examples:
    python build_table_spec.py data/4_profiling/2_interim/cash_positions_profiling.csv
    python build_table_spec.py data/4_profiling/2_interim/cash_positions_v2_profiling.csv -o data/5_spec/2_interim/cash_positions.spec.csv
"""

import argparse
import csv
import sys
from pathlib import Path

CANDIDATE_DELIMITERS = [",", ";", "\t", "|"]
DELIMITER_NAMES = {",": "comma", ";": "semicolon", "\t": "tab", "|": "pipe"}

PROFILE_REQUIRED_COLUMNS = {"column", "dtype", "distinct_pct", "missing_values"}

SPEC_COLUMNS = [
    "Source Extract",
    "Source Column",
    "Target Table",
    "Target Column Name",
    "Type",
    "Business Role",
    "Format",
    "Primary/Unique Key",
    "PII/Sensitivity",
    "Allowed Values",
    "Rejected Values",
    "Description",
    "Notes",
    "Status",
]

DEFAULT_TYPE = "Optional"
DEFAULT_STATUS = "Draft"


def detect_delimiter(sample: str) -> str:
    """Detect the delimiter from a text sample.

    Tries csv.Sniffer first since it's more robust (handles quoted fields
    correctly). Falls back to counting candidate delimiters in the first
    line if the sniffer can't decide.
    """
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters="".join(CANDIDATE_DELIMITERS))
        return dialect.delimiter
    except csv.Error:
        pass

    lines = sample.splitlines()
    first_line = lines[0] if lines else ""
    counts = {d: first_line.count(d) for d in CANDIDATE_DELIMITERS}
    best = max(counts, key=counts.get)
    return best if counts[best] > 0 else ","


def read_profile_rows(input_path: Path) -> tuple[list[dict], str]:
    """Read profiling rows, returning (rows, delimiter_used)."""
    with open(input_path, "r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        if not sample.strip():
            raise ValueError(
                f"{input_path} appears to be empty — no profiling rows found."
            )
        delimiter = detect_delimiter(sample)
        reader = csv.DictReader(f, delimiter=delimiter)
        if not reader.fieldnames:
            raise ValueError(f"{input_path} has no header row.")

        header = {h.strip() for h in reader.fieldnames if h is not None}
        missing = PROFILE_REQUIRED_COLUMNS - header
        if missing:
            raise ValueError(
                f"{input_path} is missing required profiling columns: {', '.join(sorted(missing))}"
            )

        rows = list(reader)
        if not rows:
            raise ValueError(f"{input_path} has a header but no profiling rows.")
    return rows, delimiter


def dedupe_and_fill_profile_columns(profile_rows: list[dict]) -> list[str]:
    """Preserve row order while making every source column unique and non-blank.

    - Blank names become Column_<position>, e.g. unnamed 3rd row -> Column_3.
    - Duplicate names get an incrementing suffix on the 2nd+ occurrence,
      e.g. Amount, Amount -> Amount, Amount_2.
    """
    seen_counts: dict[str, int] = {}
    result = []
    for position, row in enumerate(profile_rows, start=1):
        raw_name = (row.get("column") or "").strip()
        name = raw_name
        if not name:
            name = f"Column_{position}"
        if name in seen_counts:
            seen_counts[name] += 1
            name = f"{name}_{seen_counts[name]}"
        else:
            seen_counts[name] = 1
        result.append(name)
    return result


def to_float(value: str | None) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def to_int(value: str | None) -> int | None:
    f = to_float(value)
    return int(f) if f is not None else None


def canonical_format_from_dtype(dtype: str) -> str:
    d = dtype.strip().lower()
    if d in {"bool", "boolean"}:
        return "BOOLEAN"
    if "datetime" in d or "timestamp" in d:
        return "TIMESTAMP"
    if d == "date":
        return "DATE"
    if "int" in d:
        return "BIGINT"
    if "float" in d or "double" in d or "decimal" in d:
        return "DECIMAL(18,6)"
    if d in {"str", "string", "object", "category"}:
        return "TEXT"
    return "TEXT"


def suggest_business_role(
    fmt: str, distinct_pct: float | None, missing_values: int | None
) -> str:
    """Deterministic threshold rules for an initial Business Role suggestion."""
    d = distinct_pct if distinct_pct is not None else 0.0
    m = missing_values if missing_values is not None else 0
    numeric_formats = {"INTEGER", "BIGINT", "DECIMAL(18,6)", "BOOLEAN"}

    if fmt in numeric_formats:
        if d >= 0.60 and m <= 0:
            return "Measure"
        if d <= 0.02 and m <= 0:
            return "Dimension"
        return "Dimension Attribute"

    if fmt in {"DATE", "TIMESTAMP"}:
        if m <= 0:
            return "Dimension"
        return "Dimension Attribute"

    if d >= 0.85 and m <= 0:
        return "Degenerate Dimension"
    if d <= 0.02 and m <= 0:
        return "Dimension"
    return "Dimension Attribute"


def build_new_rows(
    source_extract: str, profile_rows: list[dict], column_names: list[str]
) -> list[dict]:
    rows = []
    target_table = infer_target_table_name(source_extract)
    for source_column, profile_row in zip(column_names, profile_rows):
        dtype = (profile_row.get("dtype") or "").strip()
        distinct_pct = to_float(profile_row.get("distinct_pct"))
        missing_values = to_int(profile_row.get("missing_values"))
        fmt = canonical_format_from_dtype(dtype)
        business_role = suggest_business_role(fmt, distinct_pct, missing_values)

        rows.append(
            {
                "Source Extract": source_extract,
                "Source Column": source_column,
                "Target Table": target_table,
                "Target Column Name": "",
                "Type": DEFAULT_TYPE,
                "Business Role": business_role,
                "Format": fmt,
                "Primary/Unique Key": "",
                "PII/Sensitivity": "",
                "Allowed Values": "",
                "Rejected Values": "",
                "Description": "",
                "Notes": (
                    "Auto-suggested from profiling thresholds "
                    "(Format + distinct_pct + missing_values); review required"
                ),
                "Status": DEFAULT_STATUS,
            }
        )
    return rows


def read_existing_spec(output_path: Path) -> list[dict]:
    with open(output_path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_spec(rows: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SPEC_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def profile_base_name(input_file: Path) -> str:
    stem = input_file.stem
    return stem[:-10] if stem.endswith("_profiling") else stem


def default_output_path(input_file: Path) -> Path:
    """Prefer data/5_spec/<stage>/<name>.spec.csv for data/4_profiling inputs.
    Falls back to placing the spec next to the input file otherwise.
    """
    base_name = profile_base_name(input_file)
    parts = list(input_file.parts)
    if "4_profiling" in parts:
        idx = parts.index("4_profiling")
        parts[idx] = "5_spec"
        return Path(*parts[:-1]) / f"{base_name}.spec.csv"
    return input_file.with_name(f"{base_name}.spec.csv")


def infer_source_extract_name(input_file: Path) -> str:
    """Infer source extract name from a *_profiling.csv file name."""
    return f"{profile_base_name(input_file)}.csv"


def infer_target_table_name(source_extract: str) -> str:
    """Infer target staging table as stg_<source_extract_stem>."""
    return f"stg_{Path(source_extract).stem}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build or extend a Table Specification from a profiling CSV file."
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the profiling file (typically *_profiling.csv)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Path to the spec file to create or extend (default: inferred from the data/4_profiling -> data/5_spec convention)",
    )
    args = parser.parse_args()

    if not args.input_file.exists():
        print(f"Error: input file not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)

    try:
        profile_rows, delimiter = read_profile_rows(args.input_file)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    column_names = dedupe_and_fill_profile_columns(profile_rows)
    source_extract = infer_source_extract_name(args.input_file)

    if args.output:
        output_path = args.output
    else:
        output_path = default_output_path(args.input_file)
        print(f"No output path given — inferred: {output_path}")

    existing_rows: list[dict] = []
    if output_path.exists():
        existing_rows = read_existing_spec(output_path)

        # Deterministically backfill missing Target Table values in legacy specs.
        for row in existing_rows:
            target_table = (row.get("Target Table") or "").strip()
            source_for_row = (row.get("Source Extract") or "").strip()
            if not target_table and source_for_row:
                row["Target Table"] = infer_target_table_name(source_for_row)

        # Whole-file immutability: once every row is Approved, the file is locked.
        if existing_rows and all(
            r.get("Status", "").strip() == "Approved" for r in existing_rows
        ):
            print(
                f"Error: {output_path} is fully Approved and is treated as immutable.\n"
                f"Copy it forward to a new version (e.g. {output_path.stem}.v2.csv) before extending it.",
                file=sys.stderr,
            )
            sys.exit(1)

        already_present = {
            (r.get("Source Extract", ""), r.get("Source Column", ""))
            for r in existing_rows
        }
        new_rows = [
            row
            for row in build_new_rows(source_extract, profile_rows, column_names)
            if (row["Source Extract"], row["Source Column"]) not in already_present
        ]
        skipped = len(profile_rows) - len(new_rows)
    else:
        new_rows = build_new_rows(source_extract, profile_rows, column_names)
        skipped = 0

    write_spec(existing_rows + new_rows, output_path)

    print(f"Detected delimiter: {DELIMITER_NAMES.get(delimiter, repr(delimiter))}")
    print(f"Profile rows found: {len(profile_rows)}")
    print(f"Source extract inferred: {source_extract}")

    adjustments = [
        (raw.strip() or "(blank)", new)
        for raw, new in zip(
            [(r.get("column") or "") for r in profile_rows], column_names
        )
        if (raw.strip() or "(blank)") != new
    ]
    if adjustments:
        print("Adjusted names (blank/duplicate headers):")
        for original, new in adjustments:
            print(f"  {original!r} -> {new!r}")

    if skipped:
        print(
            f"Skipped {skipped} row(s) already present in the spec for this source extract."
        )

    by_role: dict[str, int] = {}
    for row in new_rows:
        role = row["Business Role"]
        by_role[role] = by_role.get(role, 0) + 1
    if by_role:
        print("Suggested Business Role counts:")
        for role in sorted(by_role):
            print(f"  {role}: {by_role[role]}")

    print(f"Added {len(new_rows)} new row(s).")
    print(f"Specification written to: {output_path}")


if __name__ == "__main__":
    main()
