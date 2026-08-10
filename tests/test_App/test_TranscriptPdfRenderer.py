import tempfile
import unittest
from pathlib import Path

from conversationalspacemapapp.App.TranscriptPdfRenderer import TranscriptPdfRenderer
from conversationalspacemapapp.App.TranscriptPresentation import (
    TranscriptPresentation,
)
from conversationalspacemapapp.Types import Constants, Data


class TestTranscriptPdfRenderer(unittest.TestCase):
    def setUp(self):
        self.renderer = TranscriptPdfRenderer()

    @staticmethod
    def _messages(text: str = "Hello from the transcript"):
        return TranscriptPresentation.build(
            [
                Data.Utterance(
                    1,
                    "SPEAKER_00",
                    len(text.split()),
                    text,
                    "00:00:01",
                    "00:00:04",
                )
            ],
            roles_by_speaker={
                "SPEAKER_00": Constants.Participant.Interviewee,
            },
            colors_by_speaker={"SPEAKER_00": "#123456"},
            labels_by_speaker={"SPEAKER_00": "Guest"},
        )

    def test_paginate_preserves_presentation_and_splits_long_messages(self):
        messages = self._messages("word " * 5000)

        pages = self.renderer.paginate(messages)
        blocks = [block for page in pages for block in page]

        self.assertGreater(len(pages), 1)
        self.assertGreater(len(blocks), 1)
        self.assertFalse(blocks[0].continued)
        self.assertTrue(blocks[1].continued)
        self.assertTrue(blocks[-1].final)
        self.assertEqual(blocks[0].message.label, "Guest")
        self.assertEqual(blocks[0].message.alignment, "interviewee")
        self.assertEqual(blocks[0].message.color, "#123456")

    def test_save_creates_pdf_and_rejects_other_extensions(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "transcript.pdf"

            self.renderer.save(target, self._messages(), title="Transcript - Test")

            content = target.read_bytes()
            self.assertTrue(content.startswith(b"%PDF"))
            self.assertGreater(len(content), 1_000)
            with self.assertRaisesRegex(ValueError, r"\.pdf extension"):
                self.renderer.save(
                    target.with_suffix(".txt"),
                    self._messages(),
                    title="Transcript",
                )

    def test_empty_transcript_still_creates_one_page(self):
        self.assertEqual(self.renderer.paginate(()), ((),))
