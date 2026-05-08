from datetime import datetime

from lo17_dm.SearchEngine import SearchEngine

SEP = "-" * 78

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


def _display_article(doc: dict, keywords: list[str], engine: SearchEngine, idx: int, indent: str = "  ") -> None:
    print(
        f"{indent}[{idx:3d}]  ID: {doc['id']}   "
        f"Date: {doc['date']}   "
        f"Bulletin: {doc['bulletin']}   "
        f"Score: {doc['score']:.0f}"
    )
    print(f"{indent}       Rubrique : {doc['rubrique']}")
    print(f"{indent}       Titre    : {doc['titre']}")
    snippet = engine.get_snippet(doc["id"], keywords)
    if snippet:
        lines = _wrap(snippet)
        print(f"{indent}       Extrait  : {lines[0]}")
        for line in lines[1:]:
            print(f"{indent}                  {line}")


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
                _display_article(doc, keywords, engine, i, indent="     ")
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
            _display_article(doc, keywords, engine, i)
            print(SEP)
