import re
import calendar


class DateExtractor:
    def __init__(self):
        self.month_names = {
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
        self.from_date = None
        self.to_date = None

    def normalize_date(self, day: int | str, month: int | str, year: int | str) -> str:
        """Formate une date en dd/mm/yyyy."""
        return f"{int(day):02d}/{int(month):02d}/{int(year):04d}"

    def month_bounds(self, month_name: str, year: str) -> tuple[str, str]:
        """Retourne le premier et le dernier jour du mois donné."""
        month = self.month_names[month_name.lower()]
        last_day = calendar.monthrange(int(year), month)[1]
        return self.normalize_date(1, month, year), self.normalize_date(
            last_day, month, year
        )

    def year_bounds(self, year: str) -> tuple[str, str]:
        """Retourne les bornes de l'année entière."""
        return self.normalize_date(1, 1, year), self.normalize_date(31, 12, year)

    def compare_dates(self, a: str, b: str) -> int:
        """Compare deux dates normalisées et renvoie -1, 0 ou 1."""
        day_a, month_a, year_a = map(int, a.split("/"))
        day_b, month_b, year_b = map(int, b.split("/"))
        return (
            (year_a, month_a, day_a) < (year_b, month_b, day_b)
            and -1
            or ((year_a, month_a, day_a) > (year_b, month_b, day_b) and 1 or 0)
        )

    def update_bounds(self, start: str | None, end: str | None) -> None:
        """Met à jour les bornes min/max trouvées dans la requête."""
        if start is not None:
            if self.from_date is None or self.compare_dates(start, self.from_date) < 0:
                self.from_date = start
        if end is not None:
            if self.to_date is None or self.compare_dates(end, self.to_date) > 0:
                self.to_date = end

    def parse_date_fragment(self, fragment: str) -> tuple[str, str] | None:
        """Analyse un segment de texte pour en extraire une date ou une plage de dates."""
        fragment = fragment.strip().lower()

        match = re.search(
            r"(?P<day>\d{1,2})[ /-](?P<month>\d{1,2})[ /-](?P<year>\d{4})", fragment
        )
        if match:
            return self.normalize_date(
                match["day"], match["month"], match["year"]
            ), self.normalize_date(match["day"], match["month"], match["year"])

        match = re.search(
            r"(?P<day>\d{1,2})\s+(?P<month_name>janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)\s+(?P<year>\d{4})",
            fragment,
        )
        if match:
            return self.normalize_date(
                match["day"], self.month_names[match["month_name"]], match["year"]
            ), self.normalize_date(
                match["day"], self.month_names[match["month_name"]], match["year"]
            )

        match = re.search(
            r"(?P<month_name>janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)\s+(?P<year>\d{4})",
            fragment,
        )
        if match:
            return self.month_bounds(match["month_name"], match["year"])

        match = re.search(r"\b(?P<year>20\d{2})\b", fragment)
        if match:
            return self.year_bounds(match["year"])

        return None

    def extract(self, text: str) -> tuple[str | None, str | None, str]:
        """Extrait les dates d'une requête et retourne from_date, to_date, text_no_date."""
        self.from_date = None
        self.to_date = None
        text_no_date = text

        range_pattern = re.compile(
            r"\bentre\s+(?:le\s+)?(?P<start>[^.?,;]+?)\s+et\s+(?:le\s+)?(?P<end>[^.?,;]+?)(?=[.?,;]|$)",
            re.IGNORECASE,
        )
        match = range_pattern.search(text_no_date)
        if match:
            parsed_start = self.parse_date_fragment(match.group("start"))
            parsed_end = self.parse_date_fragment(match.group("end"))
            if parsed_start and parsed_end:
                self.update_bounds(parsed_start[0], parsed_end[1])
            text_no_date = range_pattern.sub("", text_no_date)

        from_pattern = re.compile(
            r"\b(?:à\s+partir\s+de|à\s+partir\s+du|à\s+partir|après|publiés\s+après|publié\s+après)\s+(?:le\s+)?(?P<date>[^.?,;]+?)(?=[.?,;]|$)",
            re.IGNORECASE,
        )
        match = from_pattern.search(text_no_date)
        if match:
            parsed = self.parse_date_fragment(match.group("date"))
            if parsed:
                self.update_bounds(parsed[0], None)
            text_no_date = from_pattern.sub("", text_no_date)

        to_pattern = re.compile(
            r"\b(?:avant|avant\s+le|jusqu'\s+au|jusqu'\s+à|jusqu'\s+au\s+)(?:le\s+)?(?P<date>[^.?,;]+?)(?=[.?,;]|$)",
            re.IGNORECASE,
        )
        match = to_pattern.search(text_no_date)
        if match:
            parsed = self.parse_date_fragment(match.group("date"))
            if parsed:
                self.update_bounds(None, parsed[1])
            text_no_date = to_pattern.sub("", text_no_date)

        exact_date_pattern = re.compile(
            r"\b(?:le\s+|du\s+|de\s+|en\s+)?(?P<day>\d{1,2})[ /-](?P<month>\d{1,2})[ /-](?P<year>\d{4})\b",
            re.IGNORECASE,
        )
        match = exact_date_pattern.search(text_no_date)
        if match:
            exact = self.normalize_date(
                match.group("day"), match.group("month"), match.group("year")
            )
            self.update_bounds(exact, exact)
            text_no_date = exact_date_pattern.sub("", text_no_date)

        word_date_pattern = re.compile(
            r"\b(?:le\s+|du\s+|de\s+|en\s+)?(?P<day>\d{1,2})\s+(?P<month_name>janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)\s+(?P<year>\d{4})\b",
            re.IGNORECASE,
        )
        match = word_date_pattern.search(text_no_date)
        if match:
            exact = self.normalize_date(
                match.group("day"),
                self.month_names[match.group("month_name").lower()],
                match.group("year"),
            )
            self.update_bounds(exact, exact)
            text_no_date = word_date_pattern.sub("", text_no_date)

        month_year_pattern = re.compile(
            r"\b(?:en\s+|au\s+mois\s+de\s+|mois\s+de\s+|du\s+|de\s+)?(?P<month>janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)\s+(?P<year>20\d{2})\b",
            re.IGNORECASE,
        )
        match = month_year_pattern.search(text_no_date)
        if match:
            parsed = self.month_bounds(match.group("month"), match.group("year"))
            self.update_bounds(parsed[0], parsed[1])
            text_no_date = month_year_pattern.sub("", text_no_date)

        year_pattern = re.compile(
            r"\b(?:en\s+|de\s+l'année\s+|de\s+)?(?P<year>20\d{2})\b", re.IGNORECASE
        )
        match = year_pattern.search(text_no_date)
        if match:
            parsed = self.year_bounds(match.group("year"))
            self.update_bounds(parsed[0], parsed[1])
            text_no_date = year_pattern.sub("", text_no_date)

        text_no_date = re.sub(r"\s{2,}", " ", text_no_date)
        text_no_date = re.sub(r"\s+([?.!,;])", r"\1", text_no_date)
        text_no_date = re.sub(
            r"\b(?:de|du|des|en|le|la|l')\b(?=\s*(?:et|ou|mais|,|\.|\?|!|$))",
            "",
            text_no_date,
            flags=re.IGNORECASE,
        )
        text_no_date = re.sub(r"\s{2,}", " ", text_no_date).strip()

        return self.from_date, self.to_date, text_no_date
