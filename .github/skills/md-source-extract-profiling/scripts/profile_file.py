from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from pandas.api.types import is_numeric_dtype, is_string_dtype

ROOT = Path(__file__).resolve().parents[4]
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
        if delimiter:
            return pd.read_csv(path, sep=delimiter)
        return pd.read_csv(path, sep=None, engine="python")

    if suffix == ".xlsx":
        try:
            return pd.read_excel(path, sheet_name=sheet if sheet is not None else 0)
        except ImportError as exc:
            raise ImportError(
                "openpyxl is required to read .xlsx files in this project."
            ) from exc

    raise ValueError(f"Unsupported file type: {suffix}")


def build_profile(df: pd.DataFrame) -> pd.DataFrame:
    row_count = len(df)
    duplicate_row_count = int(df.duplicated().sum())
    distinct_values = df.nunique()
    missing_values = df.isna().sum()

    blank_string_count = pd.Series(pd.NA, index=df.columns, dtype="object")
    min_length = pd.Series(pd.NA, index=df.columns, dtype="object")
    max_length = pd.Series(pd.NA, index=df.columns, dtype="object")
    zero_count = pd.Series(pd.NA, index=df.columns, dtype="object")
    negative_count = pd.Series(pd.NA, index=df.columns, dtype="object")

    for column in df.columns:
        series = df[column]

        if is_string_dtype(series) or series.dtype == object:
            non_null_strings = series.dropna().astype(str)
            blank_string_count[column] = int(non_null_strings.str.strip().eq("").sum())

            lengths = non_null_strings.str.len()
            if not lengths.empty:
                min_length[column] = int(lengths.min())
                max_length[column] = int(lengths.max())

        if is_numeric_dtype(series):
            non_null_numeric = series.dropna()
            zero_count[column] = int(non_null_numeric.eq(0).sum())
            negative_count[column] = int(non_null_numeric.lt(0).sum())

    return (
        pd.DataFrame(
            {
                "row_count": row_count,
                "dtype": df.dtypes.astype(str),
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
                "min": df.min(numeric_only=False),
                "max": df.max(numeric_only=False),
                "duplicate_row_count": duplicate_row_count,
            }
        )
        .reset_index()
        .rename(columns={"index": "column"})
    )


def resolve_output_dir(path: Path) -> Path:
    output_root = ROOT / "data" / "4_profiling"

    try:
        relative_parts = path.resolve().relative_to(ROOT.resolve()).parts
    except ValueError:
        return output_root

    if len(relative_parts) >= 3 and relative_parts[0] == "data":
        stage = relative_parts[1]
        if stage in PROFILED_DATA_STAGES:
            return output_root / stage

    return output_root


def profile_file(
    path: Path, sheet: str | int | None = None, delimiter: str | None = None
) -> Path:
    df = load_dataframe(path, sheet=sheet, delimiter=delimiter)
    profile = build_profile(df)

    output_dir = resolve_output_dir(path)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{path.stem}_profiling.csv"
    profile.to_csv(output_path, index=False)
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Profile a project data file and save the result to data/4_profiling."
    )
    parser.add_argument("path", help="Path to a .csv, .tsv, .txt, or .xlsx file")
    parser.add_argument(
        "--sheet", help="Excel sheet name or 0-based sheet index", default=None
    )
    parser.add_argument("--delimiter", help="Delimiter for .txt files", default=None)
    return parser.parse_args()


def coerce_sheet(value: str | None) -> str | int | None:
    if value is None:
        return None
    if value.isdigit():
        return int(value)
    return value


def main() -> int:
    args = parse_args()
    path = Path(args.path)
    sheet = coerce_sheet(args.sheet)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    output_path = profile_file(path, sheet=sheet, delimiter=args.delimiter)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
