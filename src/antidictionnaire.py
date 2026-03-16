import pandas as pd
import numpy as np
from lxml import etree
import re
from pathlib import Path


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
        Calcule l'IDF (inverse document frequency) pour chaque token.
        idf_t = log10(N / df_t)
            - N = nombre total de documents
            - df_t = nombre de documents contenant le token t
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
        tfidf_{t,d} = tf_{t,d} × idf_t
        """
        if self.tf is None:
            raise RuntimeError("TF non calculé. Appelez compute_tf() d'abord.")
        if self.idf is None:
            raise RuntimeError("IDF non calculé. Appelez compute_idf() d'abord.")

        merged = self.tf.merge(self.idf, on="token", how="left")
        merged["tf_idf"] = merged["tf"] * merged["idf"]

        self.tf_idf = merged[["document_id", "token", "tf_idf"]]
        return self.tf_idf

    def save(self, directory: str | Path):
        """Sauvegarde un DataFrame en CSV (séparateur tabulation)."""
        if self.tf_idf is None:
            raise RuntimeError("IDF non calculé. Appelez compute_tf_idf() d'abord.")

        self.tf_idf.to_csv(os.path.join(directory, "tf_idf.tsv"), sep="\t", index=False)
        self.tf.to_csv(os.path.join(directory, "tf.tsv"), sep="\t", index=False)
        self.idf.to_csv(os.path.join(directory, "idf.tsv"), sep="\t", index=False)


class CorpusSegmenter:
    def __init__(self):
        self.xml_path = None
        self.tree = None
        self.table: pd.DataFrame | None = None

    def get_table(self) -> pd.DataFrame:
        return self.table

    def simplify(self, sent) -> str:
        sent = sent.lower()  # Conversion en minuscules
        sent = re.sub(r"\W+", " ", sent)  # Suppression des caractères spéciaux
        return sent.strip()

    def load_xml(self, path: str):
        self.tree = etree.ElementTree().parse(path)

    def segment(self):
        """Tokenises document and creates id, token dataframe"""
        doc_dict: dict = {"document_id": [], "token": []}
        for document in self.tree.iter("document"):
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
            all_text = str(texte_elem.text) + str(title_elem.text)

            # split spaces to get all the words
            tokenlist = all_text.split(" ")

            # simplify to lower case, strip, rm special chars etc.
            tokenlist = [self.simplify(token) for token in tokenlist]

            for token in tokenlist:
                if token is not None and token != "":
                    doc_dict["document_id"].append(id)
                    doc_dict["token"].append(token)
        df = pd.DataFrame(doc_dict)
        self.table = df


class DataCleaner:
    def __init__(
        self,
    ):
        self.stopwords: set | None = None
        self.sub_tab: pd.DataFrame | None = None

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

    def build_sub_tab(self, token_list: list):
        """Builds the table with two columns one for the orinal token and one for the replacement with empty string if its a stop word"""
        assert self.stopwords is not None, (
            "Run build_stopwords before this function. Stopwords must be defined."
        )

        sub_tab: dict[str, list[str]] = {"token": [], "sub": []}
        for token in token_list:
            sub_tab["token"].append(token)
            if token in self.stopwords:
                sub_tab["sub"].append("")
            else:
                # for now if its not to be substituted we just leave the token as is
                # TODO - Implement stemming ?
                sub_tab["sub"].append(token)
        self.sub_tab = pd.DataFrame(sub_tab)

        return self.sub_tab


if __name__ == "__main__":
    import argparse
    import os
    from pathlib import Path

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
    segmenter = CorpusSegmenter()
    segmenter.load_xml(args.input)
    segmenter.segment()

    # Processing
    processor = TFIDFProcessor(segmenter.get_table())
    tf = processor.compute_tf()
    idf = processor.compute_idf()
    tf_idf = processor.compute_tf_idf()

    # Persistence
    processor.save(args.outdir)

    # make stop words list from computed metrics
    cleaner = DataCleaner()
    cleaner.build_stopwords(tf_idf)
    sub_tab = cleaner.build_sub_tab(idf["token"].unique())
    print(sub_tab)
