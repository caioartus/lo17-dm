import pandas as pd
from pathlib import Path


class AntiDict:
    def __init__(self):
        self._tokens_list: list[str] | None = None
        self.stopwords: set[str] | None = None
        self.sub_table: pd.DataFrame | None = None
        
    def get_stopwords(self) -> set[str] | None:
        return self.stopwords

    def add_manual_stopwords(self, manual_stopwords: set[str] | None) -> set[str] | None:
        if self.stopwords is not None and manual_stopwords is not None:
            self.stopwords |= manual_stopwords
        else:
            self.stopwords = manual_stopwords

    def build_stopwords(self, tf_idf: pd.DataFrame | Path, thresh: float = 0.7):
        """Builds the stopword set from data"""
        df_tf_idf: pd.DataFrame = pd.read_csv(tf_idf, sep="\t") if isinstance(tf_idf, Path) else tf_idf

        self._tokens_list = df_tf_idf["token"].unique().tolist()
        mean_tfidf = df_tf_idf.groupby("token").mean()
        stopwords = mean_tfidf[mean_tfidf["tf_idf"] <= thresh].index.to_list()
        
        set_stopwords = set(stopwords)
        self.stopwords = set_stopwords
        return set_stopwords

    def build_sub_table(self) -> pd.DataFrame:
        """Construit la table de substitution (token, sub)"""
        
        assert self.stopwords is not None and self._tokens_list is not None, (
            "Run build_stopwords before this function. Stopwords must be defined."
        )
        subs: dict[str, list[str]] = {"token": [], "sub": []}
        for token in self._tokens_list:
            subs["token"].append(token)
            if token in self.stopwords:
                subs["sub"].append("")
            else:
                subs["sub"].append(token)

        self._token = None
        df = pd.DataFrame(subs)
        self.sub_table = df
        return df