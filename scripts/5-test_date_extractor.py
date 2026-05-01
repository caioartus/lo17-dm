#!/usr/bin/env python3
from pathlib import Path

from lo17_dm.DateExtractor import DateExtractor


def main() -> None:
    file_path = Path("./test_data/test_requetes.txt")

    extractor = DateExtractor()
    content = file_path.read_text(encoding="utf-8")

    print(f"Testing DateExtractor on: {file_path}")
    print("=" * 80)

    for lineno, raw_line in enumerate(content.splitlines(), start=1):
        sentence = raw_line.strip()
        if not sentence:
            continue

        from_date, to_date, anti_date, _ = extractor.extract(sentence)

        print(f"{lineno:03d}: {sentence}")
        print(f"    from_date: {from_date}")
        print(f"    to_date:   {to_date}")
        print(f"    anti_date:   {anti_date}")
        print()


if __name__ == "__main__":
    main()
