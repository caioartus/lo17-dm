from pathlib import Path
import pandas as pd

class Correcteur:
    def __init__(self, lexique: list[str], seuil_min: int = 3, seuil_max: int = 4, seuil_prox: float = 0.6):
        self.lexique = lexique
        self.lemma_set = set(lexique)
        self.seuil_min = seuil_min
        self.seuil_max = seuil_max
        self.seuil_prox = seuil_prox

    def corrige(self, token: str) -> str | None:
        """
        Tente de corriger un token s'il n'est pas dans l'index.
        Si le token est déjà valide ou est un nombre, il est retourné tel quel.
        Sinon, on cherche le candidat le plus proche dans le lexique.
        """
        if self._in_index(token):
            return token
        
        if self._is_number(token):
            return token

        return self._treat_non_existant(token)

    def _in_index(self, token: str) -> bool:
        return token in self.lemma_set

    def _is_number(self, token: str) -> bool:
        try:
            float(token)
            return True
        except ValueError:
            return False

    def _treat_non_existant(self, mot: str) -> str | None:
        candidates = self._generate_candidates(mot)

        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0]

        return min(candidates, key=lambda terme: self._levenshtein(mot, terme))

    def _generate_candidates(self, mot: str) -> list[str]:
        candidates = []
        len_m = len(mot)

        for terme in self.lexique:
            len_t = len(terme)

            if len_m < self.seuil_min or len_t < self.seuil_min:
                continue

            if abs(len_m - len_t) > self.seuil_max:
                continue

            maxlen = max(len_m, len_t)
            ident = diff = 0

            for i in range(min(len_m, len_t)):
                if mot[i] == terme[i]:
                    ident += 1
                else:
                    diff += 1

                if (diff / maxlen) * 100 > 100 - self.seuil_prox:
                    break

            if (ident / maxlen) * 100 >= self.seuil_prox:
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
