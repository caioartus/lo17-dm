import argparse
import time
from pathlib import Path

from lo17_dm.Interface import display_ecran_titre, display_chargement_effectue
from lo17_dm.Interface import ask_requete, ask_tri, SORT_LABELS
from lo17_dm.Interface import display_requete_dict, display_results, display_tps_rep
from lo17_dm.Pretraiteur import Pretraiteur
from lo17_dm.SearchEngine import SearchEngine

OUTPUTS = Path(__file__).parent.parent / "outputs"
CORPUS_NAME = "corpus"
LEMMA_NAME = "lemmes_corpus"


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

    display_ecran_titre()

    pretraiteur = Pretraiteur(
        lemma_table_path=lemma_table_path,
        rubriques_index_path=rubrique_index_path,
        stop_words_path=stop_words_path,
    )
    engine = SearchEngine(output_dir=outdir, corpus_path=corpus_path)

    display_chargement_effectue(len(engine.documents))

    while True:
        query = ask_requete()

        if not query or query.lower() in ("quitter", "q", "exit", "quit"):
            print("\nAu revoir.")
            break

        sort_by = SORT_LABELS[str(ask_tri())]

        t0 = time.perf_counter()
        requete_dict = pretraiteur.treat_request(query)
        results = engine.search(requete_dict)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        keywords: list[str] = requete_dict.get("key_words") or []

        display_requete_dict(requete_dict)

        display_results(
            results, keywords, engine, sort_by, requete_dict.get("type_doc", "articles")
        )
        
        display_tps_rep(elapsed_ms)


if __name__ == "__main__":
    main()