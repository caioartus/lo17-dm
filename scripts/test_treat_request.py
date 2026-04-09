from lo17_dm.Pretraiteur import Pretraiteur  # adapte le nom du fichier si besoin


analyser = Pretraiteur("./outputs/lemmes_corpus.tsv")

tests = [
    "je veux des informtions s sur les orgnissasion de reshershe autur du plstic",
    "inaugration de lenemain",
    "donne moi une analyse",
    "Documents qui prlent de vande",
]

print("\n===== TESTS DE LA CLASSE ANALYSER =====\n")

for req in tests:
    print(f"Requete : {req}")
    resultat = analyser.treat_input(req, "./outputs/spacy_stems.tsv")
    print(f"Correction : {resultat}\n")

print("\n===== TESTS EN LIVE =====\n")

while True:
    txt = input("Entrer du text (quit pour quitter): ")
    if txt == "quit":
        break
    resultat = analyser.treat_input(txt, "./outputs/sub_table.tsv")
    print("Resultat: ", " ".join(resultat))
