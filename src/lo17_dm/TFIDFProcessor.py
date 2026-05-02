import os
from pathlib import Path

import numpy as np
import pandas as pd


class TFIDFProcessor:
    """Classe responsable du calcul des TF, IDF et TF-IDF 
    à partir d'un corpus déjà segmenté en tokens.

    Le fichier d'entrée doit contenir :
        - document_id : identifiant du document
        - token       : token extrait du document
    """

    def __init__(self, token_df: pd.DataFrame | None = None, token_path: Path | None = None):
        """
        Initialise le processeur TF-IDF avec un DataFrame contenant les tokens.
        - token_path : CSV avec les colonnes 'document_id' et 'token'
        - token_df : DataFrame avec les colonnes 'document_id' et 'token'
        """
        assert token_df is not None or token_path is not None, "Il est nécessaire de soumettre les tokens pour calculer la TF-IDF"
        
        if token_df is None : # (and token_path is not None)
            token_df = pd.read_csv(token_path, sep="\t")
        
        if not {"document_id", "token"}.issubset(token_df.columns):
            raise ValueError("Le DataFrame doit contenir 'document_id' et 'token'.")

        self.tokens = token_df.copy()
        self.tf: pd.DataFrame | None = None
        self.idf: pd.DataFrame | None  = None
        self.tf_idf: pd.DataFrame | None  = None

    def compute_tf(self) -> pd.DataFrame:
        """Calcule le TF (term frequency) pour chaque couple (document, token)."""
        datafrm = (
            self.tokens.groupby(["document_id", "token"]).size().reset_index(name="tf")
        )
        self.tf = datafrm
        return datafrm

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
        
        datafrm = df_t[["token", "idf"]]
        self.idf = datafrm
        return datafrm

    def compute_tf_idf(self) -> pd.DataFrame:
        """
        Calcule le TF-IDF pour chaque couple (document, token).
        tfidf_{t,d} = tf_{t,d} x idf_t
        """
        if self.tf is None:
            raise RuntimeError("TF non calculé. Appelez compute_tf() d'abord.")
        if self.idf is None:
            raise RuntimeError("IDF non calculé. Appelez compute_idf() d'abord.")

        # left join -> Si un token de self.tf n’existe pas dans self.idf, les colonnes venant de self.idf seront NaN.
        merged = self.tf.merge(self.idf, on="token", how="left")
        
        merged["tf_idf"] = merged["tf"] * merged["idf"]
        self.tf_idf = merged[["document_id", "token", "tf_idf"]]
        return self.tf_idf

    def save_all(self, directory: str | Path):
        """Sauvegarde les DataFrame en TSV (= CSV avec séparateur tabulation)."""
        if self.tf is None or self.idf is None or self.tf_idf is None :
            raise RuntimeError("TF-IDF non calculé. Appelez compute_tf_idf() d'abord.")

        self.tf_idf.to_csv(os.path.join(directory, "tf_idf.tsv"), sep="\t", index=False)
        self.tf.to_csv(os.path.join(directory, "tf.tsv"), sep="\t", index=False)
        self.idf.to_csv(os.path.join(directory, "idf.tsv"), sep="\t", index=False)
        
    def save(self, file_path: str | Path):
        """Sauvegarde un DataFrame en TSV (= CSV avec séparateur tabulation)."""
        if self.tf_idf is None :
            raise RuntimeError("TF-IDF non calculé. Appelez compute_tf_idf() d'abord.")

        file_path = Path(file_path)
        self.tf_idf.to_csv(os.path.join(file_path, "tf_idf.tsv"), sep="\t", index=False)
