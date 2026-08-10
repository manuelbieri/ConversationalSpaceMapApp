import base64
import re
import unittest
from pathlib import Path

from conversationalspacemapapp.App.AboutRenderer import AboutRenderer


class TestAboutRenderer(unittest.TestCase):
    def test_page_is_local_and_matches_transcript_typography(self):
        content = AboutRenderer().render()

        self.assertIn("Conversational Space Map", content)
        self.assertIn("How to use", content)
        self.assertIn("License", content)
        self.assertIn("<ol>", content)
        self.assertIn("transcription_timestamps.txt", content)
        self.assertIn("background: transparent", content)
        self.assertIn(
            'font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
            content,
        )
        self.assertIn("font-size: 15px", content)
        self.assertIn("prefers-color-scheme: dark", content)
        self.assertIn('<body class="app">', content)
        self.assertIn("main {\n            width: 100%;", content)
        self.assertNotIn("manuelbieri.ch/ConversationalSpaceMapApp", content)

    def test_page_contains_complete_mit_license_and_embedded_icon(self):
        content = AboutRenderer().render()
        project_root = Path(__file__).parents[2]
        license_text = (project_root / "LICENSE").read_text(encoding="utf-8").strip()

        self.assertIn(license_text, content)
        self.assertIn('<details class="license" open>', content)
        encoded_icon = re.search(r"data:image/png;base64,([^\"]+)", content)
        self.assertIsNotNone(encoded_icon)
        self.assertTrue(
            base64.b64decode(encoded_icon.group(1)).startswith(b"\x89PNG\r\n\x1a\n")
        )

    def test_missing_icon_does_not_break_about_page(self):
        content = AboutRenderer(icon_path=Path("missing-icon.png")).render()

        self.assertIn("Conversational Space Map", content)
        self.assertNotIn("data:image/png;base64", content)

    def test_docs_page_matches_centered_static_variant(self):
        project_root = Path(__file__).parents[2]
        renderer = AboutRenderer()
        docs = (project_root / "docs" / "index.html").read_text(encoding="utf-8")
        docs_icon = project_root / "docs" / "images" / "CSM_icon.png"

        self.assertEqual(docs, renderer.render_docs())
        self.assertIn('<body class="docs">', docs)
        self.assertIn("width: min(calc(100% - 24px), 980px)", docs)
        self.assertIn("margin-inline: auto", docs)
        self.assertTrue(docs_icon.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertEqual(docs_icon.read_bytes(), renderer.icon_path.read_bytes())
