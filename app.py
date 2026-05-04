import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory

sys.path.insert(0, str(Path(__file__).parent / "src"))
GROUND_TRUTH = [
    {"id": 1,  "query": "Je veux les articles de la rubrique Focus parlant d'innovation.", "operator": "AND"},
    {"id": 2,  "query": "Quels sont les articles parus entre le 3 mars 2013 et le 4 mai 2013 évoquant les Etats-Unis ?", "operator": "AND"},
    {"id": 3,  "query": "je veux voir les articles de la rubrique Focus et publiés entre 30/08/2011 et 29/09/2011.", "operator": "AND"},
    {"id": 4,  "query": "Quels sont les articles dont le titre contient le terme 'marché' et le mot 'projet' ?", "operator": "AND"},
    {"id": 5,  "query": "Quels sont les articles parlant de la Russie ou du Japon ?", "operator": "OR"},
    {"id": 6,  "query": "Rechercher tous les articles sur le CNRS et l'innovation à partir de 2013.", "operator": "AND"},
    {"id": 7,  "query": "Je veux les articles de 2014 et de la rubrique Focus et parlant de la santé.", "operator": "AND"},
    {"id": 8,  "query": "Lister tous les articles dont la rubrique est Focus et qui ont des images.", "operator": "AND"},
    {"id": 9,  "query": "Quels sont les articles dont le titre contient biocarburant ou le contenu parle des bioénergies ?", "operator": "AND"},
    {"id": 10, "query": "Je souhaites avoir tout les articles donc la rubrique est focus ou Actualités Innovations et qui contiennent les mots chercheurs et paris", "operator": "AND"},
]
from lo17_dm.Pretraiteur import Pretraiteur
from lo17_dm.SearchEngine import SearchEngine

app = Flask(__name__)

OUTPUTS = Path(__file__).parent / "outputs"
CORPUS = OUTPUTS / "corpus.xml"
LEMMA_TABLE = OUTPUTS / "lemmes_corpus.tsv"
RUBRIQUE_INDEX = OUTPUTS / "index" / "index_rubrique.tsv"
STOPWORD_PATH = OUTPUTS / "stop_words.tsv"
DATA_DIR = Path(__file__).parent / "data" / "BULLETINS"
DB_PATH = OUTPUTS / "annotations.db"



print("Chargement du moteur de recherche…")
pretraiteur = Pretraiteur(
    lemma_table_path=LEMMA_TABLE,
    rubriques_index_path=RUBRIQUE_INDEX,
    stop_words_path=STOPWORD_PATH,
)
engine = SearchEngine(output_dir=OUTPUTS, corpus_path=CORPUS)
print(f"{len(engine.documents)} documents chargés.")


