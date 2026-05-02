from lo17_dm.AntiDict import AntiDict
from lo17_dm.Stemmer import Stemmer, SpacyStemmer
import re
import pandas as pd
from pathlib import Path
from lo17_dm.DateExtractor import DateExtractor
from lo17_dm.KeyWordExtractor import KeyWordExtractor



class Pretraiteur:
    def __init__(
        self,
        lemma_table_path: str | Path,
        rubriques_index_path: str | Path,
        stop_words_path: str | Path,
        stemmer: Stemmer = SpacyStemmer(),
        date_extractor: DateExtractor = DateExtractor(),
        keyword_extractor: KeyWordExtractor
        | None = None, 
    ):
        lemma_table_path = Path(lemma_table_path)
        rubriques_index_path = Path(rubriques_index_path)
        stop_words_path = Path(stop_words_path)

        if not lemma_table_path.exists():
            raise FileNotFoundError("Lemma Table file not found.")
        if not rubriques_index_path.exists():
            raise FileNotFoundError("Rubriques Index file not found.")
        if not stop_words_path.exists():
            raise FileNotFoundError("Stop Words file not found.")

        self.rubriques = pd.read_csv(rubriques_index_path, sep="\t")["token"].to_list()
        self.stemmer = stemmer
        self.date_extractor = date_extractor
        self.keyword_extractor = keyword_extractor or KeyWordExtractor(
            lemma_table_path, stop_words_path, stemmer
        )

        self.requete_dict: dict = {}

    def treat_request(self, text: str) -> dict :
        """Effectue le traitement complet de la requete, renvoi le dictionnaire de la requete"""
        treated = self.extract_dates(text)
        print("after date extraction : ", treated)
        treated = self.extract_image(treated)
        print("after image extraction : ", treated)
        treated = self.extract_rubriques(treated)
        print("after rubriques extraction : ", treated)
        treated = self.extract_key_words(treated)
        return treated

    def extract_image(self, text) -> str:
        """Trouve si la requête demande une image ou pas.
        Détecte les patterns demandant explicitement avec/sans image,
        les retire du texte, et met à jour requete_dict.
        """
        # Pattern pour "sans image" (négation)
        sans_image_pattern = re.compile(
            r"\bsans\s+(?:des\s+)?(?:image|images)\b[.\s]*", re.IGNORECASE
        )

        # Pattern pour demandes d'image (avec/qui ont/contenant)
        avec_image_pattern = re.compile(
            r"\b(?:avec|qui\s+ont|contenant)\s+(?:des\s+|une\s+)?(?:image|images)\b[.\s]*",
            re.IGNORECASE,
        )

        treated_text = text

        # Vérifier "sans image" en premier (priorité si ambigu)
        if sans_image_pattern.search(treated_text):
            self.requete_dict["image"] = False
            treated_text = sans_image_pattern.sub("", treated_text).strip()
            return treated_text

        # Vérifier demandes positives d'image
        if avec_image_pattern.search(treated_text):
            self.requete_dict["image"] = True
            treated_text = avec_image_pattern.sub("", treated_text).strip()
            return treated_text

        # Aucun pattern trouvé
        self.requete_dict["image"] = None
        return treated_text

    def extract_rubriques(self, text):
        """Extrait les rubriques et renvoie le texte sans les rubriques"""
        self.requete_dict["rubrique"] = []
        if not re.search(r"\brubrique\b", text, flags=re.IGNORECASE):
            return text

        text_no_rubriques = text
        for rubrique in self.rubriques:
            rubrique = rubrique.strip()
            if not rubrique:
                continue

            pattern = r"\b" + re.escape(rubrique) + r"\b"
            text_no_rubriques, count = re.subn(
                pattern, "", text_no_rubriques, count=1, flags=re.IGNORECASE
            )

            if count > 0:
                self.requete_dict["rubrique"].append(rubrique)
                text_no_rubriques = re.sub(r"\s{2,}", " ", text_no_rubriques).strip()

        # Retirer le mot "rubrique" du texte
        text_no_rubriques = re.sub(
            r"\brubrique\b", "", text_no_rubriques, flags=re.IGNORECASE
        ).strip()
        return re.sub(r"\s{2,}", " ", text_no_rubriques).strip()

    def extract_dates(self, text):
        """Utilise DateExtractor pour extraire les dates et retourne le text sans les dates"""

        from_date, to_date, antidate, treated = self.date_extractor.extract(text)
        self.requete_dict["from_date"] = from_date
        self.requete_dict["to_date"] = to_date
        self.requete_dict["anti_date"] = antidate

        return treated

    def extract_key_words(self, text: str):
        """Delegates keyword extraction to KeyWordExtractor and stores results."""
        results = self.keyword_extractor.extract(text)
        self.requete_dict["titre"] = results["titre"]
        self.requete_dict["contenu"] = results["contenu"]
        self.requete_dict["exclude"] = results["exclude"]
        return self.requete_dict
