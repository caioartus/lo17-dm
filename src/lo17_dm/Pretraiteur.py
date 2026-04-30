from lo17_dm.AntiDict import AntiDict
from lo17_dm.Stemmer import Stemmer, SpacyStemmer
import re
import pandas as pd
from pathlib import Path
from lo17_dm.DateExtractor import DateExtractor


class Pretraiteur:
    def __init__(
        self,
        lemma_table_path: str | Path,
        rubriques_index_path: str | Path,
        stemmer: Stemmer = SpacyStemmer(),
        date_extractor: DateExtractor = DateExtractor(),
    ):
        lemma_table_path = Path(lemma_table_path)
        rubriques_index_path = Path(rubriques_index_path)

        if not lemma_table_path.exists():
            raise FileNotFoundError("Lemma Table file not found.")

        self.lemmas = pd.read_csv(lemma_table_path, sep="\t")["lemma"].tolist()
        self.lemma_set = set(self.lemmas)

        if not rubriques_index_path.exists():
            raise FileNotFoundError("Rubriques Index file not found.")

        self.rubriques = pd.read_csv(rubriques_index_path, sep="\t")["token"].to_list()

        self.stemmer = stemmer
        self.date_extractor = date_extractor
        self.requete: list[str] = []
        self.cleaned_tokens: list[str] = []

        self.requete_dict: dict = {}

    def treat_request(self, text: str, sub_table_csv: str | Path):
        """Effectue le traitement complet de la requete, renvoi le dictionnaire de la requete"""
        pass

    def extract_image(self, text) -> str:
        """Trouve si la requete demande une image ou pas"""
        # trouve les patterns dans le text
        # determine
        return treated_text

    def extract_rubriques(self, text):
        """Extrait les rubriques et renvoi le text sans les rubriques"""
        text_no_rubriques = text
        self.requete_dict["rubriques"] = None

        for rubrique in self.rubriques:
            if not rubrique or not rubrique.strip():
                continue

            pattern = r"\b" + re.escape(rubrique.strip()) + r"\b"

            # on check si une des rubriques est dans la requete avec un regex
            if re.search(pattern, text_no_rubriques, flags=re.IGNORECASE):
                text_no_rubriques = re.sub(
                    pattern,
                    "",
                    text_no_rubriques,
                    count=1,
                    flags=re.IGNORECASE,
                )
                text_no_rubriques = re.sub(
                    r"\s{2,}", " ", text_no_rubriques
                ).strip()  # nettoyage leger pour enlever les doubles espaces etc.
                self.requete_dict["rubriques"] = rubrique
                return text_no_rubriques

        return text_no_rubriques

    def extract_dates(self, text):
        """Utilise DateExtractor pour extraire les dates et retourne le text sans les dates"""

        from_date, to_date, treated = self.date_extractor.extract(text)
        self.requete_dict["from_date"] = from_date
        self.requete_dict["to_date"] = to_date
        return treated

    def extract_key_words(self, text: str, sub_table_csv: str | Path) -> list[str]:
        """Prend le texte brut et applique la tokenisation, la lemmatisation et renvoi les mots cles qui match"""

        stemmed_tokens = self.stemmer.transform_tolist(text)
        print(stemmed_tokens)
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
                candidat = self.treat_non_existant(token, self.lemmas, 3, 4, 0.6)
                if candidat is not None:
                    cleaned_tokens.append(candidat)
        self.cleaned_tokens = cleaned_tokens

        self.requete_dict["key_words"] = cleaned_tokens
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
        return token in self.lemma_set

    def generate_candidates(
        self, mot: str, lexique: list[str], seuilMin, seuilMax, seuilProx
    ) -> list[str]:
        candidats = []
        for terme in lexique:
            # Longueurs
            len_m = len(mot)
            len_t = len(terme)

            # seuil minimal
            if len_m < seuilMin or len_t < seuilMin:
                continue

            # difference de longueur
            if abs(len_m - len_t) > seuilMax:
                continue

            # calcul du prefixe commun
            i = 0
            ident = 0
            diff = 0
            maxlen = max(len_m, len_t)
            for i in range(min(len_m, len_t)):
                if mot[i] == terme[i]:
                    ident += 1
                else:
                    diff += 1

                perreur = (diff / maxlen) * 100

                if perreur > 100 - seuilProx:
                    break

            # score de proximite = (nb lettres communes / longueur max) * 100
            score = (ident / maxlen) * 100

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
