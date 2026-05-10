from lo17_dm.AntiDict import AntiDict
from lo17_dm.Stemmer import Stemmer, SpacyStemmer
from lo17_dm.Correcteur import Correcteur
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
    "écrire",
    "contenir",
    "paraitre",
    "parler",
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

RE_TITRE_POST = r"dans\s+le\s+titre"

RE_CONTENU = (
    r"(?:parlent|"
    r"parle|"
    r"parlant|"
    r"traitant|"
    r"traitent|"
    r"sur|"
    r"[ée]voquant|"
    r"mentionnant|"
    r"citant|"
    r"contenant|"
    r"mentionnent|"
    r"impliquant|"
    r"impliquent|"
    r"concernent|"
    r"[ée]voquent|"
    r"possédant)"
)
RE_CONTENU_POST = r"(?:est-il\s+cité|être\s+cité)"

RE_NEGATION = r"\b(?:pas\s+de|sans|non\s+pas|pas\b)"
RE_OR = (
    r"\bou\b|"
    r"\bsoit\s+de"
    r"\bsoit\s+des"
    r"\bsoit\s+du"
    r"\bsoit\s+de"
)
RE_AND = r"\bet\b"

# retire articles parasites devant le vrai mot
RE_PREFIX_CLEAN = r"^(?:de|du|des|d|la|le|les|l|un|une)\s+"


class KeyWordExtractor:
    def __init__(
        self,
        stopwords_file: str | Path,
        correcteur: Correcteur,
        stemmer: Stemmer = SpacyStemmer(),
<<<<<<< Updated upstream
    ):
        self.stopwords_file = Path(stopwords_file)
        self.correcteur = correcteur
        self.antidict = AntiDict()

        with open(self.stopwords_file, "r", encoding="utf-8") as f:
            corpus_stopwords = set(f.read().splitlines())
        self.antidict.add_manual_stopwords(corpus_stopwords | set(REQUETE_STOPWORDS))

=======
    ):        
        f_stopwords = Path(stopwords_file) if isinstance(stopwords_file, str) else stopwords_file
        with open(f_stopwords, "r", encoding="utf-8") as f:
            corpus_stopwords = set(f.read().splitlines())
        self.stopwords = corpus_stopwords
        
        self.correcteur = correcteur
>>>>>>> Stashed changes
        self.stemmer = stemmer

    def extract(self, text: str) -> dict:
        text = text.lower()
        results = {"titre": [], "contenu": [], "exclude": []}

        # -----------------------------
        # EXCLUSIONS (on traite ca d'abord comme ça pas de confusion avec titre/contenu)
        # -----------------------------
        def handle_exclude(m):
            block = m.group(1).strip()
            clean = self.normalize_terms(block)
            if clean:
                results["exclude"].extend(clean)
            return " " * len(m.group(0))

        text = re.sub(
            rf"{RE_NEGATION}\s+(.+?)(?=(?:{RE_TITRE}|{RE_CONTENU}|$))",
            handle_exclude,
            text,
            flags=re.IGNORECASE,
        )

        # -----------------------------
        # TITRE : plusieurs occurrences possibles
        # -----------------------------
        def handle_titre(m):
            block = m.group(1).strip()
            results["titre"].extend(self._parse_logic_block(block))
            return " " * len(m.group(0))

        text = re.sub(
            rf"{RE_TITRE}\s+(.+?)(?=(?:{RE_TITRE}|{RE_CONTENU}|{RE_NEGATION}|$))",
            handle_titre,
            text,
            flags=re.IGNORECASE,
        )

        # -----------------------------
        # TITRE POST : "contenant ... dans le titre"
        # -----------------------------
        text = re.sub(
            rf"(?:contenant|contient)\s+(.+?)\s+{RE_TITRE_POST}",
            handle_titre,
            text,
            flags=re.IGNORECASE,
        )

        # -----------------------------
        # CONTENU : plusieurs occurrences possibles
        # -----------------------------
        def handle_contenu(m):
            block = m.group(1).strip()
            results["contenu"].extend(self._parse_logic_block(block))
            return " " * len(m.group(0))

        text = re.sub(
            rf"{RE_CONTENU}\s+(.+?)(?=(?:{RE_TITRE}|{RE_CONTENU}|{RE_NEGATION}|$))",
            handle_contenu,
            text,
            flags=re.IGNORECASE,
        )

        # ------------
        # CONTENU POST : "ou ... est cité."
        # ------------
        def handle_contenu_post(m):
            block = m.group(0).strip()
            results["contenu"].extend(self._parse_logic_block(block))
            return " " * len(m.group(0))

        text = re.sub(
            rf"(.+?)(?={RE_CONTENU_POST})",
            handle_contenu_post,
            text,
            flags=re.IGNORECASE,
        )
        return results

    # =========================================================
    # LOGIC PARSING
    # =========================================================

    def _parse_logic_block(self, text: str) -> list[list[str]]:
        groups = []

        # split sur OU
        for or_part in re.split(RE_OR, text):
            and_group = []

            # split sur ET
            for term in re.split(RE_AND, or_part):
                term = re.sub(RE_PREFIX_CLEAN, "", term.strip())

                clean = self.normalize_terms(term)
                if clean:
                    and_group.extend(clean)

            if and_group:
                groups.append(and_group)

        return groups

    def normalize_terms(self, text: str) -> list[str]:
        """
        nettoyage + stemming + correction fautes
        """

        tokens = self.stemmer.transform_tolist(text)
        cleaned = []

        for token in tokens:
            if token in self.antidict.stopwords:
                continue

            candidate = self.correcteur.corrige(token)
            if candidate:
                cleaned.append(candidate)

        return cleaned
