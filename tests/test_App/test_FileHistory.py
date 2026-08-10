import tempfile
import unittest
from pathlib import Path

from conversationalspacemapapp.App.FileHistory import FileHistoryRepository


class TestFileHistoryRepository(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.directory = Path(self.temporary_directory.name)
        self.history = self.directory / "data" / "history.txt"
        self.first = self.directory / "a.txt"
        self.second = self.directory / "b.txt"
        self.first.touch()
        self.second.touch()

    def test_missing_history_is_empty(self):
        self.assertEqual(FileHistoryRepository(self.history).load(), [])

    def test_add_deduplicates_and_ignores_missing_files(self):
        repository = FileHistoryRepository(self.history)

        repository.add(self.second)
        repository.add(self.first)
        repository.add(self.first)
        repository.add(self.directory / "missing.txt")

        self.assertEqual(repository.load(), [self.first, self.second])
        self.assertEqual(
            self.history.read_text(encoding="utf-8").splitlines(),
            [self.second.as_posix(), self.first.as_posix()],
        )

    def test_load_filters_blank_duplicate_and_stale_entries(self):
        self.history.parent.mkdir()
        self.history.write_text(
            f"\n{self.second}\n{self.first}\n{self.second}\nmissing\n",
            encoding="utf-8",
        )

        self.assertEqual(
            FileHistoryRepository(self.history).load(),
            [self.first, self.second],
        )

    def test_invalid_encoding_is_treated_as_empty_history(self):
        self.history.parent.mkdir()
        self.history.write_bytes(b"\xff\xfe")

        self.assertEqual(FileHistoryRepository(self.history).load(), [])

    def test_legacy_history_is_migrated_once(self):
        legacy = self.directory / "legacy.txt"
        legacy.write_text(f"{self.second}\n{self.first}\n", encoding="utf-8")
        repository = FileHistoryRepository(self.history, legacy_path=legacy)

        self.assertEqual(repository.load(), [self.first, self.second])
        self.assertTrue(self.history.is_file())
        legacy.write_text("", encoding="utf-8")
        self.assertEqual(repository.load(), [self.first, self.second])

    def test_existing_history_is_not_replaced_by_legacy_file(self):
        self.history.parent.mkdir()
        self.history.write_text(f"{self.first}\n", encoding="utf-8")
        legacy = self.directory / "legacy.txt"
        legacy.write_text(f"{self.second}\n", encoding="utf-8")

        repository = FileHistoryRepository(self.history, legacy_path=legacy)

        self.assertEqual(repository.load(), [self.first])

    def test_clear_is_persistent_and_prevents_legacy_reimport(self):
        legacy = self.directory / "legacy.txt"
        legacy.write_text(f"{self.first}\n", encoding="utf-8")
        repository = FileHistoryRepository(self.history, legacy_path=legacy)
        self.assertEqual(repository.load(), [self.first])

        repository.clear()

        self.assertTrue(self.history.is_file())
        self.assertEqual(self.history.read_text(encoding="utf-8"), "")
        self.assertEqual(repository.load(), [])
        self.assertEqual(
            FileHistoryRepository(self.history, legacy_path=legacy).load(),
            [],
        )
