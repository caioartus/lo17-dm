from datetime import datetime

from lo17_dm.SearchEngine import SearchEngine

SEP = "-" * 78


def _get_snippet(text: str, keywords: list[str], context_len: int = 200) -> str:
    """Extrait un extrait contextuel autour du premier mot-clé trouvé dans le texte."""
    if not text:
        return ""
    if not keywords:
        return text[:context_len] + ("..." if len(text) > context_len else "")

    text_lower = text.lower()
    best_pos = len(text)
    for kw in keywords:
        pos = text_lower.find(kw.lower())
        if 0 <= pos < best_pos:
            best_pos = pos

    if best_pos == len(text):
        return text[:context_len] + ("..." if len(text) > context_len else "")

    start = max(0, best_pos - 60)
    end = min(len(text), best_pos + context_len)
    snippet = text[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet += "..."
    return snippet


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


def _display_article(doc: dict, keywords: list[str], idx: int, indent: str = "  ") -> None:
    print(
        f"{indent}[{idx:3d}]  ID: {doc['id']}   "
        f"Date: {doc['date']}   "
        f"Bulletin: {doc['bulletin']}   "
        f"Score: {doc['score']:.0f}"
    )
    print(f"{indent}       Rubrique : {doc['rubrique']}")
    print(f"{indent}       Titre    : {doc['titre']}")
    snippet = _get_snippet(doc["texte"], keywords)
    if snippet:
        lines = _wrap(snippet)
        print(f"{indent}       Extrait  : {lines[0]}")
        for line in lines[1:]:
            print(f"{indent}                  {line}")

def display_ecran_titre():
    print(SEP)
    print("  Moteur de recherche ADIT  -  chargement en cours…")
    print(SEP)

def display_chargement_effectue(n : int):
    print(f"  {n} documents chargés.")
    print("  Tapez 'quitter' pour quitter.\n")
    
SORT_LABELS = {
    "1": "relevance",
    "2": "date_asc",
    "3": "date_desc",
}

def ask_requete() -> str:
    """Demande une requête à l'utilisateur. Retourne une chaîne vide si EOF/interruption."""
    print("  Tri : [1] Pertinence (défaut)  [2] Date croissante  [3] Date décroissante")
    try:
        return input("  Requête : ").strip()
    except (EOFError, KeyboardInterrupt):
        return ""


def ask_tri() -> int:
    """Demande le tri souhaité. Retourne 1 (pertinence) par défaut."""
    try:
        choice = input("  Tri [1/2/3] : ").strip()
    except (EOFError, KeyboardInterrupt):
        return 1
    return int(choice) if choice in SORT_LABELS else 1


def display_results(
    results: list[dict],
    keywords: list[str],
    engine: SearchEngine,
    sort_by: str = "relevance",
    type_doc: str = "articles",
) -> None:
    if not results:
        print("\n  Aucun document trouvé.\n")
        return

    is_grouped = type_doc in ("bulletins", "rubrique")
    field = "bulletin" if type_doc == "bulletins" else "rubrique"

    _EPOCH = datetime(1900, 1, 1)

    def _group_date_min(g: dict) -> datetime:
        dates = [engine._parse_date(a["date"]) for a in g["articles"]]
        valid = [d for d in dates if d is not None]
        return min(valid) if valid else _EPOCH

    def _group_date_max(g: dict) -> datetime:
        dates = [engine._parse_date(a["date"]) for a in g["articles"]]
        valid = [d for d in dates if d is not None]
        return max(valid) if valid else _EPOCH

    if is_grouped:
        if sort_by == "date_asc":
            results = sorted(results, key=_group_date_min)
        elif sort_by == "date_desc":
            results = sorted(results, key=_group_date_max, reverse=True)

        label = "bulletin(s)" if type_doc == "bulletins" else "rubrique(s)"
        print(f"\n  {len(results)} {label} trouvé(s)\n")

        for group in results:
            print(SEP)
            group_name = group.get(field) or "—"
            header = f"Bulletin {group_name}" if type_doc == "bulletins" else f"Rubrique : {group_name}"
            articles = group.get("articles", [])
            print(f"  ▶  {header}  ({len(articles)} article{'s' if len(articles) > 1 else ''})")
            print()
            for i, doc in enumerate(articles, 1):
                _display_article(doc, keywords, i, indent="     ")
                if i < len(articles):
                    print()
        print(SEP)
    else:
        results_flat = sorted(results, key=lambda d: engine._parse_date(d["date"]) or d["date"]) if sort_by == "date_asc" \
            else sorted(results, key=lambda d: engine._parse_date(d["date"]) or d["date"], reverse=True) if sort_by == "date_desc" \
            else results

        print(f"\n  {len(results_flat)} document(s) trouvé(s)\n")
        print(SEP)
        for i, doc in enumerate(results_flat, 1):
            _display_article(doc, keywords, i)
            print(SEP)

def display_requete_dict(rdict: dict):
    print(f"\n  Analyse : {rdict}")
    
def display_tps_rep(tps: float):
    print(f"  Temps de réponse : {tps:.1f} ms\n")