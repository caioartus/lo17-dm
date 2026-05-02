from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
from lxml import etree


class SearchEngine:
    """Charge les index inversés et le corpus, puis exécute des requêtes booléennes classées."""

    def __init__(self, output_dir: str | Path, corpus_path: str | Path):
        self.output_dir: Path = Path(output_dir)
        self.indexes: dict[str, dict[str, set[int]]] = {}
        self.documents: dict[int, dict] = {}
        self._load_indexes()
        self._load_corpus(Path(corpus_path))

    # ------------------------------------------------------------------ #
    # Chargement                                                           #
    # ------------------------------------------------------------------ #

    def _load_indexes(self) -> None:
        for name in ("titre", "texte", "rubrique", "bulletin", "date", "auteur", "contact", "image"):
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

    # ------------------------------------------------------------------ #
    # Utilitaires internes                                                  #
    # ------------------------------------------------------------------ #

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

    # ------------------------------------------------------------------ #
    # Recherche dans les index                                              #
    # ------------------------------------------------------------------ #

    def _lookup_keyword(
        self,
        keyword: str,
        fields: tuple[str, ...] = ("texte", "titre"),
    ) -> set[int]:
        result: set[int] = set()
        kw = keyword.lower().strip()
        for field in fields:
            result |= self.indexes.get(field, {}).get(kw, set())
        return result

    def _lookup_rubrique(self, rubrique: str) -> set[int]:
        idx = self.indexes.get("rubrique", {})
        key = rubrique.lower().strip()
        if key in idx:
            return idx[key]
        # Correspondance partielle (sous-chaîne)
        result: set[int] = set()
        for token, docs in idx.items():
            if key in token or token in key:
                result |= docs
        return result

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

    def _filter_by_date(
        self,
        from_date: str | None,
        to_date: str | None,
        anti_date: str | None,
    ) -> set[int]:
        fd = self._parse_date(from_date) if from_date else None
        td = self._parse_date(to_date) if to_date else None
        result: set[int] = set()
        for doc_id, doc in self.documents.items():
            dt = self._parse_date(doc["date"])
            if dt is None:
                continue
            if fd and dt < fd:
                continue
            if td and dt > td:
                continue
            if anti_date and self._matches_anti_date(dt, anti_date):
                continue
            result.add(doc_id)
        return result

    def _lookup_image(self, has_image: bool) -> set[int]:
        docs_with_image = self.indexes.get("image", {}).get("image", set())
        return docs_with_image if has_image else self._all_doc_ids() - docs_with_image

    # ------------------------------------------------------------------ #
    # Score de pertinence                                                   #
    # ------------------------------------------------------------------ #

    def _score(self, doc_id: int, keywords: list[str]) -> float:
        """Score booléen classé : +3 par mot-clé dans le titre, +1 dans le texte."""
        score = 0.0
        for kw in keywords:
            kw_lower = kw.lower()
            if doc_id in self.indexes.get("titre", {}).get(kw_lower, set()):
                score += 3.0
            if doc_id in self.indexes.get("texte", {}).get(kw_lower, set()):
                score += 1.0
        return score

    # ------------------------------------------------------------------ #
    # API publique                                                          #
    # ------------------------------------------------------------------ #

    def search(self, requete_dict: dict, keyword_operator: str = "AND") -> list[dict]:
        """
        Exécute la recherche booléenne classée.

        keyword_operator : "AND" → tous les mots-clés doivent être présents,
                           "OR"  → au moins un mot-clé doit être présent.

        Retourne une liste de dicts document triée par score décroissant.
        """
        candidate_docs: set[int] | None = None

        # Filtre rubrique (toujours AND avec le reste)
        rubrique = requete_dict.get("rubriques")
        if rubrique:
            candidate_docs = self._intersect(candidate_docs, self._lookup_rubrique(rubrique))

        # Filtre date
        from_date = requete_dict.get("from_date")
        to_date = requete_dict.get("to_date")
        anti_date = requete_dict.get("anti_date")
        if from_date or to_date or anti_date:
            candidate_docs = self._intersect(
                candidate_docs, self._filter_by_date(from_date, to_date, anti_date)
            )

        # Filtre image
        has_image = requete_dict.get("image")
        if has_image is not None:
            candidate_docs = self._intersect(candidate_docs, self._lookup_image(has_image))

        # Mots-clés
        keywords: list[str] = requete_dict.get("key_words") or []
        if keywords:
            if keyword_operator.upper() == "OR":
                kw_union: set[int] = set()
                for kw in keywords:
                    kw_union |= self._lookup_keyword(kw)
                candidate_docs = self._intersect(candidate_docs, kw_union)
            else:  # AND
                for kw in keywords:
                    candidate_docs = self._intersect(candidate_docs, self._lookup_keyword(kw))

        if candidate_docs is None:
            return []

        results: list[dict] = []
        for doc_id in candidate_docs:
            if doc_id not in self.documents:
                continue
            doc = dict(self.documents[doc_id])
            doc["score"] = self._score(doc_id, keywords)
            results.append(doc)

        results.sort(key=lambda d: d["score"], reverse=True)
        return results

    def get_snippet(self, doc_id: int, keywords: list[str], context_len: int = 200) -> str:
        """Extrait un extrait contextuel autour du premier mot-clé trouvé dans le texte."""
        doc = self.documents.get(doc_id)
        if not doc:
            return ""
        text: str = doc["texte"]
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