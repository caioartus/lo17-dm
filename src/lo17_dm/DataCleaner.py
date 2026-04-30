from collections.abc import Callable
from pathlib import Path

import pandas as pd
from lxml import etree

from lo17_dm.AntiDict import AntiDict
from lo17_dm.Stemmer import SpacyStemmer, Stemmer
from lo17_dm.TFIDFProcessor import TFIDFProcessor
from lo17_dm.Tokenizer import CorpusTokenizer


class DataCleaner:
    """Class for cleaning and processing XML data with anti-dictionary substitution."""

    def __init__(self, stemmer: Stemmer = SpacyStemmer()):
        self.anti_dict: AntiDict | None = None
        self.stemmer: Stemmer = stemmer
        self.clean_xml: str | None = None
        self.unstopped: str | None = None
        self.stemmed: str | None = None

    @staticmethod
    def apply_treatment(
        xml_text: str, treatment_func: Callable[[str], str], output_path: str | Path
    ) -> str:
        """Applies a text treatment function to the title and text sections of an XML string.

        This method does not perform file I/O; it operates on XML content passed in.
        """
        tree = etree.fromstring(xml_text)

        for document in tree.iter("document"):
            titre_elem = document.find("titre")
            texte_elem = document.find("texte")
            if titre_elem is None or texte_elem is None:
                raise ValueError("Nones found, make sure corpus is correctly parsed.")

            if titre_elem.text is not None:
                titre_elem.text = treatment_func(titre_elem.text)

            if texte_elem.text is not None:
                texte_elem.text = treatment_func(texte_elem.text)

        treated = etree.tostring(tree, pretty_print=True, encoding="unicode")

        with open(output_path, "w") as f:
            f.write(treated)

        return treated

    def build_anti_dict(
        self,
        tf_idf: pd.DataFrame,
        outpath: str | Path | None = None,
    ) -> pd.DataFrame:
        """Construir l'anti dictionnaire sous forme de tableau token, remplacement, et le sauvegarde"""

        self.anti_dict = AntiDict()
        self.anti_dict.build_stopwords(tf_idf)
        self.anti_dict.build_sub_table(tf_idf["token"].unique().tolist())
        if outpath is not None:
            self.anti_dict.sub_table.to_csv(Path(outpath), sep="\t", index=False)
        return self.anti_dict.sub_table

    def remove_stopwords(self, text: str) -> str:
        assert self.anti_dict is not None, "Must run build_anti_dict before."
        if text is None:
            return None

        sub_dict = self.anti_dict.sub_table.set_index("token").T.to_dict(
            orient="records"
        )[0]
        cleaned_tokens = []
        for tok in CorpusTokenizer.tokenize(text):
            if not tok:
                continue
            sub = sub_dict.get(tok, tok)
            if sub != "":
                cleaned_tokens.append(sub)

        return " ".join(cleaned_tokens)

    def stem(self, text: str | None) -> str | None:
        if text is None:
            return None
        res = self.stemmer.transform(text)
        return res

    def substitute(
        self,
        input_path: str | Path,
        tmp_dir: str | Path,
    ) -> str:
        """Builds cleaned XML from original XML, removing stopwords and performing stemming/lemmatisation."""
        input_path = Path(input_path)
        tmp_dir = Path(tmp_dir)

        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        if not tmp_dir.exists():
            raise FileNotFoundError("Provided tmp_dir path does not exist")

        sub_tab_path = tmp_dir / "sub_table.tsv"
        stemmed_xml_path = tmp_dir / "stemmed_corpus.xml"
        final_xml_path = tmp_dir / "cleaned_corpus.xml"

        with open(input_path, encoding="utf-8") as f:
            xml_text = f.read()

        self.stemmed = self.apply_treatment(
            xml_text, lambda text: self.stem(text) or "", output_path=stemmed_xml_path
        )

        # Tokenize stemmed document to calculate tf-idf
        segmenter = CorpusTokenizer()
        segmenter.load_xml(stemmed_xml_path)
        segmenter.tokenize_corpus()

        # build tf_idf tables
        processor = TFIDFProcessor(segmenter.get_table())
        tf = processor.compute_tf()
        idf = processor.compute_idf()
        tf_idf = processor.compute_tf_idf()

        processor.save(tmp_dir)  # save intermediate files

        # construire l'anti dict après le lemmatisation
        self.build_anti_dict(tf_idf, sub_tab_path)

        self.unstopped = self.apply_treatment(
            self.stemmed,
            lambda text: self.remove_stopwords(text) or "",
            output_path=final_xml_path,
        )

        self.clean_xml = self.unstopped
        return self.clean_xml

    def save_xml(self, path: str | Path) -> None:
        """Save in XML file"""
        assert self.clean_xml is not None, (
            "Must run substitute before saving clean XML."
        )
        path = Path(path)
        with open(path, "w") as f:
            f.write(self.clean_xml)
