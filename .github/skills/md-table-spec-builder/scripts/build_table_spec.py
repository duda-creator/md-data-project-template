from __future__ import annotations

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


def detect_delimiter(sample: str) -> str:
    try:
        return (
            csv.Sniffer()
            .sniff(sample, delimiters="".join(CANDIDATE_DELIMITERS))
            .delimiter
        )
    except csv.Error:
        first_line = sample.splitlines()[0] if sample.splitlines() else ""
        counts = {
            delimiter: first_line.count(delimiter) for delimiter in CANDIDATE_DELIMITERS
        }
        best = max(counts, key=counts.get)
        return best if counts[best] else ","


def read_profile_rows(input_path: Path) -> tuple[list[dict[str, str]], str]:
    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        if not sample.strip():
            raise ValueError(f"{input_path} is empty.")
        delimiter = detect_delimiter(sample)
        reader = csv.DictReader(handle, delimiter=delimiter)
        fields = {field.strip() for field in reader.fieldnames or [] if field}
        missing = PROFILE_REQUIRED_COLUMNS - fields
        if missing:
            raise ValueError(f"{input_path} is missing: {', '.join(sorted(missing))}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"{input_path} has no profiling rows.")
    return rows, delimiter


def normalized_column_names(profile_rows: list[dict[str, str]]) -> list[str]:
    counts: dict[str, int] = {}
    result: list[str] = []
    for position, row in enumerate(profile_rows, start=1):
        name = (row.get("column") or "").strip() or f"Column_{position}"
        counts[name] = counts.get(name, 0) + 1
        result.append(name if counts[name] == 1 else f"{name}_{counts[name]}")
    return result


def profile_base_name(input_path: Path) -> str:
    return input_path.stem.removesuffix("_profiling")


def infer_source_extract_name(input_path: Path) -> str:
    return f"{profile_base_name(input_path)}.csv"


def infer_target_table_name(source_extract: str) -> str:
    return f"stg_{Path(source_extract).stem}"


def default_output_path(input_path: Path) -> Path:
    parts = list(input_path.parts)
    if "4_profiling" in parts:
        index = parts.index("4_profiling")
        parts[index] = "5_spec"
        return Path(*parts[:-1]) / f"{profile_base_name(input_path)}.spec.csv"
    return input_path.with_name(f"{profile_base_name(input_path)}.spec.csv")


def canonical_format_from_dtype(dtype: str) -> str:
    normalized = dtype.strip().lower()
    if normalized in {"bool", "boolean"}:
        return "BOOLEAN"
    if "datetime" in normalized or "timestamp" in normalized:
        return "TIMESTAMP"
    if normalized == "date":
        return "DATE"
    if "int" in normalized:
        return "BIGINT"
    if any(value in normalized for value in {"float", "double", "decimal"}):
        return "DECIMAL(18,6)"
    return "TEXT"


def to_float(value: str | None) -> float:
    try:
        return float(value or 0)
    except ValueError:
        return 0.0


def to_int(value: str | None) -> int:
    return int(to_float(value))


def suggest_business_role(
    format_value: str, distinct_pct: float, missing_values: int
) -> str:
    if format_value in {"INTEGER", "BIGINT", "DECIMAL(18,6)", "BOOLEAN"}:
        if distinct_pct >= 0.60 and missing_values == 0:
            return "Measure"
        if distinct_pct <= 0.02 and missing_values == 0:
            return "Dimension"
        return "Dimension Attribute"
    if format_value in {"DATE", "TIMESTAMP"}:
        return "Dimension" if missing_values == 0 else "Dimension Attribute"
    if distinct_pct >= 0.85 and missing_values == 0:
        return "Degenerate Dimension"
    if distinct_pct <= 0.02 and missing_values == 0:
        return "Dimension"
    return "Dimension Attribute"


def build_rows(
    source_extract: str, profile_rows: list[dict[str, str]], names: list[str]
) -> list[dict[str, str]]:
    target_table = infer_target_table_name(source_extract)
    rows: list[dict[str, str]] = []
    for source_column, profile_row in zip(names, profile_rows):
        format_value = canonical_format_from_dtype(profile_row.get("dtype", ""))
        role = suggest_business_role(
            format_value,
            to_float(profile_row.get("distinct_pct")),
            to_int(profile_row.get("missing_values")),
        )
        rows.append(
            {
                "Source Extract": source_extract,
                "Source Column": source_column,
                "Target Table": target_table,
                "Target Column Name": "",
                "Type": "Optional",
                "Business Role": role,
                "Format": format_value,
                "Primary/Unique Key": "",
                "PII/Sensitivity": "",
                "Allowed Values": "",
                "Rejected Values": "",
                "Description": "",
                "Notes": "Suggested from profiling statistics; review required.",
                "Status": "Draft",
            }
        )
    return rows


def read_existing_spec(output_path: Path) -> list[dict[str, str]]:
    with output_path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_spec(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SPEC_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_spec(
    input_path: Path, output_path: Path | None = None
) -> tuple[Path, int, int, str]:
    profile_rows, delimiter = read_profile_rows(input_path)
    source_extract = infer_source_extract_name(input_path)
    resolved_output = output_path or default_output_path(input_path)
    existing_rows = (
        read_existing_spec(resolved_output) if resolved_output.exists() else []
    )
    existing_pairs = {
        (row.get("Source Extract", ""), row.get("Source Column", ""))
        for row in existing_rows
    }
    candidates = build_rows(
        source_extract, profile_rows, normalized_column_names(profile_rows)
    )
    new_rows = [
        row
        for row in candidates
        if (row["Source Extract"], row["Source Column"]) not in existing_pairs
    ]
    write_spec(existing_rows + new_rows, resolved_output)
    return resolved_output, len(new_rows), len(candidates) - len(new_rows), delimiter


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a Table Specification from a profiling report."
    )
    parser.add_argument("input_file", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    if not args.input_file.exists():
        print(f"Error: input file not found: {args.input_file}", file=sys.stderr)
        return 1
    try:
        output_path, added, skipped, delimiter = build_spec(
            args.input_file, args.output
        )
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(f"Detected delimiter: {DELIMITER_NAMES.get(delimiter, repr(delimiter))}")
    print(f"Added {added} row(s); skipped {skipped} existing row(s).")
    print(f"Specification written to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
