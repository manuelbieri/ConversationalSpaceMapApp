import unittest

from tests import utilities

from conversationalspacemapapp.Types import Constants, Data


class TestPlotOptions(unittest.TestCase):
    def test_plot_options_are_ui_independent(self):
        options = utilities.get_plot_options(title="Interview")

        self.assertEqual(options.title, "Interview")
        self.assertEqual(options.map[0].speaker, utilities.speaker00_name)
        self.assertEqual(
            options.get_participant_color(utilities.speaker00_name),
            utilities.speaker00_color,
        )
        self.assertEqual(
            options.get_participant_label(utilities.speaker01_name),
            utilities.speaker01_label,
        )
        self.assertEqual(
            options.get_participant_type(utilities.speaker00_name),
            Constants.Participant.Interviewer,
        )

    def test_unknown_participant_raises_clear_error(self):
        with self.assertRaisesRegex(KeyError, "Unknown participant: missing"):
            utilities.get_plot_options().get_participant_type("missing")

    def test_utterances_sort_by_number(self):
        utterances = [
            Data.Utterance(2, "B", 2),
            Data.Utterance(1, "A", 1),
        ]

        self.assertEqual([item.number for item in sorted(utterances)], [1, 2])
