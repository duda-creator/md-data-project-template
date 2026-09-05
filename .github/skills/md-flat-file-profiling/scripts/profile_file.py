from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from pandas.api.types import is_numeric_dtype, is_string_dtype

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SUPPORTED_EXTENSIONS = {".csv", ".tsv", ".txt", ".xlsx"}
PROFILED_DATA_STAGES = {"1_raw", "2_interim", "3_processed"}


def load_dataframe(
    path: Path, sheet: str | int | None = None, delimiter: str | None = None
) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {suffix}")
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix == ".tsv":
        return pd.read_csv(path, sep="\t")
    if suffix == ".txt":
        return pd.read_csv(path, sep=delimiter, engine="python")
    try:
        return pd.read_excel(path, sheet_name=sheet if sheet is not None else 0)
    except ImportError as exc:
        raise ImportError("openpyxl is required to read XLSX files.") from exc


def build_profile(dataframe: pd.DataFrame) -> pd.DataFrame:
    row_count = len(dataframe)
    distinct_values = dataframe.nunique()
    missing_values = dataframe.isna().sum()
    blank_string_count = pd.Series(pd.NA, index=dataframe.columns, dtype="object")
    min_length = pd.Series(pd.NA, index=dataframe.columns, dtype="object")
    max_length = pd.Series(pd.NA, index=dataframe.columns, dtype="object")
    zero_count = pd.Series(pd.NA, index=dataframe.columns, dtype="object")
    negative_count = pd.Series(pd.NA, index=dataframe.columns, dtype="object")

    for column in dataframe.columns:
        series = dataframe[column]
        if is_string_dtype(series) or series.dtype == object:
            strings = series.dropna().astype(str)
            blank_string_count[column] = int(strings.str.strip().eq("").sum())
            lengths = strings.str.len()
            if not lengths.empty:
                min_length[column] = int(lengths.min())
                max_length[column] = int(lengths.max())
        if is_numeric_dtype(series):
            numeric = series.dropna()
            zero_count[column] = int(numeric.eq(0).sum())
            negative_count[column] = int(numeric.lt(0).sum())

    return (
        pd.DataFrame(
            {
                "row_count": row_count,
                "dtype": dataframe.dtypes.astype(str),
                "distinct_values": distinct_values,
                "distinct_pct": distinct_values.div(row_count).fillna(0).round(4),
                "missing_values": missing_values,
                "missing_pct": missing_values.div(row_count).fillna(0).round(4),
                "blank_string_count": blank_string_count,
                "zero_count": zero_count,
                "negative_count": negative_count,
                "constant_column": distinct_values.le(1),
                "min_length": min_length,
                "max_length": max_length,
                "min": dataframe.min(numeric_only=False),
                "max": dataframe.max(numeric_only=False),
                "duplicate_row_count": int(dataframe.duplicated().sum()),
            }
        )
        .reset_index()
        .rename(columns={"index": "column"})
    )


def resolve_output_dir(path: Path) -> Path:
    output_root = PROJECT_ROOT / "data" / "4_profiling"
    try:
        relative_parts = path.resolve().relative_to(PROJECT_ROOT.resolve()).parts
    except ValueError:
        return output_root
    if len(relative_parts) >= 3 and relative_parts[0] == "data":
        source_stage = relative_parts[1]
        if source_stage in PROFILED_DATA_STAGES:
            return output_root / source_stage
    return output_root


def profile_file(
    path: Path, sheet: str | int | None = None, delimiter: str | None = None
) -> Path:
    profile = build_profile(load_dataframe(path, sheet=sheet, delimiter=delimiter))
    output_dir = resolve_output_dir(path)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{path.stem}_profiling.csv"
    profile.to_csv(output_path, index=False)
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a flat-file profiling report.")
    parser.add_argument("path", type=Path)
    parser.add_argument("--sheet", default=None)
    parser.add_argument("--delimiter", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.path.exists():
        raise FileNotFoundError(f"File not found: {args.path}")
    sheet = (
        int(args.sheet)
        if args.sheet is not None and args.sheet.isdigit()
        else args.sheet
    )
    print(profile_file(args.path, sheet=sheet, delimiter=args.delimiter))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
