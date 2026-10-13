"""Arena starter: deliberately buggy. Repair using the task and checks."""
import json
from pathlib import Path


class Library:
    def __init__(self, path):
        self.path = Path(path)
        self.documents = json.loads(self.path.read_text(encoding="utf-8"))

    def search(self, query, limit=3):
        trimmed = query.strip()
        if not trimmed or limit <= 0:
            return []

        q_lower = trimmed.lower()
        matches = [
            doc for doc in self.documents
            if q_lower in doc["text"].lower()
        ]
        return matches[:limit]


if __name__ == "__main__":
    library = Library(Path(__file__).parent / "data" / "documents.json")
    for hit in library.search("password", limit=1):
        print(f"[{hit['source']}] {hit['text']}")
