import re

sentences = [
    "Afficher la liste des articles qui parlent des systèmes embarqués dans la rubrique Horizons Enseignement.",
    "Je voudrais les articles qui parlent d’airbus ou du projet Taxibot.",
    "Je voudrais les articles qui parlent du tennis.",
    "Je voudrais les articles traitant de la Lune.",
    "Quels sont les articles parus entre le 3 mars 2013 et le 4 mai 2013 évoquant les Etats-Unis ?",
    "Afficher les articles de la rubrique en direct des laboratoires.",
    "Je veux les articles de la rubrique Focus parlant d’innovation.",
    "Je cherche les recherches sur l’aéronotique.",
    "Quels sont les articles parlant de la Russie ou du Japon ?",
    "Je voudrais les articles de 2011 sur l’enseignement.",
    "Je voudrais les articles dont le titre contient le mot chimie.",
    "Je veux les articles de 2014 et de la rubrique Focus et parlant de la santé.",
    "Je souhaite les rubriques des articles parlant de nutrition ou de vins.",
    "Quels sont les articles sur la réalité virtelle ?",
    "Quels sont les articles traitant d’informatique ou de réseaux.",
    "je voudrais les articles de la rubrique Focus mentionnant un laboratoire.",
    "quels sont les articles publiés au mois de novembre 2011 portant sur de la recherche.",
    "je veux des articles sur la plasturige.",
    "je voudrais les articles liés à la recherche scientifique publiés en Février 2010.",
    "Donner les articles qui parlent d’apprentissage et de la rubrique Horizons Enseignement."
]

RE_CONTENU = r"(?:parl\w*(?:\s+(?:de|d['’]|du|des))?|trait\w*(?:\s+(?:de|d['’]|du|des))?|\bsur\b|\bà\s+propos\s+(?:de|d['’]|du|des)|[ée]voqu\w*|mentionn\w*|concern\w*|port\w*\s+sur|impliqu\w*|liés?\s+à(?:\s+la)?)"

for s in sentences:
    matches = list(re.finditer(RE_CONTENU, s, re.IGNORECASE))
    print(f"{s}")
    for m in matches:
        print(f"  -> {m.group()}")
