import os
from lo17_dm.Index import Index


os.chdir(os.path.dirname(os.path.abspath(__file__)))


def main():
    index = Index()
    index.load_xml("../outputs/cleaned_corpus.xml")
    index.build("../outputs")


main()
