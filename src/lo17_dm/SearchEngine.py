from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
from lxml import etree


class SearchEngine:
    """Charge les index inversés et le corpus, puis exécute des requêtes booléennes classées."""

    def __init__(
        self,
        output_dir: str | Path,
        corpus_path: str | Path,
        poids_score: dict[str, float] = {"titre": 0.6, "texte": 0.4},
    ):
        self.output_dir: Path = Path(output_dir)
        self.indexes: dict[str, dict[str, set[int]]] = {}
        self.documents: dict[int, dict] = {}
        self.poids_score: dict[str, float] = poids_score
        self._load_indexes()
        self._load_corpus(Path(corpus_path))

    def _load_indexes(self) -> None:
        for name in (
            "titre",
            "texte",
            "rubrique",
            "bulletin",
            "date",
            "auteur",
            "contact",
            "image",
        ):
            path = self.output_dir / "index" / f"index_{name}.tsv"
            if not path.exists():
                continue
            df = pd.read_csv(path, sep="\t", dtype=str)
            idx: dict[str, set[int]] = {}
            for _, row in df.iterrows():
                token = str(row["token"]).strip().lower()
                docs = {int(d) for d in str(row["docs"]).split(",") if d.strip()}
                idx[token] = docs
            self.indexes[name] = idx

    def _load_corpus(self, corpus_path: Path) -> None:
        tree = etree.ElementTree().parse(corpus_path)
        for doc in tree.iter("document"):
            article_elem = doc.find("article")
            if article_elem is None or article_elem.text is None:
                continue
            doc_id = int(article_elem.text)

            def _text(tag: str, _doc=doc) -> str:
                e = _doc.find(tag)
                return (e.text or "") if e is not None else ""

            images_elem = doc.find("images")
            has_image = images_elem is not None and len(list(images_elem)) > 0

            self.documents[doc_id] = {
                "id": doc_id,
                "titre": _text("titre"),
                "rubrique": _text("rubrique"),
                "date": _text("date"),
                "texte": _text("texte"),
                "auteur": _text("auteur"),
                "bulletin": _text("bulletin"),
                "has_image": has_image,
            }

    @staticmethod
    def _parse_date(date_str: str) -> datetime | None:
        """Parse une date au format j/mm/aaaa ou jj/mm/aaaa."""
        if not date_str:
            return None
        try:
            parts = date_str.strip().split("/")
            if len(parts) == 3:
                return datetime(int(parts[2]), int(parts[1]), int(parts[0]))
        except (ValueError, IndexError):
            pass
        return None

    def _all_doc_ids(self) -> set[int]:
        return set(self.documents)

    @staticmethod
    def _intersect(a: set[int] | None, b: set[int]) -> set[int]:
        return b if a is None else a & b

    @staticmethod
    def _union(a: set[int] | None, b: set[int]) -> set[int]:
        return b if a is None else a | b

    def _group_by(self, results: list[dict], field: str) -> list[dict]:
        """Regroupe les articles par valeur de `field` (par article, par rubrique, par bulletin)"""
        groups: dict[str, list[dict]] = {}
        for doc in results:
            key = doc.get(field) or "-"
            groups.setdefault(key, []).append(doc)

        grouped = []
        for key, articles in groups.items():
            articles.sort(key=lambda d: d["score"], reverse=True)
            grouped.append(
                {
                    field: key,
                    "articles": articles,
                    "score": max(a["score"] for a in articles),
                }
            )

        grouped.sort(key=lambda g: g["score"], reverse=True)
        return grouped

    # -------------------------- Recherche dans les index --------------------------

    def _matches_anti_date(self, doc_date: datetime, anti_date: str) -> bool:
        """Vérifie si doc_date correspond au motif anti_date (ex: '*/06/*' pour juin)."""
        parts = anti_date.split("/")
        if len(parts) != 3:
            return False
        day_s, month_s, year_s = parts
        try:
            if day_s != "*" and int(day_s) != doc_date.day:
                return False
            if month_s != "*" and int(month_s) != doc_date.month:
                return False
            if year_s != "*" and int(year_s) != doc_date.year:
                return False
        except ValueError:
            return False
        return True

    def _lookup_image(self, has_image: bool) -> set[int]:
        docs_with_image = self.indexes.get("image", {}).get("image", set())
        return docs_with_image if has_image else self._all_doc_ids() - docs_with_image

    def _get_okay_dates(
        self, start: datetime | None, end: datetime | None, anti: str | None
    ) -> set[int]:
        good_docs = set()
        """Finds documents with acceptable dates among those available in the index"""
        date_idx = self.indexes.get("date", {})
        for datestr, docs in date_idx.items():
            date = self._parse_date(datestr)
            if date is None:
                continue
            # si dans les bornes (ou borne pas defini) et si pas antidate
            if (
                (start is None or date >= start)
                and (end is None or date <= end)
                and (anti is None or not self._matches_anti_date(date, anti))
            ):
                good_docs.update(docs)
        return good_docs

    def _score(self, doc_id: int, keywords: list[str]) -> float:
        """Score booléen classé : +3 par mot-clé dans le titre, +1 dans le texte."""
        score = 0.0
        if sum(self.poids_score.values()) != 1:
            raise ValueError("La somme des poids doit être égale à 1")

        if len(keywords) == 0:  # pas de mots cles, tout les doc sont pertinents
            return 1

        for champ in self.poids_score.keys():
            for kw in keywords:
                if doc_id in self.indexes[champ].get(kw, {}):
                    score += self.poids_score[champ]
        score = score / len(keywords)
        return score

    def search(self, requete_dict: dict) -> list[dict]:
        type_doc = requete_dict.get("type_doc", "articles")

        # Rubrique, toujours OU
        rubriques = requete_dict.get("rubrique")
        has_rubrique = set()
        if rubriques:
            for rubrique in rubriques:
                has_rubrique |= self.indexes.get("rubrique", {}).get(rubrique, set())

        # Filtre date
        from_date = self._parse_date(requete_dict.get("from_date"))
        to_date = self._parse_date(requete_dict.get("to_date"))
        anti_date = requete_dict.get("anti_date")

        date_ok = self._get_okay_dates(from_date, to_date, anti_date)
        has_date_filter = bool(from_date or to_date or anti_date)

        # Filtre image
        image_val = requete_dict.get("image")
        has_image_docs = (
            self._lookup_image(image_val) if image_val is not None else set()
        )

        # Mots-clés titre (DNF : (a ET b) OU (c ET d))
        titre_docs = set()
        titre_groups = requete_dict.get("titre", [])
        for and_group in titre_groups:
            and_docs_list = [
                self.indexes.get("titre", {}).get(word, set()) for word in and_group
            ]
            if and_docs_list:
                titre_docs |= set.intersection(*and_docs_list)

        # Mots-clés contenu (DNF : (a ET b) OU (c ET d))
        keywords_docs = set()
        contenu_groups = requete_dict.get("contenu", [])
        for and_group in contenu_groups:
            and_docs_list = [
                self.indexes.get("texte", {}).get(word, set()) for word in and_group
            ]
            if and_docs_list:
                keywords_docs |= set.intersection(*and_docs_list)

        # Exclusion (toujours ET NOT)
        exclude_docs = set()
        for word in requete_dict.get("exclude", []):
            exclude_docs |= self.indexes.get("texte", {}).get(word, set())
            exclude_docs |= self.indexes.get("titre", {}).get(word, set())

        # --- INTERSECTION FINALE ---
        active_filters = []
        if rubriques:
            active_filters.append(has_rubrique)
        if has_date_filter:
            active_filters.append(date_ok)
        if image_val is not None:
            active_filters.append(has_image_docs)
        if titre_groups:
            active_filters.append(titre_docs)
        if contenu_groups:
            active_filters.append(keywords_docs)

        if active_filters:
            active_filters.sort(key=len)
            candidate_docs = active_filters[0].copy()
            for f in active_filters[1:]:
                candidate_docs &= f
        else:
            candidate_docs = self._all_doc_ids()

        candidate_docs -= exclude_docs

        # --- SCORE ET RÉSULTATS ---
        all_keywords = []
        for gp in titre_groups + contenu_groups:
            all_keywords.extend(gp)

        results: list[dict] = []
        for doc_id in candidate_docs:
            if doc_id not in self.documents:
                continue
            doc = dict(self.documents[doc_id])
            doc["score"] = self._score(doc_id, all_keywords)
            results.append(doc)

        results.sort(key=lambda d: d["score"], reverse=True)

        if type_doc == "bulletins":
            return self._group_by(results, "bulletin")
        elif type_doc == "rubrique":
            return self._group_by(results, "rubrique")
        return results
