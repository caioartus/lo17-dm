import nltk
from nltk.stem.snowball import SnowballStemmer
import spacy
import pandas as pd
import os
import fr_core_news_sm
from Tokenizer import CorpusTokenizer

class Stemmer:
    def __init__(self):
        pass

    def stem(self, text: str):
        raise NotImplementedError()


class SpacyStemmer(Stemmer):
    def __init__(self):
        self.nlp = fr_core_news_sm.load()

    def stem(self, text: str):
        table: dict[str, list[str]] = {"token": [], "lemma": []}
        doc = self.nlp(text)

        for word in doc:
            table["token"].append(word)
            table["lemma"].append(word.lemma_)

        self.lemma_table = pd.DataFrame(table)

        return self.lemma_table

    def save_table(self, outdir: str):
        self.lemma_table.to_csv(os.path.join(outdir, "sapcy_table.tsv"), sep="\t")


class SnowStemmer(Stemmer):
    def __init__(self):
        self.model = SnowballStemmer("french")

    def stem(self, text: str):
        table: dict[str, list[str]] = {"token": [], "lemma": []}
        doc = 
        for word in doc:
            table["token"].append(word)
            table["lemma"].append(self.model.stem(word))

        self.lemma_table = pd.DataFrame(table)

        return self.lemma_table


def stemming_demo():

    # Initialize stemmer for English
    stemmer = SnowballStemmer("french")

    # Test words with different morphological patterns
    test_words = ["cours", "courir", "coureur", "courons", "courera"]

    print("Basic Stemming Results:")
    print("-" * 30)
    for word in test_words:
        stem = stemmer.stem(word)
        print(f"{word:12} → {stem}")


def main():
    stemmer = SpacyStemmer()
    res = stemmer.stem(
        "J'aime bien manger des frites a la mayonnaise, un maillot de bain et un morceau de pain, avec des pains au vin il vint",
    )
    print(res)


if __name__ == "__main__":
    main()
