import pandas as pd


class AntiDict:
    def __init__(self):
        self.stopwords: set | None = None
        self.sub_table: pd.DataFrame = None

    def build_stopwords(self, tf_idf: pd.DataFrame):
        """Builds the stopword set from data"""

        thresh = 0.7
        mean_tfidf = tf_idf.groupby("token").mean()
        stopwords = mean_tfidf[mean_tfidf["tf_idf"] <= thresh].index.to_list()
        self.stopwords = set(stopwords)
        print(stopwords)
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
