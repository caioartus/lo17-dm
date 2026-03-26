from lxml import etree
from pathlib import Path
from lo17_dm.Tokenizer import CorpusTokenizer
import pandas as pd


class Index:
    def __init__(self):
        self.xml_tree: etree._Element | None = None
        self.index_dict: dict = {}

    def load_xml(self, path: str | Path):
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError("Path provided does not exist")
        self.xml_tree = etree.ElementTree().parse(path)

    def treat_field(self, text: str, document_id: int) -> None:
        """Traite un champ de text en mettant a jour le dict interne"""

        tokenlist = CorpusTokenizer.tokenize(text)
        for tok in tokenlist:
            if tok not in self.index_dict.keys():
                self.index_dict[tok] = [document_id]
            else:
                self.index_dict[tok].append(document_id)

    def build(self, output_path: str | Path):
        """Construit l'index inversé pour le titre et le text"""
        assert self.xml_tree is not None, "Load XML before calling this function"

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
                self.treat_field(titre_elem.text, doc_id)

            if texte_elem.text is not None:
                self.treat_field(texte_elem.text, doc_id)
