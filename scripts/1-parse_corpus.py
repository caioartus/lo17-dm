import argparse
from pathlib import Path
from lo17_dm.Parser import CorpusParser

OUTPUTS = Path(__file__).parent.parent / "outputs"
FILENAME = "corpus"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--indir", required=True,
                        help="Path to folder containing all HTML files")

    parser.add_argument("--outdir", default=OUTPUTS,
                        help="Directory where the XML file will be saved")

    parser.add_argument("--outname", default=FILENAME,
                        help="Name of the XML file to generate")


    args = parser.parse_args()
    assert "." not in args.outname, "Il faut préciser uniquement le nom du fichier (sans .xml)"

    indir = Path(args.indir)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    filename = f"{args.outname}.xml"
    outfile = outdir / filename

    corpus = CorpusParser(indir)
    corpus.parseFiles()
    corpus.makeXML()
    corpus.save_xml(outfile)

    print(f"Saved XML to {outfile}")


if __name__ == "__main__":
    main()
