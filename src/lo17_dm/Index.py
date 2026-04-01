from collections import Counter
from pathlib import Path

from lxml import etree
import pandas as pd

from lo17_dm.Tokenizer import CorpusTokenizer


class Index:
    def __init__(self):
        self.xml_tree: etree._Element | None = None
        self.index_dict: dict = {}

    def get_required(self, elem: etree._Element | None, name: str) -> str:
        """Retourne le texte d'un élément requis ou lève une ValueError."""
        if elem is None or elem.text is None:
            raise ValueError(f"Champ requis manquant : {name}")
        return elem.text

    def load_xml(self, path: str | Path):
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError("Path provided does not exist")
        self.xml_tree = etree.ElementTree().parse(path)

    def add_raw(self, text: str, document_id: int, index_dict: dict, section: str):
        """Ajoute le text de facon brute à l'index avec seulement un traitement minimal"""
        # TODO - Voir si on met vraiment en lowercase
        treated = text.lower()  # On met en lowercase quand même
        if treated not in index_dict:
            index_dict[treated] = {
                "freq": 1,
                "section": section,
                "docs": [document_id],
            }
        else:
            index_dict[treated]["freq"] += 1
            if document_id not in index_dict[treated]["docs"]:
                index_dict[treated]["docs"].append(document_id)

        return index_dict

    def treat_field(
        self, text: str, document_id: int, index_dict: dict, section: str
    ) -> dict:
        """Traite un champ de text, retourne le dictionnaire mis a jour"""
        token_counts = Counter(CorpusTokenizer.tokenize(text))
        for tok, count in token_counts.items():
            if tok not in index_dict:
                index_dict[tok] = {
                    "freq": count,
                    "section": section,
                    "docs": [document_id],
                }
            else:
                index_dict[tok]["freq"] += count
                if document_id not in index_dict[tok]["docs"]:
                    index_dict[tok]["docs"].append(document_id)
        return index_dict

    def build(self, output_dir: str | Path):
        """Construit l'index inversé pour le titre et le text"""
        assert self.xml_tree is not None, "Load XML before calling this function"

        output_dir = Path(output_dir)
        if not output_dir.exists():
            raise FileNotFoundError("Output directory doesn't exist.")

        for document in self.xml_tree.iter("document"):
            article_text = self.get_required(document.find("article"), "article")
            doc_id = int(article_text)
            print(doc_id)

            # Champs tokenises
            titre_text = self.get_required(document.find("titre"), "titre")
            texte_text = self.get_required(document.find("texte"), "texte")

            # Champs traites minimalement
            rubrique_text = self.get_required(document.find("rubrique"), "rubrique")
            bulletin_text = self.get_required(document.find("bulletin"), "bulletin")
            date_text = self.get_required(document.find("date"), "date")
            auteur_text = self.get_required(document.find("auteur"), "auteur")
            contact_text = self.get_required(document.find("contact"), "contact")

            # Dictionnaires pour les champs à traiter
            tokenized_fields = {
                "titre": titre_text,
                "texte": texte_text,
            }
            raw_fields = {
                "rubrique": rubrique_text,
                "bulletin": bulletin_text,
                "date": date_text,
                "auteur": auteur_text,
                "contact": contact_text,
            }

            # Traitement des champs tokenisés
            for section, text in tokenized_fields.items():
                self.index_dict = self.treat_field(
                    text, doc_id, self.index_dict, section
                )

            # Traitement des champs bruts
            for section, text in raw_fields.items():
                self.index_dict = self.add_raw(text, doc_id, self.index_dict, section)

    def save_to_tsv(self, index_dict: dict, path: str | Path):
        data = []
        for token, info in index_dict.items():
            data.append(
                {
                    "token": token,
                    "freq": info["freq"],
                    "section": info["section"],
                    "docs": ",".join(map(str, info["docs"])),
                }
            )
        df = pd.DataFrame(data)
        df.to_csv(path, sep="\t", index=False)
