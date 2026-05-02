from lo17_dm.AntiDict import AntiDict
from lo17_dm.Stemmer import Stemmer, SpacyStemmer
from pathlib import Path
import pandas as pd
import re


REQUETE_STOPWORDS = [
    # pronoms / sujets inutiles
    "je",
    "j",
    "nous",
    "on",
    "moi",
    "me",
    "mon",
    "ma",
    "mes",
    # verbes de demande très fréquents
    "veux",
    "veut",
    "voulons",
    "voudrais",
    "voudrions",
    "souhaite",
    "souhaites",
    "souhaitons",
    "cherche",
    "cherchez",
    "recherche",
    "rechercher",
    "trouver",
    "trouve",
    "donner",
    "donnez",
    "afficher",
    "affiche",
    "lister",
    "liste",
    "retourner",
    "retournez",
    "obtenir",
    # mots de structure de requête
    "articles",
    "article",
    "liste",
    "tous",
    "tout",
    "des",
    "les",
    "du",
    "de",
    "d",
    "la",
    "le",
    "un",
    "une",
    "au",
    "aux",
    "dans",
    "sur",
    "avec",
    "dont",
    "qui",
    "que",
    "quoi",
    "quels",
    "quelles",
    "quel",
    "quelle",
    # mots parasites fréquents
    "mot",
    "terme",
    "rubrique",
    "rubriques",
    "titre",
    "contenu",
    "parlant",
    "parle",
    "parlent",
    "traitant",
    "traitent",
    "évoquant",
    "évoque",
    "évoquent",
    "mentionnant",
    "mentionne",
    "mentionnent",
    # connecteurs qu’on gère séparément
    "et",
    "ou",
    "mais",
    "pas",
    "non",
    "sans",
    # garder vide si stemming bizarre
    "",
]

# =========================================================
# REGEX PATTERNS
# =========================================================

RE_TITRE = (
    r"(?:titre\s+contient(?:\s+le\s+mot)?|"
    r"titre\s+évoque|"
    r"titre\s+poss[èe]de\s+le\s+mot)"
)

RE_CONTENU = (
    r"(?:parlent?\s+de|"
    r"parle\s+de|"
    r"traitant\s+de|"
    r"traitent\s+de|"
    r"sur|"
    r"[ée]voquant|"
    r"mentionnant|"
    r"concernent|"
    r"[ée]voquent)"
)

RE_NEGATION = r"\b(?:pas\s+de|sans|non\s+pas)\b"
RE_OR = r"\bou\b"
RE_AND = r"\bet\b"

# retire articles parasites devant le vrai mot
RE_PREFIX_CLEAN = r"^(?:de|du|des|d|la|le|les|l|un|une)\s+"


