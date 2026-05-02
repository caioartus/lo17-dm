import argparse
from pathlib import Path

import pandas as pd
from lxml import etree  # type: ignore[import-untyped]

from lo17_dm.AntiDict import AntiDict
from lo17_dm.TFIDFProcessor import TFIDFProcessor
from lo17_dm.Tokenizer import CorpusTokenizer

#  ============== Détermination de l’anti-dictionnaire (indexation des tokens) ==============

def segmente(infile: Path, outfile_path: Path) -> pd.DataFrame:
    tokenizer = CorpusTokenizer()
    tokenizer.load_xml(infile)
    tokenizer.tokenize_corpus()
    
    df = tokenizer.get_table()
    if df is None: # vérification
        raise RuntimeError("Le corpus n'a pas pu être tokenisé, retenter d'appeler tokenize_corpus()")
    
    tokenizer.save_table(outfile_path)
    print(f"Tokens sauvegardés dans {outfile_path}")
    return df

# ========================== Génération du corpus filtré ==========================

def substitue(text: str, sub_table_path: str | Path) -> str:
    """Élimine ou remplace les tokens d'un texte selon un fichier de substitution.

    Le fichier de substitution est un TSV à deux colonnes : token et sub.
    Si sub est vide (NaN ou ""), le token est supprimé. Sinon il est remplacé par sub.
    """
    sub_df = pd.read_csv(sub_table_path, sep="\t")
    sub_dict = {}
    for _, row in sub_df.iterrows():
        sub = row["sub"]
        sub_dict[row["token"]] = "" if pd.isna(sub) else str(sub)

    tokens = CorpusTokenizer.tokenize(text)
    result = []
    for tok in tokens:
        replacement = sub_dict.get(tok, tok)  # conserver si absent de la table
        if replacement != "":
            result.append(replacement)
    return " ".join(result)

def apply_substitue_to_xml(
    input_path: str | Path, sub_table_path: str | Path, output_path: str | Path
) -> None:
    """Applique substitue sur les champs titre et texte de chaque document du corpus XML."""
    input_path = Path(input_path)
    output_path = Path(output_path)

    tree = etree.parse(str(input_path))
    root = tree.getroot()

    for document in root.iter("document"):
        titre_elem = document.find("titre")
        texte_elem = document.find("texte")

        if titre_elem is not None and titre_elem.text:
            titre_elem.text = substitue(titre_elem.text, sub_table_path)
        if texte_elem is not None and texte_elem.text:
            texte_elem.text = substitue(texte_elem.text, sub_table_path)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(etree.tostring(root, pretty_print=True, encoding="unicode"))

    print(f"XML filtré sauvegardé dans {output_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--infile", default="./outputs/corpus.xml",
                        help="Chemin vers le corpus XML d'entrée")

    parser.add_argument("--outdir", default="./exercices-td/outputs-td2",
                        help="Dossier de sortie pour les fichiers TSV et XML")

    parser.add_argument("--tokenfile", default="tokens",
                        help="Nom du fichier TSV (intermédiaire) pour stocker les tokens")
    
    parser.add_argument("--outname", default="corpus_filtre",
                        help="Nom du fichier XML filtré (sans extension)")
    


    args = parser.parse_args()
    assert "." not in args.outname or "." not in args.token_file, (
        "Il faut préciser uniquement le nom du fichier (sans .xml)"
    )
    infile = Path(args.infile)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    
    token_path = outdir / f"{args.tokenfile}.tsv"
    filtered_xml_path = outdir / f"{args.outname}.xml"

    # Tokenisation du corpus
    df_token = segmente(infile, token_path)
    
    # Calcul du TF, IDF, et TF-IDF
    processor = TFIDFProcessor(df_token)
    processor.compute_tf()
    print("TF calculé.")
    processor.compute_idf()
    print("IDF calculé.")
    df_tf_idf = processor.compute_tf_idf()
    print("TF-IDF calculé.")
    processor.save_all(outdir)
    print(f"tf.tsv, idf.tsv et tf-idf.tsv sauvegardés dans {outdir}/")

    # Construction de l'anti-dictionnaire
    anti_dict = AntiDict()
    anti_dict.build_stopwords(df_tf_idf)
    anti_dict.build_sub_table()

    sub_table_path = outdir / "sub_table.tsv"
    assert anti_dict.sub_table is not None and anti_dict.stopwords is not None
    anti_dict.sub_table.to_csv(sub_table_path, sep="\t", index=False)
    print(f"Table de substitution sauvegardée dans {sub_table_path}")
    print(f"  -> {len(anti_dict.stopwords)} stopwords détectés")

    # Substitue pour produire le XML filtré
    print(filtered_xml_path)
    apply_substitue_to_xml(infile, sub_table_path, filtered_xml_path)


if __name__ == "__main__":
    main()