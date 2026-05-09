from pathlib import Path

import pandas as pd
from lxml import etree

from lo17_dm.AntiDict import AntiDict
from lo17_dm.Stemmer import SpacyStemmer, Stemmer
from lo17_dm.Tokenizer import CorpusTokenizer


class DataCleaner:
    """Class for cleaning and processing XML data with anti-dictionary substitution and lemmatisation."""

    def __init__(
        self,
        stemmer: Stemmer = SpacyStemmer(),
        manual_stopwords: set[str] | None = None,
    ):
        self._stemmer: Stemmer = stemmer
        self.stopwords: set[str] = (
            manual_stopwords if manual_stopwords is not None else set()
        )
        self._sub_table: pd.DataFrame | None = None

    def get_stopwords(self) -> set[str] | None:
        return self.stopwords

    def export_stop_words(self, output_path: str | Path) -> None:
        """Export les stopwords dans un fichier texte"""
        assert self.stopwords is not None, "Aucun stopword à exporter"
        output_path = Path(output_path)
        with open(output_path, "w", encoding="utf-8") as f:
            for sw in self.stopwords:
                f.write(f"{sw}\n")
        print(f"Stopwords exportés dans {output_path}")

    def get_all_lemmas(self) -> set[str] | None:
        assert self._sub_table is not None, (
            "La table de substitution est vide, appeler build_sub_table()"
        )
        # les lemmes sont tous les sub qui ne sont pas des stopwords (ie. != "")
        return set(self._sub_table["sub"].dropna().loc[lambda s: s != ""])

    def _stem(self, text: str | None) -> str:
        if text is None or text == "":
            return ""
        return self._stemmer.transform(text)

    def _substitue(self, text: str) -> str:
        """Élimine ou remplace les tokens d'un texte selon un fichier de substitution.

        Le fichier de substitution est un TSV à deux colonnes : token et sub.
        Si sub est vide (NaN ou ""), le token est supprimé. Sinon il est remplacé par sub.
        """
        assert self._sub_table is not None, (
            "La table de substitution est vide, appeler build_sub_table()"
        )

        sub_dict = {}
        for _, row in self._sub_table.iterrows():
            sub = row["sub"]
            sub_dict[row["token"]] = "" if pd.isna(sub) else str(sub)

        tokens = CorpusTokenizer.tokenize(text)
        result = []
        for tok in tokens:
            replacement = sub_dict.get(tok, tok)  # conserver si absent de la table
            if replacement != "":
                result.append(replacement)
        return " ".join(result)

    def build_sub_table(self, df_tf_idf: pd.DataFrame):
        """Construit la table de substitution à deux colonnes avec pour chaque ligne :
        * (token, "")       si le token est un stopword
        * (token, lemme)    sinon
        """
        anti_dict = AntiDict()

        # Définition des stopwords
        anti_dict.build_stopwords(df_tf_idf)
        anti_dict.add_manual_stopwords(self.stopwords)
        self.stopwords = anti_dict.get_stopwords() or self.stopwords

        # Création de la table de substitution + lemmatisation
        sub_table = anti_dict.build_sub_table()
        sub_table["sub"] = sub_table["sub"].apply(self._stem)

        self._sub_table = sub_table

    def apply_substitue_to_xml(
        self, input_path: str | Path, output_path: str | Path
    ) -> None:
        """Applique substitue sur les champs titre et texte de chaque document du corpus XML."""
        input_path = Path(input_path)
        output_path = Path(output_path)

        tree = etree.parse(str(input_path))
        root = tree.getroot()

        for document in root.iter("document"):
            titre_elem = document.find("titre")
            texte_elem = document.find("texte")

            if titre_elem is not None and titre_elem.text:
                titre_elem.text = self._substitue(titre_elem.text)
            if texte_elem is not None and texte_elem.text:
                texte_elem.text = self._substitue(texte_elem.text)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(etree.tostring(root, pretty_print=True, encoding="unicode"))

        print(f"XML filtré sauvegardé dans {output_path}")
