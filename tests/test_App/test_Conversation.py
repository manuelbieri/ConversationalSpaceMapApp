import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from conversationalspacemapapp.App.Conversation import (
    ConversationSession,
    PlotSettings,
)
from conversationalspacemapapp.Types import Constants, Data


class TestConversationSession(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.path = Path(self.temporary_directory.name) / "transcript.txt"
        self.path.write_text("content", encoding="utf-8")
        self.parser = SimpleNamespace(
            map=[
                Data.Utterance(1, "A", 0, "Question"),
                Data.Utterance(2, "B", 4, "Answer"),
            ],
            participants=["A", "B"],
        )
        self.session = ConversationSession(
            parser_factory=lambda path: self.parser,
            default_role=Constants.Participant.Undefined,
            default_color="#123456",
        )

    def test_load_builds_participant_state_and_statistics(self):
        self.session.load(self.path)

        self.assertTrue(self.session.is_loaded)
        self.assertEqual(self.session.path, self.path)
        self.assertIs(self.session.parser, self.parser)
        self.assertEqual(self.session.utterances, tuple(self.parser.map))
        self.assertEqual(self.session.participant("A").label, "A")
        self.assertEqual(self.session.participant("A").color, "#123456")
        self.assertEqual(
            self.session.roles_by_speaker(),
            {
                "A": Constants.Participant.Undefined,
                "B": Constants.Participant.Undefined,
            },
        )
        self.assertEqual(
            self.session.colors_by_speaker(),
            {"A": "#123456", "B": "#123456"},
        )
        self.assertEqual(self.session.labels_by_speaker(), {"A": "A", "B": "B"})
        statistics = self.session.statistics()
        self.assertEqual(statistics.total_words, 4)
        self.assertEqual(statistics.speaker_count, 2)
        self.assertEqual(statistics.average_words_per_utterance, 2.0)
        self.assertEqual(statistics.utterances_for("A"), 1)
        self.assertEqual(statistics.utterances_for("B"), 1)
        self.assertEqual(statistics.average_words_for("A"), 0.0)
        self.assertEqual(statistics.average_words_for("B"), 4.0)
        self.assertEqual(statistics.longest_utterance_for("A"), 0)
        self.assertEqual(statistics.longest_utterance_for("B"), 4)
        self.assertEqual(statistics.percentage_for("A"), 0.0)
        self.assertEqual(statistics.percentage_for("B"), 100.0)
        self.assertEqual(statistics.percentage_for("missing"), 0.0)
        self.assertEqual(
            statistics.as_text(),
            "Total words: 4 / Words A: 0 (0.0%) / "
            "Words B: 4 (100.0%) / Total utterances: 2",
        )

    def test_participant_and_plot_updates_flow_into_plot_options(self):
        self.session.load(self.path)
        self.session.set_participant_role("A", Constants.Participant.Interviewer)
        self.session.set_participant_label("A", "Facilitator")
        self.session.set_participant_color("A", "#ABCDEF")
        settings = PlotSettings(
            title="Title",
            show_title=False,
            labels=False,
            interviewer_label="Left",
            interviewee_label="Right",
            yaxis=False,
            xaxis=False,
            grid=False,
            legend=False,
        )
        self.session.set_plot_settings(settings)

        options = self.session.build_plot_options()

        self.assertEqual(options.map, tuple(self.parser.map))
        self.assertEqual(options.title, "Title")
        self.assertFalse(options.show_title)
        self.assertFalse(options.labels)
        self.assertFalse(options.yaxis)
        self.assertFalse(options.xaxis)
        self.assertFalse(options.grid)
        self.assertFalse(options.legend)
        self.assertEqual(options.get_participant_label("A"), "Facilitator")
        self.assertEqual(options.get_participant_color("A"), "#ABCDEF")
        self.assertEqual(self.session.colors_by_speaker()["A"], "#ABCDEF")
        self.assertEqual(self.session.labels_by_speaker()["A"], "Facilitator")
        self.assertEqual(
            options.get_participant_type("A"), Constants.Participant.Interviewer
        )

    def test_zero_word_statistics_are_safe(self):
        self.parser.map = [Data.Utterance(1, "A", 0)]
        self.parser.participants = ["A"]
        self.session.load(self.path)

        statistics = self.session.statistics()

        self.assertEqual(statistics.total_words, 0)
        self.assertEqual(statistics.average_words_per_utterance, 0.0)
        self.assertEqual(statistics.average_words_for("A"), 0.0)
        self.assertEqual(statistics.percentage_for("A"), 0.0)
        self.assertIn("Words A: 0 (0.0%)", statistics.as_text())

    def test_failed_load_is_atomic(self):
        self.session.load(self.path)
        original_parser = self.session.parser
        failing_path = self.path.with_name("broken.txt")
        failing_path.write_text("broken", encoding="utf-8")
        self.session._parser_factory = lambda path: (_ for _ in ()).throw(
            ValueError("invalid transcript")
        )

        with self.assertRaisesRegex(ValueError, "invalid transcript"):
            self.session.load(failing_path)

        self.assertEqual(self.session.path, self.path)
        self.assertIs(self.session.parser, original_parser)

    def test_invalid_operations_have_clear_errors(self):
        with self.assertRaises(FileNotFoundError):
            self.session.load(self.path.with_name("missing.txt"))
        with self.assertRaisesRegex(RuntimeError, "No conversation"):
            self.session.build_plot_options()

        self.session.load(self.path)
        with self.assertRaisesRegex(KeyError, "Unknown participant"):
            self.session.participant("missing")
        with self.assertRaisesRegex(TypeError, "role must be"):
            self.session.set_participant_role("A", "Interviewer")
        with self.assertRaisesRegex(TypeError, "settings must be"):
            self.session.set_plot_settings(object())
