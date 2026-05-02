# A AJOUTER : LES GRAPHIQUES

import argparse
from pathlib import Path
from lxml import etree
from lo17_dm.Stemmer import SnowStemmer, SpacyStemmer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--indir", default="./exercices-td/outputs-td2",
                        help="Directory where the input XML file is located")

    parser.add_argument("--inname", default="corpus_filtre",
                        help="Name of the XML file to read (without extension)")

    parser.add_argument("--outdir", default="./exercices-td/outputs-td3",
                        help="Directory where TSV stem tables will be saved")

    parser.add_argument("--outname", default="stems",
                        help="Base name for TSV output files (prefix)")


    args = parser.parse_args()
    assert "." not in args.inname or args.outname, (
        "Il faut préciser uniquement le nom du fichier (sans .xml ou .tsv)"
    )

    indir = Path(args.indir)
    indir.mkdir(parents=True, exist_ok=True)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    input_xml = indir / f"{args.inname}.xml"

    # Load XML
    tree = etree.parse(str(input_xml))

    # Extract text
    all_text = []
    for document in tree.iter("document"):
        titre_elem = document.find("titre")
        texte_elem = document.find("texte")

        if titre_elem is None or texte_elem is None:
            raise ValueError("Missing <titre> or <texte> in XML.")

        if titre_elem.text:
            all_text.append(titre_elem.text)
        if texte_elem.text:
            all_text.append(texte_elem.text)

    all_text_str = " ".join(all_text)
    
    spacy_path = outdir / f"{args.outname}_spacy.tsv"
    snow_path = outdir / f"{args.outname}_snow.tsv"

    # Spacy stemmer
    spacy_stemmer = SpacyStemmer()
    spacy_stemmer.make_table(all_text_str).to_csv(spacy_path, sep="\t", index=False)
    print(f"Spacy stems saved to {spacy_path}")
    
    # Snowball stemmer
    snow_stemmer = SnowStemmer()
    snow_stemmer.make_table(all_text_str).to_csv(snow_path, sep="\t", index=False)
    print(f"Snow stems saved to {snow_path}")


if __name__ == "__main__":
    main()
