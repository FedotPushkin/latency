#!/usr/bin/env python
import argparse
import csv
import re
from pathlib import Path


BEGIN_PATTERN = r"(?:begin|beginning)[\s_]+text\s*(?:\u2014+)?"
END_PATTERN = r"(?:end|ending)[\s_]+text\s*(?:\u2014+)?"
def strip_markers(text: str) -> str:
    """
    Delete all characters before BEGIN_TEXT marker and/or after END_TEXT marker.
    
    Markers can be absent - if a marker doesn't exist, no deletion occurs for that side.
    - If BEGIN_TEXT marker exists: delete everything before it
    - If END_TEXT marker exists: delete everything after it

    Handles various cases:
    - Case-insensitive matching (e.g., begin_text, Begin_Text, BEGIN_TEXT)
    - Alternative spellings (e.g., beginning, begining, beginning text)
    - Multiple whitespace and newline variations
    - Underscore or space separators (BEGIN_TEXT or BEGIN TEXT)
    - Markers with em-dashes (—-)
    - Unicode and multi-language text
    - Graceful fallback for non-string inputs

    Args:
        text: Input text potentially containing markers

    Returns:
        Text with everything before BEGIN_TEXT and/or after END_TEXT deleted
    """
    if not isinstance(text, str):
        return text

    original_text = text
    try:
        # Strip leading/trailing whitespace
        text = text.strip()

        if not text:
            return text
        
        # Pattern to find BEGIN_TEXT marker
        begin_pattern = r'(?:begin|beginning)[\s_]+text\s*(?:—+)?'
        begin_match = re.search(begin_pattern, text, flags=re.IGNORECASE)

        # Pattern to find END_TEXT marker
        end_pattern = r'(?:end|ending)[\s_]+text\s*(?:—+)?'
        end_match = re.search(end_pattern, text, flags=re.IGNORECASE)
        # Delete everything before BEGIN_TEXT marker (if it exists)
        if begin_match:
            text = text[begin_match.end():]

        # Delete everything after END_TEXT marker (if it exists)
        if end_match:
            # Need to re-search in case text was modified after begin marker removal
            end_match = re.search(end_pattern, text, flags=re.IGNORECASE)
            if end_match:
                text = text[:end_match.start()]

        # Final cleanup: remove excess whitespace while preserving
        # internal structure and respecting multi-language spacing rules
        text = text.strip()

        return text

    except (TypeError, AttributeError) as e:
        print(f"Error stripping markers: {e}")
        return original_text

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
    all_ids = []
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

            rid = (row.get("id") or "").strip()
            if rid:
                all_ids.append(rid)

            output_text = row.get("output_text") or ""
            #output_text = strip_markers(output_text)
            if begin_re.search(output_text) or end_re.search(output_text):
                matched += 1
                if rid:
                    matched_ids.append(rid)
                if user_id:
                    matched_user_ids.add(user_id)

    freq = (matched / total * 100) if total else 0.0

    # Выгружаем matched IDs в txt файл
    matched_ids_output_file = args.ids_output if args.ids_output else "matched_ids_fixed.txt"
    with open(matched_ids_output_file, "w", encoding="utf-8") as out:
        for i in matched_ids:
            out.write(i + "\n")

    # Выгружаем все ID в txt файл
    ids_output_file = "all_ids.txt"
    with open(ids_output_file, "w", encoding="utf-8") as out:
        for i in all_ids:
            out.write(i + "\n")

    print(f"total_rows={total}")
    print(f"matched_rows={matched}")
    print(f"unique_user_ids={len(matched_user_ids)}")
    ratio = len(matched_user_ids) / len(all_user_ids) if all_user_ids else 0
    print(f"unique_user_ratio={ratio:.6f}")
    print(f"frequency_percent={freq:.2f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
