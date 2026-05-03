import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lo17_dm.Pretraiteur import Pretraiteur
from lo17_dm.SearchEngine import SearchEngine

OUTPUTS = Path(__file__).parent.parent / "outputs"
CORPUS = OUTPUTS / "clean_corpus.xml"
LEMMA_TABLE = OUTPUTS / "lemmes_corpus.tsv"
RUBRIQUE_INDEX = OUTPUTS / "index" / "index_rubrique.tsv"
SUB_TABLE = OUTPUTS / "sub_table.tsv"
STOPWORD_PATH = OUTPUTS / "stop_words.tsv"

SEP = "─" * 78

SORT_LABELS = {
    "1": "relevance",
    "2": "date_asc",
    "3": "date_desc",
}


# ------------------------------------------------------------------ #
# Affichage                                                            #
# ------------------------------------------------------------------ #

def _wrap(text: str, width: int = 70) -> list[str]:
    lines: list[str] = []
    while len(text) > width:
        cut = text.rfind(" ", 0, width)
        if cut == -1:
            cut = width
        lines.append(text[:cut])
        text = text[cut:].lstrip()
    if text:
        lines.append(text)
    return lines or [""]


def display_results(
    results: list[dict],
    keywords: list[str],
    engine: SearchEngine,
    sort_by: str = "relevance",
) -> None:
    if not results:
        print("\n  Aucun document trouvé.\n")
        return

    if sort_by == "date_asc":
        results = sorted(
            results,
            key=lambda d: engine._parse_date(d["date"]) or d["date"],
        )
    elif sort_by == "date_desc":
        results = sorted(
            results,
            key=lambda d: engine._parse_date(d["date"]) or d["date"],
            reverse=True,
        )

    print(f"\n  {len(results)} document(s) trouvé(s)\n")
    print(SEP)

    for i, doc in enumerate(results, 1):
        print(
            f"  [{i:3d}]  ID: {doc['id']}   "
            f"Date: {doc['date']}   "
            f"Bulletin: {doc['bulletin']}   "
            f"Score: {doc['score']:.0f}"
        )
        print(f"         Rubrique : {doc['rubrique']}")
        print(f"         Titre    : {doc['titre']}")
        snippet = engine.get_snippet(doc["id"], keywords)
        if snippet:
            lines = _wrap(snippet)
            print(f"         Extrait  : {lines[0]}")
            for line in lines[1:]:
                print(f"                    {line}")
        print(SEP)


# ------------------------------------------------------------------ #
# Boucle principale                                                    #
# ------------------------------------------------------------------ #

def main() -> None:
    print(SEP)
    print("  Moteur de recherche ADIT  —  chargement en cours…")
    print(SEP)

    pretraiteur = Pretraiteur(
        lemma_table_path=LEMMA_TABLE,
        rubriques_index_path=RUBRIQUE_INDEX,
        stop_words_path=STOPWORD_PATH,
    )
    engine = SearchEngine(output_dir=OUTPUTS, corpus_path=CORPUS)

    print(f"  {len(engine.documents)} documents chargés.")
    print("  Tapez 'quitter' pour quitter.\n")

    while True:
        print(
            "  Tri : [1] Pertinence (défaut)  "
            "[2] Date croissante  [3] Date décroissante"
        )
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

        # Détection de l'opérateur : "ou" → OR, sinon AND
        operator = "OR" if " ou " in query.lower() else "AND"

        t0 = time.perf_counter()
        requete_dict = pretraiteur.treat_request(query)
        results = engine.search(requete_dict, keyword_operator=operator)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        keywords: list[str] = requete_dict.get("key_words") or []

        print(f"\n  Analyse : {requete_dict}")
        print(f"  Opérateur mots-clés : {operator}")

        display_results(results, keywords, engine, sort_by)
        print(f"  Temps de réponse : {elapsed_ms:.1f} ms\n")


if __name__ == "__main__":
    main()