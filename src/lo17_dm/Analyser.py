from lo17_dm.AntiDict import AntiDict
from lo17_dm.Tokenizer import CorpusTokenizer
from lo17_dm.Stemmer import Stemmer, SpacyStemmer
import re
from datetime import datetime
import pandas as pd
from pathlib import Path


class Analyser:
    def __init__(self, index_path: str | Path, stemmer: Stemmer = SpacyStemmer()):
        index_path = Path(index_path)

        if not index_path.exists():
            raise FileNotFoundError("Index file not found.")

        self.stemmer = stemmer
        self.requete: list[str] = []
        self.cleaned_tokens: list[str] = []
        self.index = pd.read_csv(index_path, sep="\t")["token"].tolist()
        self.index_set = set(self.index)

    def treat_input(self, text: str, sub_table_csv: str | Path) -> list[str]:
        # TODO - Do NOT treat stop words, just let them pass
        """Prend le texte brut et applique la tokenisation, la lemmatisation"""
        stemmed_text = self.stemmer.transform(text)
        stemmed_tokens = CorpusTokenizer.tokenize(stemmed_text)
        self.requete = stemmed_tokens

        # récupération de l'anti-dictionnaire
        antidict = AntiDict()
        antidict.build_from_file(sub_table_csv)

        cleaned_tokens = []
        for token in self.requete:
            if token in antidict.stopwords:
                continue
            # verifie dans l'ordre donc si c'est un nombre ou une date ou regarde pas dans l'index
            if self.is_date(token) or self.is_number(token) or self.in_index(token):
                cleaned_tokens.append(token)
                continue
            else:
                candidat = self.treat_non_existant(token, self.index, 3, 4, 0.6)
                if candidat is not None:
                    cleaned_tokens.append(candidat)
        self.cleaned_tokens = cleaned_tokens
        return self.cleaned_tokens

    def is_date(self, token: str) -> bool:
        """Check if a token represents a date (YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY, or a year)"""
        # Check common date formats
        date_patterns = [
            r"^\d{4}-\d{2}-\d{2}$",  # YYYY-MM-DD
            r"^\d{2}/\d{2}/\d{4}$",  # DD/MM/YYYY or MM/DD/YYYY
            r"^\d{1,2}/\d{1,2}/\d{4}$",  # Flexible day/month
        ]

        for pattern in date_patterns:
            if re.match(pattern, token):
                return True
        return False

    def is_number(self, token: str) -> bool:
        """Check if a token represents a number (integer or float)"""
        try:
            float(token)
            return True
        except ValueError:
            return False

    def in_index(self, token: str) -> bool:
        """Vérifie si un token présent dans l'index"""
        return token in self.index_set

    def generate_candidates(
        self, mot: str, lexique: list[str], seuilMin, seuilMax, seuilProx
    ) -> list[str]:
        candidats = []

        for terme in lexique:
            # Longueurs
            len_m = len(mot)
            len_t = len(terme)

            # (a) seuil minimal
            if len_m < seuilMin or len_t < seuilMin:
                continue

            # (b) difference de longueur
            if abs(len_m - len_t) > seuilMax:
                continue

            # (c) calcul du prefixe commun
            i = 0
            while i < min(len_m, len_t) and mot[i] == terme[i]:
                i += 1

            # score de proximite = (nb lettres communes / longueur max) * 100
            score = (i / max(len_m, len_t)) * 100

            if score >= seuilProx:
                candidats.append(terme)

        return candidats

    def levenshtein(self, a, b):
        # matrice (len(a)+1) x (len(b)+1)
        dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]

        # initialisation
        for i in range(len(a) + 1):
            dp[i][0] = i
        for j in range(len(b) + 1):
            dp[0][j] = j

        # remplissage
        for i in range(1, len(a) + 1):
            for j in range(1, len(b) + 1):
                cout_sub = 0 if a[i - 1] == b[j - 1] else 1
                dp[i][j] = min(
                    dp[i - 1][j] + 1,  # suppression
                    dp[i][j - 1] + 1,  # insertion
                    dp[i - 1][j - 1] + cout_sub,  # substitution
                )
        return dp[-1][-1]

    def treat_non_existant(
        self, mot: str, lexique: list[str], seuilMin, seuilMax, seuilProx
    ) -> str | None:
        """
        Traite un mot qui n'existe pas dans le lexique.
        1. Recherche par prefixe pour generer des candidats
        2. Si un seul candidat -> retour direct
        3. Si plusieurs -> departage par distance de Levenshtein
        4. Si aucun -> renvoie None
        """

        candidats = self.generate_candidates(
            mot, lexique, seuilMin, seuilMax, seuilProx
        )

        if len(candidats) == 0:
            return None

        if len(candidats) == 1:
            return candidats[0]  # on retourne le lemme

        # calcul de la distance pour chaque candidat
        best_terme = None
        best_dist = float("inf")

        for terme in candidats:
            d = self.levenshtein(mot, terme)
            if d < best_dist:
                best_dist = d
                best_terme = terme

        return best_terme


lexique_test = {
    "information": None,
    "indexation": None,
    "recherche": None,
    "document": None,
    "corpus": None,
    "analyse": None,
    "donnee": None,
    "donner": None,
    "machine": None,
    "apprentissage": None,
    "modele": None,
    "texte": None,
    "phrase": None,
    "mot": None,
    "erreur": None,
    "correcteur": None,
    "distance": None,
    "prefixe": None,
    "lemme": None,
}
