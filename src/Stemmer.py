import nltk
from nltk.stem.snowball import SnowballStemmer
import spacy
import pandas as pd
import os
import fr_core_news_sm
from Tokenizer import CorpusTokenizer
from lxml import etree


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
        tokens = CorpusTokenizer.tokenize(text)
        spaces = [True] * (len(tokens) - 1) + [False]
        doc = spacy.tokens.Doc(self.nlp.vocab, words=tokens, spaces=spaces)
        doc = self.nlp(doc)
        seen: set[str] = set()
        for word in doc:
            if word.text not in seen:
                seen.add(word.text)
                table["token"].append(word.text)
                table["lemma"].append(word.lemma_)

        self.lemma_table = pd.DataFrame(table)

        return self.lemma_table

    def save_table(self, outdir: str):
        self.lemma_table.to_csv(os.path.join(outdir, "sapcy_table.tsv"), sep="\t")


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
        seen: set[str] = set()
        for word in doc:
            if word not in seen:
                seen.add(word)
                table["token"].append(word)
                table["lemma"].append(self.model.stem(word))

        self.lemma_table = pd.DataFrame(table)

        return self.lemma_table


def main():
    """Generation de tableaux token, lemme pour analyse"""
    all_text = []
    tree = etree.ElementTree().parse("../outputs/clean_corpus.xml")
    for document in tree.iter("document"):
        titre_elem = document.find("titre")
        texte_elem = document.find("texte")
        if titre_elem is None or texte_elem is None:
            raise ValueError("Nones found, make sure corpus is correctly parsed.")
        if titre_elem.text is not None:
            all_text.append(titre_elem.text)
        if texte_elem.text is not None:
            all_text.append(texte_elem.text)

    all_text_str = " ".join(all_text)

    stemmer = SpacyStemmer()
    stemmer.make_table(all_text_str).to_csv(
        "../outputs/spacy_stems.tsv", sep="\t", index=False
    )

    stemmer = SnowStemmer()

    stemmer.make_table(all_text_str).to_csv(
        "../outputs/snow_stems.tsv", sep="\t", index=False
    )


if __name__ == "__main__":
    main()
