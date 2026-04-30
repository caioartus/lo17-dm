import argparse
import os
import sys
from pathlib import Path

from lo17_dm.DataCleaner import DataCleaner


sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

parser = argparse.ArgumentParser()
parser.add_argument("--input", help="Path to input XML", default="./outputs/corpus.xml")
parser.add_argument("--outdir", help="Path to output directory", default="./outputs")
args = parser.parse_args()

input = Path(args.input)
out = Path(args.outdir)
os.makedirs(out, exist_ok=True)


cleaner = DataCleaner()

cleaner.substitute(args.input, args.outdir)
cleaner.save_xml(os.path.join(args.outdir, "clean_corpus.xml"))
