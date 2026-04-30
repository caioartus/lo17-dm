#!/usr/bin/env python3
from pathlib import Path

from lo17_dm.Pretraiteur import Pretraiteur


def main() -> None:
    file_path = Path("./test_data/test_requetes.txt")

    pretraiteur = Pretraiteur(
        lemma_table_path="outputs/lemmes_corpus.csv",
        rubriques_index_path="outputs/index_rubrique.tsv",
    )
    content = file_path.read_text(encoding="utf-8")

    print(f"Testing Pretraiteur on: {file_path}")
    print("=" * 80)

    for lineno, raw_line in enumerate(content.splitlines(), start=1):
        sentence = raw_line.strip()
        if not sentence:
            continue

        pretraiteur.treat_request(sentence, sub_table_csv="../outputs/sub_table.tsv")

        print(pretraiteur.requete_dict)

        print("-" * 80)


if __name__ == "__main__":
    main()