class KeyWordExtractor:
    def __init__(self, lemma_table_path: str | Path, stemmer: Stemmer = SpacyStemmer()):
        lemma_table_path = Path(lemma_table_path)

        if not lemma_table_path.exists():
            raise FileNotFoundError("Lemma Table file not found.")

        self.lemmas = pd.read_csv(lemma_table_path, sep="\t")["token"].tolist()
        self.lemma_set = set(self.lemmas)
        self.stemmer = stemmer

    def extract(self, text: str, sub_table_csv: str | Path) -> dict:
        text = text.lower()

        antidict = AntiDict()
        antidict.build_from_file(sub_table_csv)

        results = {"titre": [], "contenu": [], "exclude": []}

        # -----------------------------
        # TITRE : plusieurs occurrences possibles
        # ex:
        # "titre contient X ou le contenu parle de Y"
        # -----------------------------
        for match in re.finditer(
            rf"{RE_TITRE}\s+(.+?)(?=(?:{RE_TITRE}|{RE_CONTENU}|{RE_NEGATION}|$))",
            text,
            re.IGNORECASE,
        ):
            block = match.group(1).strip()
            results["titre"].extend(self._parse_logic_block(block, antidict))

        # -----------------------------
        # CONTENU : plusieurs occurrences possibles
        # ex:
        # "parlent de X ou des Y"
        # -----------------------------
        for match in re.finditer(
            rf"{RE_CONTENU}\s+(.+?)(?=(?:{RE_TITRE}|{RE_CONTENU}|{RE_NEGATION}|$))",
            text,
            re.IGNORECASE,
        ):
            block = match.group(1).strip()
            results["contenu"].extend(self._parse_logic_block(block, antidict))

        # -----------------------------
        # EXCLUSIONS
        # -----------------------------
        for ex in re.findall(
            rf"{RE_NEGATION}\s+(.+?)(?=(?:{RE_TITRE}|{RE_CONTENU}|$))",
            text,
            re.IGNORECASE,
        ):
            clean = self._normalize_term(ex.strip(), antidict)
            if clean:
                results["exclude"].append(clean)

        return results

    # =========================================================
    # LOGIC PARSING
    # =========================================================

    def _parse_logic_block(self, text: str, antidict: AntiDict) -> list[list[str]]:
        groups = []

        # split sur OU
        for or_part in re.split(RE_OR, text):
            and_group = []

            # split sur ET
            for term in re.split(RE_AND, or_part):
                term = re.sub(RE_PREFIX_CLEAN, "", term.strip())

                clean = self._normalize_term(term, antidict)
                if clean:
                    and_group.append(clean)

            if and_group:
                groups.append(and_group)

        return groups

    def _normalize_term(self, term: str, antidict: AntiDict) -> str | None:
        """
        nettoyage + stemming + correction fautes
        """

        tokens = self.stemmer.transform_tolist(term)

        cleaned = []

        for token in tokens:
            if token in antidict.stopwords or token in REQUETE_STOPWORDS:
                continue

            if self._is_number(token):
                continue

            if self._in_index(token):
                cleaned.append(token)
            else:
                candidate = self._treat_non_existant(token, self.lemmas, 3, 4, 0.6)
                if candidate:
                    cleaned.append(candidate)

        if not cleaned:
            return None

        return " ".join(cleaned)

    # =========================================================
    # HELPERS
    # =========================================================

    def _in_index(self, token: str) -> bool:
        return token in self.lemma_set

    def _is_number(self, token: str) -> bool:
        try:
            float(token)
            return True
        except ValueError:
            return False

    def _treat_non_existant(
        self,
        mot: str,
        lexique: list[str],
        seuilMin: int,
        seuilMax: int,
        seuilProx: float,
    ) -> str | None:
        candidates = self._generate_candidates(
            mot,
            lexique,
            seuilMin,
            seuilMax,
            seuilProx,
        )

        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0]

        return min(candidates, key=lambda terme: self._levenshtein(mot, terme))

    def _generate_candidates(
        self,
        mot: str,
        lexique: list[str],
        seuilMin: int,
        seuilMax: int,
        seuilProx: float,
    ) -> list[str]:
        candidates = []
        len_m = len(mot)

        for terme in lexique:
            len_t = len(terme)

            if len_m < seuilMin or len_t < seuilMin:
                continue

            if abs(len_m - len_t) > seuilMax:
                continue

            maxlen = max(len_m, len_t)
            ident = diff = 0

            for i in range(min(len_m, len_t)):
                if mot[i] == terme[i]:
                    ident += 1
                else:
                    diff += 1

                if (diff / maxlen) * 100 > 100 - seuilProx:
                    break

            if (ident / maxlen) * 100 >= seuilProx:
                candidates.append(terme)

        return candidates

    def _levenshtein(self, a: str, b: str) -> int:
        dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]

        for i in range(len(a) + 1):
            dp[i][0] = i

        for j in range(len(b) + 1):
            dp[0][j] = j

        for i in range(1, len(a) + 1):
            for j in range(1, len(b) + 1):
                cost = 0 if a[i - 1] == b[j - 1] else 1

                dp[i][j] = min(
                    dp[i - 1][j] + 1,
                    dp[i][j - 1] + 1,
                    dp[i - 1][j - 1] + cost,
                )

        return dp[-1][-1]
