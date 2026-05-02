from lo17_dm.KeyWordExtractor import KeyWordExtractor
from lo17_dm.Stemmer import SpacyStemmer

extractor = KeyWordExtractor(
    lemma_table_path="outputs/lemmes_corpus.tsv",
    stopwords_file="outputs/stop_words.tsv"
)

s = "Quels sont les articles dont le titre évoque la recherche ?"
print(extractor.extract(s))
