import argparse
from pathlib import Path

from lo17_dm.Tokenizer import CorpusTokenizer
from lo17_dm.TFIDFProcessor import TFIDFProcessor
from lo17_dm.DataCleaner import DataCleaner

MANUAL_STOPWORDS: set[str] = set()

OUTPUTS = Path(__file__).parent.parent / "outputs"
INNAME = "corpus"
OUTNAME = "clean_corpus"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--indir", default=OUTPUTS, help="Directory where the input XML file is located"
    )

    parser.add_argument(
        "--inname",
        default=INNAME,
        help="Name of the XML file to clean (without extension)",
    )

    parser.add_argument(
        "--outdir",
        default=OUTPUTS,
        help="Directory where the cleaned XML file will be saved",
    )

    parser.add_argument(
        "--outname",
        default=OUTNAME,
        help="Name of the cleaned XML file (without extension)",
    )

    args = parser.parse_args()
    assert "." not in args.inname or "." not in args.outname, (
        "Il faut préciser uniquement le nom du fichier (sans .xml)"
    )

    indir = Path(args.indir)
    indir.mkdir(parents=True, exist_ok=True)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    input_xml = indir / f"{args.inname}.xml"
    output_xml = outdir / f"{args.outname}.xml"

    tokenizer = CorpusTokenizer()
    tokenizer.load_xml(input_xml)
    tokenizer.tokenize_corpus()
    token_df = tokenizer.get_table()

    processor = TFIDFProcessor(token_df)
    processor.compute_tf()
    processor.compute_idf()
    df_tf_idf = processor.compute_tf_idf()

    cleaner = DataCleaner(manual_stopwords=MANUAL_STOPWORDS)
    cleaner.build_sub_table(df_tf_idf)
    cleaner.export_stop_words(OUTPUTS / "stop_words.txt")
    cleaner.apply_substitue_to_xml(input_xml, output_xml)

    print(f"Cleaned XML saved to {output_xml}")


if __name__ == "__main__":
    main()
