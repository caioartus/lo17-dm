import os
import re
from pathlib import Path

import pandas as pd
from lxml import etree


class CorpusTokenizer:
    """Transforme le Corpus en un DataFrame"""

    def __init__(self):
        self._tree: etree._Element | None = None
        self.table: pd.DataFrame | None = None

    def get_table(self) -> pd.DataFrame | None:
        return self.table

    def load_xml(self, path: str | Path):
        self._tree = etree.ElementTree().parse(path)

    @staticmethod
    def simplify(sent: str) -> str:
        sent = sent.lower()  # Conversion en minuscules
        sent = re.sub(r"[^\w-]+", "", sent)  # Suppression des caractères spéciaux
        return sent.strip("\n").strip()

    @staticmethod
    def simplify_many(tokenlist: list[str]) -> list:
        return [CorpusTokenizer.simplify(tok) for tok in tokenlist]

    @staticmethod
    def tokenize(text: str) -> list[str]:
        """Splits and simplifies text into list of tokens"""
        delimiters = ["'", " ", "’"]
        pattern = "|".join(re.escape(d) for d in delimiters)
        result = re.split(pattern, text)
        result = [
            tok
            for tok in CorpusTokenizer.simplify_many(result)
            if tok != "" and tok is not None
        ]
        return result

    def tokenize_corpus(self) -> pd.DataFrame :
        '''Tokenise un document et créé un DataFrame (id, token)'''
        assert self._tree is not None, "XMl n'a pas été chargé, appeler load_xml()"
        
        doc_dict: dict = {"document_id": [], "token": []}
        for document in self._tree.iter("document"):
            article_elem = document.find("article")

            texte_elem = document.find("texte")
            title_elem = document.find("titre")

            if (
                article_elem is None
                or article_elem.text is None
                or texte_elem is None
                or title_elem is None
            ):
                raise ValueError("Error during parsing, None found in elements.")

            id = int(article_elem.text)
            # concat title and text t
            all_text = str(texte_elem.text) + str(title_elem.text)

            # split and simplify the tokens
            tokenlist = CorpusTokenizer.tokenize(all_text)

            for token in tokenlist:
                if token is not None and token != "":
                    doc_dict["document_id"].append(id)
                    doc_dict["token"].append(token)
        
        df = pd.DataFrame(doc_dict)
        self.table = df
        return df

    def save_table(self, outfile_path: Path):
        assert self.table is not None, "Le corpus n'a pas été tokenisé, appeler tokenize_corpus()"

        self.table.to_csv(outfile_path, sep="\t", index=False)
