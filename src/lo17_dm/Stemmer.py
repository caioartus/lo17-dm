import os

import fr_core_news_sm
import pandas as pd
import spacy
from nltk.stem.snowball import SnowballStemmer

from .Tokenizer import CorpusTokenizer


class Stemmer:
    def __init__(self):
        pass

    def make_table(self, text: str) -> pd.DataFrame:
        raise NotImplementedError()

    def transform(self, text: str) -> str:
        raise NotImplementedError()


class SpacyStemmer(Stemmer):
    def __init__(self):
        self.nlp = fr_core_news_sm.load()

    def make_table(self, text: str):
        table: dict[str, list[str]] = {"token": [], "lemma": []}
        tokens = [tok for tok in CorpusTokenizer.tokenize(text) if tok]
        if not tokens:
            self.lemma_table = pd.DataFrame(table)
            return self.lemma_table

        spaces = [True] * (len(tokens) - 1) + [False]
        doc = spacy.tokens.Doc(self.nlp.vocab, words=tokens, spaces=spaces)
        doc = self.nlp(doc)
        for word in doc:
            table["token"].append(word.text)
            table["lemma"].append(word.lemma_)
        self.lemma_table = pd.DataFrame(table)

        return self.lemma_table

    def save_table(self, outdir: str):
        self.lemma_table.to_csv(os.path.join(outdir, "spacy_table.tsv"), sep="\t")

    def transform(self, text: str) -> str:
        lemma_table = self.make_table(text)
        return " ".join(lemma_table["lemma"].astype(str).tolist())


class SnowStemmer(Stemmer):
    def __init__(self):
        self.model = SnowballStemmer("french")

    def transform(self, text: str) -> str:
        doc = CorpusTokenizer.tokenize(text)
        stemmed = []
        for word in doc:
            stemmed.append(self.model.stem(word))
        self.stemed_tokens = stemmed
        return " ".join(self.stemed_tokens)

    def make_table(self, text: str):
        table: dict[str, list[str]] = {"token": [], "lemma": []}
        doc = CorpusTokenizer.tokenize(text)
        for word in doc:
            table["token"].append(word)
            table["lemma"].append(self.model.stem(word))

        self.lemma_table = pd.DataFrame(table)

        return self.lemma_table
