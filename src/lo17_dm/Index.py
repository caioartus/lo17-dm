from collections import Counter
from pathlib import Path

from lxml import etree
import pandas as pd

from lo17_dm.Tokenizer import CorpusTokenizer


class Index:
    def __init__(self):
        self.xml_tree: etree._Element | None = None
        self.index_dict: dict = {}

    def load_xml(self, path: str | Path):
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError("Path provided does not exist")
        self.xml_tree = etree.ElementTree().parse(path)

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
            article_elem = document.find("article")
            titre_elem = document.find("titre")
            texte_elem = document.find("texte")
            if (
                titre_elem is None
                or texte_elem is None
                or article_elem is None
                or article_elem.text is None
            ):
                raise ValueError("Nones found, make sure corpus is correctly parsed.")

            doc_id = int(article_elem.text)

            if titre_elem.text is not None:
                self.titre_dict = self.treat_field(
                    titre_elem.text, doc_id, self.index_dict, "titre"
                )

            if texte_elem.text is not None:
                self.texte_dict = self.treat_field(
                    texte_elem.text, doc_id, self.index_dict, "texte"
                )

            self.save_to_tsv(self.titre_dict, output_dir / "index.tsv")

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
