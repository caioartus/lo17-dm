import argparse
import pandas as pd
from lo17_dm.Correcteur import Correcteur
from lo17_dm.Stemmer import SpacyStemmer
from lo17_dm.KeyWordExtractor import KeyWordExtractor

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--lemmes", default="./outputs/lemmes_corpus.tsv",
                        help="Path to the TSV lemma table")

    parser.add_argument("--stopwords", default="./outputs/stop_words.tsv",
                        help="Path to the TSV stop words")

    args = parser.parse_args()

    # Chargement des lemmes pour initialiser le Correcteur
    try:
        lemmas = pd.read_csv(args.lemmes, sep="\t")["token"].tolist()
    except Exception as e:
        print(f"Erreur lors du chargement des lemmes : {e}")
        return

    correcteur = Correcteur(lemmas)
    stemmer = SpacyStemmer()
    
    # On utilise KeyWordExtractor pour avoir le même pipeline que dans le projet
    extractor = KeyWordExtractor(args.stopwords, correcteur, stemmer)

    tests = [
        "je veux des informtions s sur les orgnissasion de reshershe autur du plstic",
        "inaugration de lenemain",
        "donne moi une analyse",
        "Documents qui prlent de vande",
    ]

    print("\n===== TESTS DU PIPELINE DE NORMALISATION =====\n")

    for req in tests:
        print(f"Requete : {req}")
        resultat = extractor.normalize_terms(req)
        print(f"Normalisation : {resultat}\n")

    print("\n===== TESTS EN LIVE =====\n")

    while True:
        try:
            txt = input("Entrer du texte (quit pour quitter): ")
            if txt == "quit":
                break
            resultat = extractor.normalize_terms(txt)
            print("Resultat :", " ".join(resultat))
        except (EOFError, KeyboardInterrupt):
            break


if __name__ == "__main__":
    main()
