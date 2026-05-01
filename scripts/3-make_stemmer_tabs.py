import os
import sys

from lxml import etree

from lo17_dm.Stemmer import SnowStemmer, SpacyStemmer

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))


def main():
    """Generation de tableaux token, lemme pour analyse"""
    script_dir = os.path.dirname(os.path.abspath(__file__))

    all_text = []
    tree = etree.ElementTree().parse(
        os.path.join(script_dir, "../outputs/nostopwords_corpus.xml")
    )
    for document in tree.iter("document"):
        titre_elem = document.find("titre")
        texte_elem = document.find("texte")
        if titre_elem is None or texte_elem is None:
            raise ValueError("Nones found, make sure corpus is correctly parsed.")
        if titre_elem.text is not None:
            all_text.append(titre_elem.text)
        if texte_elem.text is not None:
            all_text.append(texte_elem.text)

    all_text_str = " ".join(all_text)

    stemmer = SpacyStemmer()
    stemmer.make_table(all_text_str).to_csv(
        os.path.join(script_dir, "../outputs/spacy_stems.tsv"), sep="\t", index=False
    )

    stemmer = SnowStemmer()

    stemmer.make_table(all_text_str).to_csv(
        os.path.join(script_dir, "../outputs/snow_stems.tsv"), sep="\t", index=False
    )


if __name__ == "__main__":
    main()
