"""
Compare latency metrics between two Excel files.

Inputs:
  - latency.xlsx
  - latency_after_changes.xlsx

Required columns (case-insensitive):
  - word_count
  - latency_seconds
  - action

Outputs:
  - exact_word_count_diff.csv (mean latency per word_count match)
  - binned_latency_diff.csv (mean latency per bin)
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd


FILE_1 = Path("latency.xlsx")
FILE_2 = Path("latency_after_changes.xlsx")


def read_latency_file(path: Path) -> pd.DataFrame:
    """Read latency file and normalize column names."""
    df = pd.read_excel(path)
    print(df.columns)
    col_map = {str(col).strip().lower(): col for col in df.columns}
    print(col_map)
    required = ["word_count", "latency_seconds", "action"]
    missing = [name for name in required if name not in col_map]
    if missing:
        raise ValueError(f"Missing columns in {path.name}: {', '.join(missing)}")
    df = df[
        [
            col_map["word_count"],
            col_map["latency_seconds"],
            col_map["action"],
        ]
    ].rename(
        columns={
            col_map["word_count"]: "word_count",
            col_map["latency_seconds"]: "latency_seconds",
            col_map["action"]: "action",
        }
    )
    return df


def main() -> None:
    if not FILE_1.exists():
        raise FileNotFoundError(f"Missing input file: {FILE_1}")
    if not FILE_2.exists():
        raise FileNotFoundError(f"Missing input file: {FILE_2}")

    df1 = read_latency_file(FILE_1)
    df2 = read_latency_file(FILE_2)

    # Filter by action and drop rows with missing values
    df1 = df1[df1["action"].astype(str).str.lower() == "humanize"]
    df2 = df2[df2["action"].astype(str).str.lower() == "humanize"]
    df1 = df1.dropna(subset=["word_count", "latency_seconds"])
    df2 = df2.dropna(subset=["word_count", "latency_seconds"])

    # Exact matches by word_count (mean latency per word_count)
    exact_1 = df1.groupby("word_count", as_index=False)["latency_seconds"].agg(
        latency_seconds_before="mean",
        count_before="size",
    )
    exact_2 = df2.groupby("word_count", as_index=False)["latency_seconds"].agg(
        latency_seconds_after="mean",
        count_after="size",
    )
    exact = exact_1.merge(exact_2, on="word_count", how="inner")
    exact["diff_percent"] = (
        (exact["latency_seconds_after"] - exact["latency_seconds_before"])
        / exact["latency_seconds_before"].replace(0, pd.NA)
    ) * 100
    exact.to_csv("exact_word_count_diff.csv", index=False)

    # Bin edges from combined word_count to ensure same boundaries
    combined_words = pd.concat([df1["word_count"], df2["word_count"]], ignore_index=True)
    _, bin_edges = pd.qcut(combined_words, q=4, duplicates="drop", retbins=True)

    if len(bin_edges) <= 2:
        raise ValueError("Not enough unique word_count values to create 10 bins.")

    df1["word_bin"] = pd.cut(df1["word_count"], bins=bin_edges, include_lowest=True)
    df2["word_bin"] = pd.cut(df2["word_count"], bins=bin_edges, include_lowest=True)

    bin_1 = df1.groupby("word_bin", as_index=False)["latency_seconds"].agg(
        latency_seconds_before="mean",
        count_before="size",
    )
    bin_2 = df2.groupby("word_bin", as_index=False)["latency_seconds"].agg(
        latency_seconds_after="mean",
        count_after="size",
    )
    binned = bin_1.merge(bin_2, on="word_bin", how="outer").sort_values("word_bin")
    binned["diff_percent"] = (
        (binned["latency_seconds_after"] - binned["latency_seconds_before"])
        / binned["latency_seconds_before"].replace(0, pd.NA)
    ) * 100
    binned["bin_start"] = binned["word_bin"].apply(lambda interval: interval.left if pd.notna(interval) else pd.NA)
    binned["bin_end"] = binned["word_bin"].apply(lambda interval: interval.right if pd.notna(interval) else pd.NA)
    binned = binned[
        [
            "bin_start",
            "bin_end",
            "count_before",
            "count_after",
            "latency_seconds_before",
            "latency_seconds_after",
            "diff_percent",
        ]
    ]
    binned.to_csv("binned_latency_diff.csv", index=False)

    print("Saved outputs:")
    print(" - exact_word_count_diff.csv")
    print(" - binned_latency_diff.csv")


if __name__ == "__main__":
    main()
