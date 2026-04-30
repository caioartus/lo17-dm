import re
import calendar

# ---------------------------------------------------------------------------
# Noms de mois français -> numéro
# ---------------------------------------------------------------------------

MONTH_NAMES: dict[str, int] = {
    "janvier": 1,
    "février": 2,
    "fevrier": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "aout": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
    "decembre": 12,
}

# Groupe de capture réutilisable pour les noms de mois
_MONTHS = "|".join(MONTH_NAMES)

# ---------------------------------------------------------------------------
# Patterns de reconnaissance de dates positives
# ---------------------------------------------------------------------------

# "entre le <date> et le <date>"
RE_RANGE = re.compile(
    r"\bentre\s+(?:le\s+)?(?P<start>[^.?,;]+?)\s+et\s+(?:le\s+)?(?P<end>[^.?,;]+?)(?=[.?,;]|$)",
    re.IGNORECASE,
)

# "à partir de / après / publié(s) après <date>"
RE_FROM = re.compile(
    r"\b(?:à\s+partir\s+de|à\s+partir\s+du|à\s+partir|après|publiés?\s+après)\s+(?:le\s+)?(?P<date>[^.?,;]+?)(?=[.?,;]|$)",
    re.IGNORECASE,
)

# "avant / jusqu'au / jusqu'à <date>"
RE_TO = re.compile(
    r"\b(?:avant(?:\s+le)?|jusqu'\s*(?:au|à)(?:\s+le)?)\s+(?P<date>[^.?,;]+?)(?=[.?,;]|$)",
    re.IGNORECASE,
)

# Date numérique : "12/03/2024" ou "12-03-2024"
RE_DATE_NUMERIC = re.compile(
    r"\b(?:le\s+|du\s+|de\s+|en\s+)?(?P<day>\d{1,2})[/\- ](?P<month>\d{1,2})[/\- ](?P<year>\d{4})\b",
    re.IGNORECASE,
)

# Date littérale : "12 mars 2024"
RE_DATE_LITERAL = re.compile(
    rf"\b(?:le\s+|du\s+|de\s+|en\s+)?(?P<day>\d{{1,2}})\s+(?P<month>{_MONTHS})\s+(?P<year>\d{{4}})\b",
    re.IGNORECASE,
)

# Mois + année : "mars 2024", "en mars 2024", "au mois de mars 2024"
RE_MONTH_YEAR = re.compile(
    rf"\b(?:en\s+|au\s+mois\s+de\s+|mois\s+de\s+|du\s+|de\s+)?(?P<month>{_MONTHS})\s+(?P<year>20\d{{2}})\b",
    re.IGNORECASE,
)

# Année seule : "2024", "en 2024", "de l'année 2024"
RE_YEAR = re.compile(
    r"\b(?:en\s+|de\s+l'année\s+|de\s+)?(?P<year>20\d{2})\b",
    re.IGNORECASE,
)

