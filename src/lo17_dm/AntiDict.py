import pandas as pd
from pathlib import Path


class AntiDict:
    def __init__(self):
        self._tokens_list: list[str] | None = None
        self.stopwords: set[str] | None = None
        self.sub_table: pd.DataFrame | None = None

    def get_stopwords(self) -> set[str] | None:
        return self.stopwords

<<<<<<< HEAD
    def add_manual_stopwords(self, manual_stopwords: set[str] | None) -> set[str] | None:
=======
    def add_manual_stopwords(
        self, manual_stopwords: set[str] | None
    ) -> set[str] | None:
>>>>>>> rapport
        if self.stopwords is not None and manual_stopwords is not None:
            self.stopwords |= manual_stopwords
        else:
            self.stopwords = manual_stopwords

<<<<<<< HEAD
    def build_stopwords(self, tf_idf: pd.DataFrame | Path, thresh: float = 0.7):
        """Builds the stopword set from data"""
        df_tf_idf: pd.DataFrame = pd.read_csv(tf_idf, sep="\t") if isinstance(tf_idf, Path) else tf_idf
=======
    """
        def build_from_file(self, path: str | Path):
            path = Path(path)
            if not path.exists():
                raise FileNotFoundError("Path not found")
            self.sub_table = pd.read_csv(path, sep="\t")
            self.stopwords = set(
                self.sub_table[self.sub_table["sub"].isna()]["token"].to_list()
            )
    """

    def build_stopwords(
        self,
        df_tf_idf: pd.DataFrame | None = None,
        tf_idf_path: Path | None = None,
        thresh: float = 0.7,
    ):
        """Builds the stopword set from data"""
        assert df_tf_idf is not None or tf_idf_path is not None, (
            "Il est nécessaire de soumettre les tokens pour calculer la TF-IDF"
        )

        if df_tf_idf is None:  # (and tf_idf_path is not None)
            df_tf_idf = pd.read_csv(tf_idf_path, sep="\t")
>>>>>>> rapport

        self._tokens_list = df_tf_idf["token"].unique().tolist()
        mean_tfidf = df_tf_idf.groupby("token").mean()
        stopwords = mean_tfidf[mean_tfidf["tf_idf"] <= thresh].index.to_list()

        set_stopwords = set(stopwords)
        self.stopwords = set_stopwords
        return set_stopwords

    def build_sub_table(self) -> pd.DataFrame:
        """Construit la table de substitution (token, sub)"""

        if self.stopwords is None or self._tokens_list is None:
            raise ValueError(
                "Run build_stopwords before this function. Stopwords must be defined."
            )

        subs: dict[str, list[str]] = {"token": [], "sub": []}
        for token in self._tokens_list:
            subs["token"].append(token)
            if token in self.stopwords:
                subs["sub"].append("")
            else:
                subs["sub"].append(token)

        df = pd.DataFrame(subs)
        self.sub_table = df
        return df
