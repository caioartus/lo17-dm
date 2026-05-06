import argparse
import time
from pathlib import Path

from lo17_dm.Interface import SEP, display_results
from lo17_dm.Pretraiteur import Pretraiteur
from lo17_dm.SearchEngine import SearchEngine

OUTPUTS = Path(__file__).parent.parent / "outputs"
CORPUS_NAME = "corpus"
LEMMA_NAME = "lemmes_corpus"

SORT_LABELS = {
    "1": "relevance",
    "2": "date_asc",
    "3": "date_desc",
}

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default=OUTPUTS,
                        help="Directory containing index and corpus files")
    parser.add_argument("--corpus", default=CORPUS_NAME,
                        help="Name of the corpus XML file (without extension)")
    parser.add_argument("--lemma", default=LEMMA_NAME,
                        help="Name of the lemma TSV file (without extension)")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    corpus_path = outdir / f"{args.corpus}.xml"
    lemma_table_path = outdir / f"{args.lemma}.tsv"
    rubrique_index_path = outdir / "index" / "index_rubrique.tsv"
    stop_words_path = outdir / "stop_words.tsv"

    print(SEP)
    print("  Moteur de recherche ADIT  -  chargement en cours…")
    print(SEP)

    pretraiteur = Pretraiteur(
        lemma_table_path=lemma_table_path,
        rubriques_index_path=rubrique_index_path,
        stop_words_path=stop_words_path,
    )
    engine = SearchEngine(output_dir=outdir, corpus_path=corpus_path)

    print(f"  {len(engine.documents)} documents chargés.")
    print("  Tapez 'quitter' pour quitter.\n")

    while True:
        print("  Tri : [1] Pertinence (défaut)  [2] Date croissante  [3] Date décroissante")
        try:
            query = input("  Requête : ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAu revoir.")
            break

        if query.lower() in ("quitter", "q", "exit", "quit"):
            print("Au revoir.")
            break
        if not query:
            continue

        try:
            sort_choice = input("  Tri [1/2/3] : ").strip()
        except (EOFError, KeyboardInterrupt):
            sort_choice = "1"

        sort_by = SORT_LABELS.get(sort_choice, "relevance")

        t0 = time.perf_counter()
        requete_dict = pretraiteur.treat_request(query)
        results = engine.search(requete_dict)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        keywords: list[str] = requete_dict.get("key_words") or []

        print(f"\n  Analyse : {requete_dict}")

        display_results(results, keywords, engine, sort_by, requete_dict.get("type_doc", "articles"))
        print(f"  Temps de réponse : {elapsed_ms:.1f} ms\n")


if __name__ == "__main__":
    main()