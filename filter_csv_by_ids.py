#!/usr/bin/env python
import argparse
import csv
from pathlib import Path


def parse_args(default_csv_path: str) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Фильтрует CSV файл, оставляя только строки с ID из списка"
    )
    p.add_argument(
        "csv_path",
        nargs="?",
        default=default_csv_path,
        help="Путь к исходному CSV файлу",
    )
    p.add_argument(
        "--ids-file",
        default="matched_ids.txt",
        help="Путь к файлу со списком ID (по умолчанию: matched_ids.txt)",
    )
    p.add_argument(
        "--output",
        help="Путь к выходному CSV файлу (по умолчанию: <csv_path>_filtered.csv)",
    )
    p.add_argument(
        "--delimiter",
        help="Разделитель CSV, например ',' ';' или '\\t'. Если не указан, определяется автоматически.",
    )
    return p.parse_args()


def load_ids(ids_file: str) -> set:
    """Загружает список ID из текстового файла."""
    ids = set()
    with open(ids_file, "r", encoding="utf-8") as f:
        for line in f:
            id_val = line.strip()
            if id_val:
                ids.add(id_val)
    return ids


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    default_csv_path = str(script_dir / "walter-humanizer-text-10k.csv")
    args = parse_args(default_csv_path)

    # Определяем путь к файлу ID (относительно директории скрипта, если не абсолютный)
    ids_file_path = args.ids_file
    if not Path(ids_file_path).is_absolute():
        ids_file_path = str(script_dir / args.ids_file)

    # Определяем путь к CSV (относительно директории скрипта, если не абсолютный)
    csv_path = args.csv_path
    if not Path(csv_path).is_absolute():
        csv_path = str(script_dir / args.csv_path)

    # Загружаем список ID
    print(f"Загрузка ID из {ids_file_path}...")
    ids_set = load_ids(ids_file_path)
    print(f"Загружено {len(ids_set)} уникальных ID")

    # Определяем путь к выходному файлу
    if args.output:
        output_path = args.output
        if not Path(output_path).is_absolute():
            output_path = str(script_dir / args.output)
    else:
        csv_path_obj = Path(csv_path)
        output_path = str(csv_path_obj.parent / f"{csv_path_obj.stem}_filtered{csv_path_obj.suffix}")

    # Определяем разделитель
    delimiter = args.delimiter if args.delimiter else ","

    # Обрабатываем CSV
    total_rows = 0
    filtered_rows = 0
    sep_line = None

    with open(
        csv_path,
        "r",
        encoding="utf-8",
        errors="replace",
        newline="",
    ) as infile:
        # Проверяем наличие sep= строки
        first_line = infile.readline()
        if first_line.lower().startswith("sep="):
            sep_line = first_line
        else:
            infile.seek(0)

        reader = csv.DictReader(infile, delimiter=delimiter, strict=False)

        if not reader.fieldnames:
            raise SystemExit("CSV файл не содержит заголовков.")

        # Открываем выходной файл для записи
        with open(
            output_path,
            "w",
            encoding="utf-8",
            newline="",
        ) as outfile:
            # Записываем sep= строку, если она была
            if sep_line:
                outfile.write(sep_line)

            writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames, delimiter=delimiter)
            writer.writeheader()

            for row in reader:
                total_rows += 1

                # Пропускаем пустые строки
                if not row:
                    continue
                if all((value is None) or (str(value).strip() == "") for value in row.values()):
                    continue

                # Проверяем, есть ли ID в списке
                row_id = (row.get("id") or "").strip()
                if row_id in ids_set:
                    writer.writerow(row)
                    filtered_rows += 1

    print(f"Обработано строк: {total_rows}")
    print(f"Отфильтровано строк: {filtered_rows}")
    print(f"Результат сохранен в: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
