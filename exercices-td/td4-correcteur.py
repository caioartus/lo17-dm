import argparse
from lo17_dm.Pretraiteur import Pretraiteur


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--lemmes", default="./outputs/lemmes_corpus.tsv",
                        help="Path to the TSV lemma table")

    parser.add_argument("--stems", default="./outputs/spacy_stems.tsv",
                        help="Path to the TSV stem table")

    parser.add_argument("--subtable", default="./outputs/sub_table.tsv",
                        help="Path to the TSV substitution table")

    args = parser.parse_args()

    analyser = Pretraiteur(args.lemmes)

    tests = [
        "je veux des informtions s sur les orgnissasion de reshershe autur du plstic",
        "inaugration de lenemain",
        "donne moi une analyse",
        "Documents qui prlent de vande",
    ]

    print("\n===== TESTS DE LA CLASSE ANALYSER =====\n")

    for req in tests:
        print(f"Requete : {req}")
        resultat = analyser.treat_input(req, args.stems)
        print(f"Correction : {resultat}\n")

    print("\n===== TESTS EN LIVE =====\n")

    while True:
        txt = input("Entrer du texte (quit pour quitter): ")
        if txt == "quit":
            break
        resultat = analyser.treat_input(txt, args.subtable)
        print("Resultat :", " ".join(resultat))


if __name__ == "__main__":
    main()
