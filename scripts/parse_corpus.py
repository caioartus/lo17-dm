import argparse
import os
import sys
from os import makedirs
from pathlib import Path

from lo17_dm.Parser import CorpusParser


argparser = argparse.ArgumentParser()
argparser.add_argument(
    "--input", help="Path to folder containing all of the html files", required=True
)
argparser.add_argument(
    "--outdir",
    help="Path to directory where output xml file will be saved",
    required=False,
    default="./outputs",
)
args = argparser.parse_args()

input = Path(args.input)
out = Path(args.outdir)
makedirs(out, exist_ok=True)

corpus = CorpusParser(input)
corpus.parseFiles()
corpus.makeXML()
corpus.save_xml(os.path.join(out, "corpus.xml"))
print("Saved XML to ", out)
