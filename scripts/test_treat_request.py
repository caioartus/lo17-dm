from lo17_dm.Analyser import Analyser  # adapte le nom du fichier si besoin


analyser = Analyser("./outputs/index_texte.tsv")

tests = [
    "je veux des informtions s sur les orgnissasion de reshershe autur du plstic",
    "inaugration de lenemain",
    "donne moi une analyse",
]

print("\n===== TESTS DE LA CLASSE ANALYSER =====\n")

for req in tests:
    print(f"Requete : {req}")
    resultat = analyser.treat_input(req, "./outputs/sub_table.tsv")
    print(f"Correction : {resultat}\n")
