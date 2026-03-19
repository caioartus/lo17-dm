import pandas as pd
import numpy as np
from lxml import etree
import re
from pathlib import Path
import nltk
from nltk.stem.snowball import SnowballStemmer
from Tokenizer import CorpusTokenizer


class TFIDFProcessor:
    """Classe responsable du calcul des matrices TF, IDF et TF-IDF
    à partir d'un corpus déjà segmenté en tokens.

    Le fichier d'entrée doit contenir :
        - document_id : identifiant du document
        - token       : token extrait du document
    """

    def __init__(self, token_df):
        """
        Initialise le processeur TF-IDF avec un DataFrame contenant les tokens.
        - token_df : pd.DataFrame avec les colonnes 'document_id' et 'token'
        """
        if not {"document_id", "token"}.issubset(token_df.columns):
            raise ValueError("Le DataFrame doit contenir 'document_id' et 'token'.")

        self.tokens = token_df.copy()
        self.tf = None
        self.idf = None
        self.tf_idf = None

    def compute_tf(self) -> pd.DataFrame:
        """Calcule le TF (term frequency) pour chaque couple (document, token)."""
        self.tf = (
            self.tokens.groupby(["document_id", "token"]).size().reset_index(name="tf")
        )
        return self.tf

    def compute_idf(self) -> pd.DataFrame:
        """
        Calcule l'IDF (idf_t = log10(N / df_t)) pour chaque token.
        avec : N = nb_doc, df_t = nb_doc_with_t
        """
        N = self.tokens["document_id"].nunique()

        df_t = (
            self.tokens.drop_duplicates(subset=["document_id", "token"])
            .groupby("token")
            .size()
            .reset_index(name="df")
        )

        df_t["idf"] = np.log10(N / df_t["df"])
        self.idf = df_t[["token", "idf"]]
        return self.idf

    def compute_tf_idf(self) -> pd.DataFrame:
        """
        Calcule le TF-IDF pour chaque couple (document, token).
        tfidf_{t,d} = tf_{t,d} x idf_t
        """
        if self.tf is None:
            raise RuntimeError("TF non calculé. Appelez compute_tf() d'abord.")
        if self.idf is None:
            raise RuntimeError("IDF non calculé. Appelez compute_idf() d'abord.")

        merged = self.tf.merge(self.idf, on="token", how="left")
        merged["tf_idf"] = merged["tf"] * merged["idf"]
        self.tf_idf = merged[
            [
                "document_id",
                "token",
                "tf_idf",
            ]
        ]
        return self.tf_idf

    def save(self, directory: str | Path):
        """Sauvegarde un DataFrame en CSV (séparateur tabulation)."""
        if self.tf_idf is None:
            raise RuntimeError("IDF non calculé. Appelez compute_tf_idf() d'abord.")

        self.tf_idf.to_csv(os.path.join(directory, "tf_idf.tsv"), sep="\t", index=False)
        self.tf.to_csv(os.path.join(directory, "tf.tsv"), sep="\t", index=False)
        self.idf.to_csv(os.path.join(directory, "idf.tsv"), sep="\t", index=False)


class AntiDict:
    def __init__(self):
        self.stopwords: set | None = None
        self.sub_table: pd.DataFrame = None

    def build_stopwords(self, tf_idf: pd.DataFrame):
        """Builds the stopword set from data"""
        # For now we only use tf-idf mean bottom 100 words as stop words.
        # TODO - Review how we select stop words from statistics
        N = 100
        stopwords = (
            tf_idf.groupby("token")["tf_idf"]
            .mean()
            .sort_values()
            .iloc[0:N]
            .index.to_list()
        )
        self.stopwords = set(stopwords)
        return self.stopwords

    def build_sub_table(self, token_list: list):
        """Builds the dict for replacements"""
        assert self.stopwords is not None, (
            "Run build_stopwords before this function. Stopwords must be defined."
        )
        subs: dict[str, list[str]] = {"token": [], "sub": []}
        for token in token_list:
            subs["token"].append(token)
            if token in self.stopwords:
                subs["sub"].append("")
            else:
                # for now if its not to be substituted we just leave the token as is
                # TODO - Implement stemming ?
                subs["sub"].append(token)
        self.sub_table = pd.DataFrame(subs)
        return self.sub_table


class DataCleaner:
    """A MODIFIER -> SEPARER LA LOGIQUE"""

    def __init__(self):
        self.anti_dict: AntiDict = None
        self.clean_xml = None

    def apply_treatment(self, input_path: str, treatment_func):
        """Applies a text treatment function to the title and text sections of the XML."""
        tree = etree.ElementTree().parse(input_path)
        for document in tree.iter("document"):
            titre_elem = document.find("titre")
            texte_elem = document.find("texte")
            if titre_elem is None or texte_elem is None:
                raise ValueError("Nones found, make sure corpus is correctly parsed.")
            if titre_elem.text is not None:
                titre_elem.text = treatment_func(titre_elem.text)
            if texte_elem.text is not None:
                texte_elem.text = treatment_func(texte_elem.text)
        self.clean_xml = etree.tostring(tree, pretty_print=True, encoding="unicode")
        return self.clean_xml

    def build_anti_dict(self, tf_idf: pd.DataFrame, outpath: str | None):
        self.anti_dict = AntiDict()
        self.anti_dict.build_stopwords(tf_idf)
        self.anti_dict.build_sub_table(tf_idf["token"].unique().tolist())
        if outpath is not None:
            self.anti_dict.sub_table.to_csv(outpath, sep="\t", index=False)
        return self.anti_dict.sub_table

    def substitute(self, input_path: str):
        """Builds cleaned XML from original XML, cleaning the contents of title and text sections"""

        assert self.anti_dict is not None, "Must run build_anti_dict before."

        sub_dict = self.anti_dict.sub_table.set_index("token").T.to_dict(
            orient="records"
        )[0]

        def treatment(text):
            cleaned_tokens = []
            for tok in CorpusTokenizer.tokenize(text):
                sub = sub_dict.get(tok, tok)
                if sub != "":
                    cleaned_tokens.append(sub)
            return " ".join(cleaned_tokens)

        return self.apply_treatment(input_path, treatment)

    def save_xml(self, path: str | Path) -> None:
        """Save in XML file"""
        path = Path(path)
        with open(path, "w") as f:
            f.write(self.clean_xml)


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input", help="Path to input XML", default="outputs/corpus.xml"
    )
    parser.add_argument("--outdir", help="Path to output directory", default="outputs")
    args = parser.parse_args()

    input = Path(args.input)
    out = Path(args.outdir)
    os.makedirs(out, exist_ok=True)

    # Initialization
    segmenter = CorpusTokenizer()
    segmenter.load_xml(args.input)
    segmenter.tokenize_corpus()

    # Processing
    processor = TFIDFProcessor(segmenter.get_table())
    tf = processor.compute_tf()
    idf = processor.compute_idf()
    tf_idf = processor.compute_tf_idf()

    # Persistence
    processor.save(args.outdir)

    # make stop words list from computed metrics
    cleaner = DataCleaner()

    cleaner.build_anti_dict(tf_idf, outpath=os.path.join(args.outdir, "sub_table.tsv"))

    cleaner.substitute(args.input)
    cleaner.save_xml(os.path.join(args.outdir, "clean_corpus.xml"))
