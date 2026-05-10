import sqlite3
import sys
import time
import statistics
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lo17_dm.Pretraiteur import Pretraiteur
from lo17_dm.SearchEngine import SearchEngine

OUTPUTS = Path(__file__).parent.parent / "outputs"
OUTPUTS_INDEX = OUTPUTS / "index"
CORPUS = OUTPUTS / "clean_corpus.xml"
LEMMA_TABLE = OUTPUTS / "lemmes_corpus.tsv"
RUBRIQUE_INDEX = OUTPUTS_INDEX / "index_rubrique.tsv"
STOP_WORDS = OUTPUTS / "stop_words.txt"
SUB_TABLE = OUTPUTS / "sub_table.tsv"
ANNOTATIONS_DB = OUTPUTS / "annotations.db"

N_TIMING_RUNS = 100


def load_manually_annotated() -> list[dict]:
    with sqlite3.connect(ANNOTATIONS_DB) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, query FROM queries ORDER BY id")
        queries = cur.fetchall()
        manually_annotated = []
        for qid, query in queries:
            cur.execute(
                "SELECT doc_id FROM annotations WHERE query_id = ? AND is_relevant = 1",
                (qid,),
            )
            relevant_ids = {row[0] for row in cur.fetchall()}
            manually_annotated.append(
                {"id": qid, "query": query.strip(), "relevant_ids": relevant_ids}
            )
    return manually_annotated


def precision(retrieved: set[int], relevant: set[int]) -> float:
    if not retrieved:
        return 0.0
    return len(retrieved & relevant) / len(retrieved)


def recall(retrieved: set[int], relevant: set[int]) -> float:
    if not relevant:
        return 0.0
    return len(retrieved & relevant) / len(relevant)


def f1(p: float, r: float) -> float:
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)


def run_evaluation() -> None:
    print("=" * 90)
    print("\t\tEVALUATION DU MOTEUR DE RECHERCHE ADIT")
    print("=" * 90)
    print("  Chargement...", end=" ")

    manually_annotated = load_manually_annotated()

    pretraiteur = Pretraiteur(
        lemma_table_path=LEMMA_TABLE,
        rubriques_index_path=RUBRIQUE_INDEX,
        stop_words_path=STOP_WORDS,
    )
    engine = SearchEngine(output_dir=OUTPUTS, corpus_path=CORPUS)
    print(f"  {len(engine.documents)} documents chargés.\n")

    print(f"  Mesure de qualité (précision, rappel et f1-score)")
    print("-" * 90)
    print(
        f"{'N°':<4} {'Requête':<52} {'P':>6} {'R':>6} {'F1':>6} {'Ret':>5} {'Rel':>5}"
    )
    print("-" * 90)

    quality_rows: list[dict] = []

    for test in manually_annotated:
        requete_dict = pretraiteur.treat_request(test["query"])
        results = engine.search(requete_dict)
        retrieved_ids = {doc["id"] for doc in results}
        relevant_ids: set[int] = test["relevant_ids"]

        p = precision(retrieved_ids, relevant_ids)
        r = recall(retrieved_ids, relevant_ids)
        f = f1(p, r)

        label = test["query"][:50] + ("…" if len(test["query"]) > 50 else "")
        gt_note = "" if relevant_ids else " [GT manquante]"
        print(
            f"{test['id']:<4} {label:<52} "
            f"{p:>6.2f} {r:>6.2f} {f:>6.2f} "
            f"{len(retrieved_ids):>5} {len(relevant_ids):>5}{gt_note}"
        )
        quality_rows.append(
            {
                "id": test["id"],
                "precision": p,
                "recall": r,
                "f1": f,
                "retrieved": len(retrieved_ids),
                "relevant": len(relevant_ids),
            }
        )

    filled = [r for r in quality_rows if r["relevant"] > 0]
    if filled:
        avg_p = sum(r["precision"] for r in filled) / len(filled)
        avg_r = sum(r["recall"] for r in filled) / len(filled)
        avg_f = sum(r["f1"] for r in filled) / len(filled)
        print("-" * 90)
        print(
            f"{'Moyenne (GT renseignées)':<56} "
            f"{avg_p:>6.2f} {avg_r:>6.2f} {avg_f:>6.2f}"
        )
    print("-" * 90)
    print()

    print(f"  Mesure de performance ({N_TIMING_RUNS} exécutions par requête)")
    print("-" * 90)
    print(
        f"{'N°':<4} {'Requête':<46} {'Moy(ms)':>8} {'Min(ms)':>8} {'Max(ms)':>8} {'Éc-T':>6}"
    )
    print("-" * 90)

    all_times: list[float] = []

    for test in manually_annotated:
        times: list[float] = []
        for _ in range(N_TIMING_RUNS):
            t0 = time.perf_counter()
            rd = pretraiteur.treat_request(test["query"])
            # rd = pretraiteur.treat_request(test["query"], SUB_TABLE)
            engine.search(rd)
            times.append((time.perf_counter() - t0) * 1000)

        all_times.extend(times)
        avg = statistics.mean(times)
        mn = min(times)
        mx = max(times)
        std = statistics.stdev(times)
        label = test["query"][:44] + ("…" if len(test["query"]) > 44 else "")
        print(
            f"{test['id']:<4} {label:<46} {avg:>8.1f} {mn:>8.1f} {mx:>8.1f} {std:>6.1f}"
        )

    print("-" * 90)
    print(
        f"{'Moyenne globale':<50} "
        f"{statistics.mean(all_times):>8.1f} "
        f"{min(all_times):>8.1f} "
        f"{max(all_times):>8.1f}"
    )
    print("=" * 90)


if __name__ == "__main__":
    run_evaluation()
