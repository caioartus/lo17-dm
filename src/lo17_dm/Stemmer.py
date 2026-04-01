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

    def transform_tolist(self, text: str) -> list[str]:
        raise NotImplementedError()

    def transform(self, text: str) -> str:
        raise NotImplementedError()

    def save_table(self, outdir: str):
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

        lemmas = self.transform_tolist(text)
        for token, lemma in zip(tokens, lemmas):
            table["token"].append(token)
            table["lemma"].append(lemma)

        self.lemma_table = pd.DataFrame(table)
        return self.lemma_table

    def _make_spacy_doc(self, tokens: list[str]) -> spacy.tokens.Doc:

        # Each token except last has a trailing space; last token has no trailing space.
        spaces = [True] * (len(tokens) - 1) + [False]
        return spacy.tokens.Doc(self.nlp.vocab, words=tokens, spaces=spaces)

    def _lemmatize_tokens(self, tokens: list[str]) -> list[str]:
        """Prend des tokens en entree et les transforme"""
        if not tokens:
            return []
        doc = self._make_spacy_doc(tokens)
        doc = self.nlp(doc)
        return [token.lemma_ for token in doc]

    def transform_tolist(self, text: str) -> list[str]:
        """Renvoi la liste des tokens lemmatisees a partir d'un text en entree"""
        tokens = [tok for tok in CorpusTokenizer.tokenize(text) if tok]
        return self._lemmatize_tokens(tokens)

    def save_table(self, outdir: str):
        self.lemma_table.to_csv(os.path.join(outdir, "spacy_table.tsv"), sep="\t")

    def transform(self, text: str) -> str:
        return " ".join(self.transform_tolist(text))


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