# Mois seul sans année : "juin", "au mois de juin"
RE_MONTH_ONLY = re.compile(
    rf"\b(?:au\s+mois\s+de\s+|mois\s+de\s+|en\s+)?(?P<month>{_MONTHS})\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Patterns de négation de dates
# Formes reconnues : "pas en juin", "pas au mois de juin 2024", "sauf le 12 mars",
#                    "excepté en 2024", "hormis janvier 2023", etc.
# ---------------------------------------------------------------------------

_NEGATION_PREFIX = (
    r"(?:pas\s+(?:au\s+mois\s+de\s+|en\s+|le\s+|du\s+)?"
    r"|sauf\s+(?:au\s+mois\s+de\s+|en\s+|le\s+|du\s+)?"
    r"|excepté\s+(?:en\s+|le\s+|au\s+mois\s+de\s+)?"
    r"|hormis\s+(?:en\s+|le\s+|au\s+mois\s+de\s+)?)"
)

RE_ANTI = re.compile(
    rf"\b{_NEGATION_PREFIX}(?P<date>[^.?,;]+?)(?=[.?,;]|$)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Nettoyage cosmétique du texte après suppression des dates
# ---------------------------------------------------------------------------

RE_CLEANUP = [
    (re.compile(r"\s{2,}"), " "),
    (re.compile(r"\s+([?.!,;])"), r"\1"),
    (
        re.compile(  # prépositions orphelines en fin de groupe
            r"\b(?:de|du|des|en|le|la|l')\b(?=\s*(?:et|ou|mais|,|\.|\?|!|$))",
            re.IGNORECASE,
        ),
        "",
    ),
    (re.compile(r"\s{2,}"), " "),
]


# ---------------------------------------------------------------------------


class DateExtractor:
    def __init__(self):
        self.from_date: str | None = None
        self.to_date: str | None = None
        self.anti_date: str | None = None

    # Formatage ------------------------------------------------------------------

    @staticmethod
    def _fmt(day, month, year) -> str:
        """Formate trois composantes en dd/mm/yyyy."""
        return f"{int(day):02d}/{int(month):02d}/{int(year):04d}"

    @staticmethod
    def _fmt_wildcard(day, month, year) -> str:
        """Formate trois composantes en dd/mm/yyyy avec '*' pour les champs absents."""
        d = f"{int(day):02d}" if day is not None else "*"
        m = f"{int(month):02d}" if month is not None else "*"
        y = f"{int(year):04d}" if year is not None else "*"
        return f"{d}/{m}/{y}"

    def _month_bounds(self, month_name: str, year: str) -> tuple[str, str]:
        """Premier et dernier jour du mois."""
        month = MONTH_NAMES[month_name.lower()]
        last_day = calendar.monthrange(int(year), month)[1]
        return self._fmt(1, month, year), self._fmt(last_day, month, year)

    def _year_bounds(self, year: str) -> tuple[str, str]:
        """Premier et dernier jour de l'année."""
        return self._fmt(1, 1, year), self._fmt(31, 12, year)

    # Comparaison et mise à jour des bornes -------------------------------------

    @staticmethod
    def _as_tuple(date: str) -> tuple[int, int, int]:
        d, m, y = date.split("/")
        return int(y), int(m), int(d)

    def _update_bounds(self, start: str | None, end: str | None) -> None:
        """Élargit la plage courante pour englober [start, end]."""
        if start and (
            self.from_date is None
            or self._as_tuple(start) < self._as_tuple(self.from_date)
        ):
            self.from_date = start
        if end and (
            self.to_date is None or self._as_tuple(end) > self._as_tuple(self.to_date)
        ):
            self.to_date = end

    # Analyse d'un fragment de texte --------------------------------------------

    def _parse_fragment(self, fragment: str) -> tuple[str, str] | None:
        """Tente d'extraire une date ou plage depuis un court segment de texte.
        Retourne (start, end) au format dd/mm/yyyy, ou None si rien trouvé."""
        fragment = fragment.strip().lower()

        m = RE_DATE_NUMERIC.search(fragment)
        if m:
            exact = self._fmt(m["day"], m["month"], m["year"])
            return exact, exact

        m = RE_DATE_LITERAL.search(fragment)
        if m:
            exact = self._fmt(m["day"], MONTH_NAMES[m["month"]], m["year"])
            return exact, exact

        m = RE_MONTH_YEAR.search(fragment)
        if m:
            return self._month_bounds(m["month"], m["year"])

        m = RE_YEAR.search(fragment)
        if m:
            return self._year_bounds(m["year"])

        return None

    def _parse_anti_fragment(self, fragment: str) -> str | None:
        """Tente d'extraire une date depuis un fragment de négation.
        Retourne une chaîne au format dd/mm/yyyy avec '*' pour les champs absents."""
        fragment = fragment.strip().lower()

        m = RE_DATE_NUMERIC.search(fragment)
        if m:
            return self._fmt_wildcard(m["day"], m["month"], m["year"])

        m = RE_DATE_LITERAL.search(fragment)
        if m:
            return self._fmt_wildcard(m["day"], MONTH_NAMES[m["month"]], m["year"])

        m = RE_MONTH_YEAR.search(fragment)
        if m:
            return self._fmt_wildcard(None, MONTH_NAMES[m["month"].lower()], m["year"])

        m = RE_YEAR.search(fragment)
        if m:
            return self._fmt_wildcard(None, None, m["year"])

        # Mois seul, sans année : "pas en juin"
        m = RE_MONTH_ONLY.search(fragment)
        if m:
            return self._fmt_wildcard(None, MONTH_NAMES[m["month"].lower()], None)

        return None

    # Extraction principale -----------------------------------------------------

    def _apply(self, pattern: re.Pattern, text: str, handler) -> str:
        """Applique un pattern, appelle handler(match) pour mettre à jour les bornes,
        puis supprime la correspondance du texte."""
        m = pattern.search(text)
        if m:
            handler(m)
            text = pattern.sub("", text, count=1)
        return text

    def extract(self, text: str) -> tuple[str | None, str | None, str | None, str]:
        """Extrait les dates d'une requête.
        Retourne (from_date, to_date, anti_date, texte_sans_dates)."""
        self.from_date = self.to_date = self.anti_date = None

        def handle_range(m):
            start = self._parse_fragment(m.group("start"))
            end = self._parse_fragment(m.group("end"))
            if start and end:
                self._update_bounds(start[0], end[1])

        def handle_from(m):
            parsed = self._parse_fragment(m.group("date"))
            if parsed:
                self._update_bounds(parsed[0], None)

        def handle_to(m):
            parsed = self._parse_fragment(m.group("date"))
            if parsed:
                self._update_bounds(None, parsed[1])

        def handle_date(m):
            parsed = self._parse_fragment(m.group(0))
            if parsed:
                self._update_bounds(*parsed)

        def handle_anti(m):
            parsed = self._parse_anti_fragment(m.group("date"))
            if parsed:
                self.anti_date = parsed

        # Les négations sont traitées en premier pour ne pas interférer avec
        # les autres patterns qui pourraient capturer les mêmes fragments.
        text = self._apply(RE_ANTI, text, handle_anti)
        text = self._apply(RE_RANGE, text, handle_range)
        text = self._apply(RE_FROM, text, handle_from)
        text = self._apply(RE_TO, text, handle_to)
        text = self._apply(RE_DATE_NUMERIC, text, handle_date)
        text = self._apply(RE_DATE_LITERAL, text, handle_date)
        text = self._apply(RE_MONTH_YEAR, text, handle_date)
        text = self._apply(RE_YEAR, text, handle_date)

        for pattern, repl in RE_CLEANUP:
            text = pattern.sub(repl, text)

        return self.from_date, self.to_date, self.anti_date, text.strip()
