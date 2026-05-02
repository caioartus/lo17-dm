import argparse
from pathlib import Path
from lo17_dm.Index import Index

OUTPUTS = Path(__file__).parent.parent / "outputs"
INNAME = "clean_corpus"
OUTNAME = "lemmes_corpus"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--indir", default=OUTPUTS,
                        help="Directory where the XML file will be loaded")

    parser.add_argument("--inname", default=INNAME, # ou juste corpus pour le TD1 (clean_corpus généré au TD3)
                        help="Name of the XML file to index (without extension)")  

    parser.add_argument("--outdir", default=OUTPUTS,
                        help="Directory where TSV files will be saved")

    parser.add_argument("--outname", default=OUTNAME,
                        help="Base name for TSV output files (without extension)")


    args = parser.parse_args()
    assert "." not in args.inname or args.outname, (
        "Il faut préciser uniquement le nom du fichier (sans .xml ou .tsv)"
    )
    
    indir = Path(args.indir)
    indir.mkdir(parents=True, exist_ok=True)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    
    xmlfilename = f"{args.inname}.xml"
    inpath = indir / xmlfilename

    index = Index()
    index.load_xml(inpath)
    index.build()

    index.save_to_tsv(outdir, args.outname)

    print(f"Index saved to {outdir}")


if __name__ == "__main__":
    main()
