#!/usr/bin/env python3
"""
Évaluation expérimentale du moteur de recherche ADIT.

Protocole :
  1. 10 requêtes de test avec vérité terrain (ground truth) définie manuellement.
  2. Calcul de Précision et Rappel pour chaque requête.
  3. Mesure du temps de réponse moyen sur 100 exécutions par requête.
  4. Affichage des résultats sous forme de tableau de synthèse.

Pour compléter la vérité terrain :
  - Exécutez d'abord le moteur (scripts/moteur.py) pour chaque requête.
  - Inspectez le corpus XML (outputs/clean_corpus.xml) manuellement.
  - Remplissez les ensembles GROUND_TRUTH[i]["relevant_ids"] avec les IDs corrects.
"""

import sys
import time
import statistics
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lo17_dm.Pretraiteur import Pretraiteur
from lo17_dm.SearchEngine import SearchEngine

OUTPUTS = Path(__file__).parent.parent / "outputs"
CORPUS = OUTPUTS / "clean_corpus.xml"
LEMMA_TABLE = OUTPUTS / "lemmes_corpus.csv"
RUBRIQUE_INDEX = OUTPUTS / "index_rubrique.tsv"
SUB_TABLE = OUTPUTS / "sub_table.tsv"

N_TIMING_RUNS = 100

# ------------------------------------------------------------------ #
# Vérité terrain — À COMPLÉTER MANUELLEMENT                           #
# Chaque entrée contient :                                             #
#   query        : la requête en langage naturel                       #
#   operator     : "AND" ou "OR" selon le sens de la requête          #
#   relevant_ids : ensemble des IDs de documents RÉELLEMENT pertinents #
#                  (à remplir après inspection manuelle du corpus)     #
# ------------------------------------------------------------------ #

GROUND_TRUTH: list[dict] = [
    {
        "id": 1,
        "query": "Je veux les articles de la rubrique Focus parlant d'innovation.",
        "operator": "AND",
        "relevant_ids": set(),  # TODO : remplir après inspection manuelle
    },
    {
        "id": 2,
        "query": (
            "Quels sont les articles parus entre le 3 mars 2013 et le 4 mai 2013 "
            "évoquant les Etats-Unis ?"
        ),
        "operator": "AND",
        "relevant_ids": set(),
    },
    {
        "id": 3,
        "query": "Afficher les articles de la rubrique en direct des laboratoires.",
        "operator": "AND",
        "relevant_ids": set(),
    },
    {
        "id": 4,
        "query": "Articles contenant une image.",
        "operator": "AND",
        "relevant_ids": set(),
    },
    {
        "id": 5,
        "query": "Quels sont les articles parlant de la Russie ou du Japon ?",
        "operator": "OR",
        "relevant_ids": set(),
    },
    {
        "id": 6,
        "query": "Je voudrais les articles de 2011 sur l'enseignement.",
        "operator": "AND",
        "relevant_ids": set(),
    },
    {
        "id": 7,
        "query": (
            "Je veux les articles de 2014 et de la rubrique Focus et "
            "parlant de la santé."
        ),
        "operator": "AND",
        "relevant_ids": set(),
    },
    {
        "id": 8,
        "query": "Lister tous les articles dont la rubrique est Focus et qui ont des images.",
        "operator": "AND",
        "relevant_ids": set(),
    },
    {
        "id": 9,
        "query": "Je veux les articles sans image.",
        "operator": "AND",
        "relevant_ids": set(),
    },
    {
        "id": 10,
        "query": "Quels sont les articles qui parlent des robots et des chirurgiens ?",
        "operator": "AND",
        "relevant_ids": set(),
    },
]


# ------------------------------------------------------------------ #
# Métriques                                                            #
# ------------------------------------------------------------------ #

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


# ------------------------------------------------------------------ #
# Évaluation                                                           #
# ------------------------------------------------------------------ #

def run_evaluation() -> None:
    print("=" * 78)
    print("  ÉVALUATION DU MOTEUR DE RECHERCHE ADIT")
    print("=" * 78)
    print("  Chargement…")

    pretraiteur = Pretraiteur(
        lemma_table_path=LEMMA_TABLE,
        rubriques_index_path=RUBRIQUE_INDEX,
    )
    engine = SearchEngine(output_dir=OUTPUTS, corpus_path=CORPUS)
    print(f"  {len(engine.documents)} documents chargés.\n")

    # ── Tableau Qualité ──────────────────────────────────────────────
    print(f"{'N°':<4} {'Requête':<52} {'P':>6} {'R':>6} {'F1':>6} {'Ret':>5} {'Rel':>5}")
    print("─" * 78)

    quality_rows: list[dict] = []

    for test in GROUND_TRUTH:
        requete_dict = pretraiteur.treat_request(test["query"], SUB_TABLE)
        results = engine.search(requete_dict, keyword_operator=test["operator"])
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
        print("─" * 78)
        print(
            f"{'Moyenne (GT renseignées)':<56} "
            f"{avg_p:>6.2f} {avg_r:>6.2f} {avg_f:>6.2f}"
        )
    print()

    # ── Tableau Performance ──────────────────────────────────────────
    print(f"  Mesure de performance ({N_TIMING_RUNS} exécutions par requête)\n")
    print(f"{'N°':<4} {'Requête':<46} {'Moy(ms)':>8} {'Min(ms)':>8} {'Max(ms)':>8} {'Éc-T':>6}")
    print("─" * 78)

    all_times: list[float] = []

    for test in GROUND_TRUTH:
        times: list[float] = []
        for _ in range(N_TIMING_RUNS):
            t0 = time.perf_counter()
            rd = pretraiteur.treat_request(test["query"], SUB_TABLE)
            engine.search(rd, keyword_operator=test["operator"])
            times.append((time.perf_counter() - t0) * 1000)

        all_times.extend(times)
        avg = statistics.mean(times)
        mn = min(times)
        mx = max(times)
        std = statistics.stdev(times)
        label = test["query"][:44] + ("…" if len(test["query"]) > 44 else "")
        print(f"{test['id']:<4} {label:<46} {avg:>8.1f} {mn:>8.1f} {mx:>8.1f} {std:>6.1f}")

    print("─" * 78)
    print(
        f"{'Moyenne globale':<50} "
        f"{statistics.mean(all_times):>8.1f} "
        f"{min(all_times):>8.1f} "
        f"{max(all_times):>8.1f}"
    )
    print()
    print("  Évaluation terminée.")
    print("=" * 78)


if __name__ == "__main__":
    run_evaluation()