import os
from pathlib import Path

import numpy as np
import pandas as pd


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
