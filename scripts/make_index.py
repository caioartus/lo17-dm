import os
from lo17_dm.Index import Index


os.chdir(os.path.dirname(os.path.abspath(__file__)))


def main():
    index = Index()
    index.load_xml("../outputs/clean_corpus.xml")
    index.build("../outputs")
    index.save_to_tsv("../outputs")


main()
