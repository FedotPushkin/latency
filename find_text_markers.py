#!/usr/bin/env python
import argparse
import csv
import re
from pathlib import Path


BEGIN_PATTERN = r"(?:begin|beginning)[\s_]+text\s*(?:\u2014+)?"
END_PATTERN = r"(?:end|ending)[\s_]+text\s*(?:\u2014+)?"


def parse_args(default_csv_path: str) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("csv_path", nargs="?", default=default_csv_path)
    p.add_argument(
        "--delimiter",
        help="Delimiter override, e.g. ',' ';' or '\\t'. If omitted, auto-detect.",
    )
    p.add_argument("--case-sensitive", action="store_true")
    p.add_argument("--ids-output")
    return p.parse_args()


def main() -> int:
    default_csv_path = str(
        Path(__file__).resolve().parent / "walter-humanizer-text-10k.csv"
    )
    args = parse_args(default_csv_path)

    flags = 0 if args.case_sensitive else re.IGNORECASE
    begin_re = re.compile(BEGIN_PATTERN, flags)
    end_re = re.compile(END_PATTERN, flags)

    total = 0
    matched = 0
    matched_ids = []
    matched_user_ids = set()
    all_user_ids = set()

    with open(
        args.csv_path,
        "r",
        encoding="utf-8",
        errors="replace",
        newline="",
    ) as f:
        # Check for sep= line and skip it if present
        first_line = f.readline()
        if first_line.lower().startswith("sep="):
            # File pointer is already after sep= line, DictReader will read header next
            pass
        else:
            # Rewind to start - first line is the header
            f.seek(0)

        delimiter = args.delimiter if args.delimiter else ","
        reader = csv.DictReader(f, delimiter=delimiter, strict=False)

        if not reader.fieldnames:
            raise SystemExit("CSV has no header row.")

        for row in reader:
            if not row:
                continue
            if all((value is None) or (str(value).strip() == "") for value in row.values()):
                continue

            total += 1

            user_id = (row.get("user_id_id") or "").strip()
            if user_id:
                all_user_ids.add(user_id)

            output_text = row.get("output_text") or ""

            if begin_re.search(output_text) or end_re.search(output_text):
                matched += 1
                rid = (row.get("id") or "").strip()
                if rid:
                    matched_ids.append(rid)
                if user_id:
                    matched_user_ids.add(user_id)

    freq = (matched / total * 100) if total else 0.0

    if args.ids_output:
        with open(args.ids_output, "w", encoding="utf-8") as out:
            for i in matched_ids:
                out.write(i + "\n")
    else:
        for i in matched_ids:
            print(i)

    print(f"total_rows={total}")
    print(f"matched_rows={matched}")
    print(f"unique_user_ids={len(matched_user_ids)}")
    ratio = len(matched_user_ids) / len(all_user_ids) if all_user_ids else 0
    print(f"unique_user_ratio={ratio:.6f}")
    print(f"frequency_percent={freq:.2f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
