from pathlib import Path


class FileHistoryRepository:
    """Persists recent transcript paths in an injected writable location."""

    def __init__(self, path: Path, *, legacy_path: Path | None = None) -> None:
        self.path = Path(path)
        self.legacy_path = Path(legacy_path) if legacy_path is not None else None
        self._migration_attempted = False

    def load(self) -> list[Path]:
        self._migrate_legacy_history()
        return self._read_valid_paths(self.path)

    def add(self, path: Path) -> None:
        path = Path(path)
        if not path.is_file() or path in self.load():
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as history:
            history.write(path.as_posix() + "\n")

    def clear(self) -> None:
        """Clear recent files and prevent legacy history from being re-imported."""
        self._migration_attempted = True
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("", encoding="utf-8")

    @staticmethod
    def _read_valid_paths(path: Path) -> list[Path]:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError, UnicodeError:
            return []

        output: list[Path] = []
        for candidate in sorted(Path(line.strip()) for line in lines if line.strip()):
            if candidate.is_file() and candidate not in output:
                output.append(candidate)
        return output

    def _migrate_legacy_history(self) -> None:
        if self._migration_attempted:
            return
        self._migration_attempted = True
        if self.path.exists() or self.legacy_path is None:
            return

        legacy_paths = self._read_valid_paths(self.legacy_path)
        if not legacy_paths:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            "".join(path.as_posix() + "\n" for path in legacy_paths),
            encoding="utf-8",
        )
