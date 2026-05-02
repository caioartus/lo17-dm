import re

s = "Quels sont les articles dont le titre évoque la recherche ?"

RE_TITRE = (
    r"(?:(?:dont\s+le\s+)?titre\s+contient(?:\s+les?\s+mots?|\s+le\s+terme)?|"
    r"(?:dont\s+le\s+)?titre\s+[ée]voque|"
    r"(?:dont\s+le\s+)?titre\s+poss[èe]de(?:\s+les?\s+mots?)?|"
    r"(?:qui\s+)?contiennent\s+les?\s+mots?|"
    r"(?:qui\s+)?contient\s+les?\s+mots?|"
    r"contenant\s+les?\s+mots?|"
    r"contenant\s+le\s+terme|"
    r"avec\s+le\s+mot|"
    r"possédant\s+le\s+mot)"
)
print("Regex TITRE:", RE_TITRE)

matches = list(re.finditer(RE_TITRE, s, re.IGNORECASE))
for m in matches:
    print("Match:", m.group())
