"""Additional checks for Library.search edge cases."""
import shutil
import tempfile
import unittest
from pathlib import Path

from search import Library


class ExtraChecks(unittest.TestCase):
    def test_survives_file_deletion(self):
        """Library loads once; searches work after the original file is gone."""
        original = Path(__file__).parent / "data" / "documents.json"
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_copy = Path(tmp_dir) / "documents.json"
            shutil.copy(original, temp_copy)
            library = Library(temp_copy)
            temp_copy.unlink()  # delete the file

            first = library.search("password")
            second = library.search("password")
            self.assertEqual(len(first), 2)
            self.assertEqual(len(second), 2)
            self.assertEqual(first, second)

    def test_preserves_order(self):
        """Matching documents appear in original file order."""
        library = Library(Path(__file__).parent / "data" / "documents.json")
        results = library.search("password", limit=3)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["source"], "it.md")
        self.assertEqual(results[1]["source"], "security.md")

    def test_negative_limit(self):
        """A negative limit must return an empty list."""
        library = Library(Path(__file__).parent / "data" / "documents.json")
        self.assertEqual(library.search("password", limit=-1), [])

    def test_preserve_fields(self):
        """Result documents keep their original text and source."""
        library = Library(Path(__file__).parent / "data" / "documents.json")
        results = library.search("vacation")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["source"], "leave.md")
        self.assertEqual(
            results[0]["text"],
            "This fictional team receives 15 vacation days per year."
        )


if __name__ == "__main__":
    unittest.main()
