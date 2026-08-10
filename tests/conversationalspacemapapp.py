"""Briefcase entry point for the standard-library unittest suite."""

from pathlib import Path
import unittest


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    suite = unittest.defaultTestLoader.discover(
        start_dir=str(project_root / "tests"),
        top_level_dir=str(project_root),
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return_code = 0 if result.wasSuccessful() else 1
    print(f">>>>>>>>>> EXIT {return_code} <<<<<<<<<<", flush=True)
    return return_code


if __name__ == "__main__":
    main()
