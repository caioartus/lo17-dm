# search function 
# takes in indexes, request
# finds relevant documents
# returns the relevant document ids 

# docs form ids function 
# takes in doc ids and corpus
# returns relevant documents as formatted string 
from pathlib import Path
import pandas as pd
from datetime import datetime

class SearchEngine : 
    def __init__(self, output_dir: str | Path, corpus_path: str | Path):
        self.output_dir: Path = Path(output_dir)
        self.indexes: dict[str, dict[str, set[int]]] = {}
        self._load_indexes()
        self._load_corpus(Path(corpus_path))

    def _load_indexes(self) -> None:
        for name in ("titre", "texte", "rubrique", "bulletin", "date", "auteur", "contact", "image"):
            path = self.output_dir / "index" / f"index_{name}.tsv"
            if not path.exists():
                continue
            df = pd.read_csv(path, sep="\t", dtype=str)
            idx: dict[str, set[int]] = {}
            for _, row in df.iterrows():
                token = str(row["token"]).strip().lower()
                docs = {int(d) for d in str(row["docs"]).split(",") if d.strip()}
                idx[token] = docs
            self.indexes[name] = idx
    
    @staticmethod
    def _parse_date(date_str: str) -> datetime | None:
        """Parse une date au format j/mm/aaaa ou jj/mm/aaaa."""
        if not date_str:
            return None
        try:
            parts = date_str.strip().split("/")
            if len(parts) == 3:
                return datetime(int(parts[2]), int(parts[1]), int(parts[0]))
        except (ValueError, IndexError):
            pass
        return None
 
    def search(requete : dict) : 
        pass