def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    with _db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS annotations (
            query_id    INTEGER NOT NULL,
            doc_id      INTEGER NOT NULL,
            is_relevant INTEGER NOT NULL,
            PRIMARY KEY (query_id, doc_id)
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS queries (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            query    TEXT NOT NULL,
            operator TEXT NOT NULL DEFAULT 'AND'
        )""")
        if conn.execute("SELECT COUNT(*) FROM queries").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO queries (id, query, operator) VALUES (?,?,?)",
                [(q["id"], q["query"], q["operator"]) for q in GROUND_TRUTH],
            )


_init_db()

_DATE_KEY = lambda d: engine._parse_date(d["date"]) or datetime.min  # noqa: E731


# ── Pages ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", doc_count=len(engine.documents))


# ── Recherche ──────────────────────────────────────────────────────────────

@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    sort_by = request.args.get("sort", "relevance")

    if not query:
        return jsonify({"results": [], "query_dict": {}, "elapsed_ms": 0, "count": 0, "keywords": []})

    t0 = time.perf_counter()
    requete_dict = pretraiteur.treat_request(query)
    results = engine.search(requete_dict)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    keywords: list[str] = requete_dict.get("key_words") or []

    if sort_by == "date_asc":
        results = sorted(results, key=_DATE_KEY)
    elif sort_by == "date_desc":
        results = sorted(results, key=_DATE_KEY, reverse=True)

    output = []
    for doc in results:
        output.append({
            "id": doc["id"],
            "titre": doc["titre"],
            "rubrique": doc["rubrique"],
            "date": doc["date"],
            "bulletin": doc["bulletin"],
            "auteur": doc["auteur"],
            "score": doc["score"],
            "snippet": engine.get_snippet(doc["id"], keywords),
            "has_image": doc.get("has_image", False),
        })

    return jsonify({
        "results": output,
        "query_dict": requete_dict,
        "elapsed_ms": round(elapsed_ms, 1),
        "count": len(output),
        "keywords": keywords,
    })


# ── Catalogue (paginé) ─────────────────────────────────────────────────────

@app.route("/browse")
def browse():
    sort_by = request.args.get("sort", "date_asc")
    page = max(1, int(request.args.get("page", 1)))
    per_page = 30

    docs = sorted(engine.documents.values(), key=_DATE_KEY, reverse=(sort_by == "date_desc"))
    total = len(docs)
    start = (page - 1) * per_page
    output = [{
        "id": d["id"], "titre": d["titre"], "rubrique": d["rubrique"],
        "date": d["date"], "bulletin": d["bulletin"], "auteur": d["auteur"],
        "has_image": d.get("has_image", False),
    } for d in docs[start:start + per_page]]

    return jsonify({"docs": output, "total": total, "page": page,
                    "pages": (total + per_page - 1) // per_page, "per_page": per_page})


# ── Annotation — données ───────────────────────────────────────────────────

@app.route("/api/queries")
def api_queries():
    with _db() as conn:
        rows = conn.execute("SELECT id, query, operator FROM queries ORDER BY id").fetchall()
    return jsonify([{"id": r["id"], "query": r["query"], "operator": r["operator"]} for r in rows])


@app.route("/api/queries", methods=["PUT"])
def api_save_queries():
    data = request.get_json()  # [{id: int|null, query: str, operator: str}]
    with _db() as conn:
        existing_ids = {r[0] for r in conn.execute("SELECT id FROM queries").fetchall()}
        new_ids = {q["id"] for q in data if q.get("id") is not None}
        for old_id in existing_ids - new_ids:
            conn.execute("DELETE FROM annotations WHERE query_id=?", (old_id,))
            conn.execute("DELETE FROM queries WHERE id=?", (old_id,))
        for q in data:
            text = q["query"].strip()
            if not text:
                continue
            op = q.get("operator", "AND")
            if q.get("id") is not None and q["id"] in existing_ids:
                conn.execute("UPDATE queries SET query=?, operator=? WHERE id=?", (text, op, q["id"]))
            else:
                conn.execute("INSERT INTO queries (query, operator) VALUES (?,?)", (text, op))
    return jsonify({"ok": True})


@app.route("/api/queries/reset", methods=["POST"])
def api_reset_queries():
    with _db() as conn:
        conn.execute("DELETE FROM annotations")
        conn.execute("DELETE FROM queries")
        conn.execute("DELETE FROM sqlite_sequence WHERE name='queries'")
        conn.executemany(
            "INSERT INTO queries (id, query, operator) VALUES (?,?,?)",
            [(q["id"], q["query"], q["operator"]) for q in GROUND_TRUTH],
        )
    return jsonify({"ok": True})


@app.route("/api/docs")
def api_docs():
    sort_by = request.args.get("sort", "date_asc")
    docs = sorted(engine.documents.values(), key=_DATE_KEY, reverse=(sort_by == "date_desc"))
    return jsonify([{
        "id": d["id"], "titre": d["titre"], "rubrique": d["rubrique"],
        "date": d["date"], "has_image": d.get("has_image", False),
    } for d in docs])


@app.route("/api/annotations", methods=["GET"])
def api_get_annotations():
    with _db() as conn:
        rows = conn.execute("SELECT query_id, doc_id, is_relevant FROM annotations").fetchall()
    result: dict[str, dict[str, int]] = {}
    for row in rows:
        result.setdefault(str(row["query_id"]), {})[str(row["doc_id"])] = row["is_relevant"]
    return jsonify(result)


@app.route("/api/annotations", methods=["POST"])
def api_save_annotation():
    data = request.get_json()
    qid, did, rel = int(data["query_id"]), int(data["doc_id"]), data["is_relevant"]
    with _db() as conn:
        if rel is None:
            conn.execute("DELETE FROM annotations WHERE query_id=? AND doc_id=?", (qid, did))
        else:
            conn.execute(
                "INSERT OR REPLACE INTO annotations (query_id, doc_id, is_relevant) VALUES (?,?,?)",
                (qid, did, int(rel)),
            )
    return jsonify({"ok": True})


@app.route("/api/export")
def api_export():
    with _db() as conn:
        rows = conn.execute(
            "SELECT query_id, doc_id FROM annotations WHERE is_relevant=1 ORDER BY query_id, doc_id"
        ).fetchall()
    relevant: dict[int, list[int]] = {}
    for row in rows:
        relevant.setdefault(row["query_id"], []).append(row["doc_id"])

    lines = ["GROUND_TRUTH: list[dict] = ["]
    for q in GROUND_TRUTH:
        ids = relevant.get(q["id"], [])
        ids_str = "{" + ", ".join(str(i) for i in ids) + "}" if ids else "set()"
        lines += [
            "    {",
            f'        "id": {q["id"]},',
            f'        "query": {repr(q["query"])},',
            f'        "operator": {repr(q["operator"])},',
            f'        "relevant_ids": {ids_str},',
            "    },",
        ]
    lines.append("]")
    return "\n".join(lines), 200, {"Content-Type": "text/plain; charset=utf-8"}


# ── Documents bruts ────────────────────────────────────────────────────────

@app.route("/document/<int:doc_id>")
def document(doc_id):
    return send_from_directory(DATA_DIR, f"{doc_id}.htm")


if __name__ == "__main__":
    app.run(debug=False, port=5000)
