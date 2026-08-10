import unittest
from dataclasses import replace
from pathlib import Path
import tempfile
from unittest.mock import MagicMock

import matplotlib
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt

matplotlib.use("Agg")

from tests import utilities

from conversationalspacemapapp.Plotter import PlotMap
from conversationalspacemapapp.Types import Data


class TestPlotMap(unittest.TestCase):
    def setUp(self):
        self.figure, self.axes = plt.subplots()

    def tearDown(self):
        plt.close(self.figure)

    def test_bar_plot_uses_modern_style_and_roles(self):
        plot = PlotMap.MapBarPlot(fig=self.figure)
        plot.plot(utilities.get_plot_options(title="Modern plot"))

        self.assertEqual(
            self.axes.get_facecolor(),
            mcolors.to_rgba(PlotMap.MapBarPlot.background_color),
        )
        self.assertTrue(
            all(not spine.get_visible() for spine in self.axes.spines.values())
        )
        self.assertEqual([patch.get_width() for patch in self.axes.patches], [-10, 15])
        self.assertTrue(
            any(list(line.get_xdata()) == [0, 0] for line in self.axes.lines)
        )
        self.assertTrue(any(line.get_visible() for line in self.axes.get_xgridlines()))
        self.assertEqual(self.axes.xaxis.get_major_formatter()(-10, None), "10")
        self.assertEqual(self.axes.get_title(), "Modern plot")
        self.assertEqual(self.axes.get_title(loc="left"), "")
        self.assertEqual(
            [text.get_text() for text in self.axes.get_legend().get_texts()],
            [utilities.speaker00_label, utilities.speaker01_label],
        )
        self.assertFalse(self.axes.get_legend().get_frame_on())
        self.assertEqual(self.axes.title.get_color(), "#000000")
        self.assertEqual(self.axes.yaxis.label.get_color(), "#000000")
        self.assertTrue(
            all(label.get_color() == "#000000" for label in self.axes.get_xticklabels())
        )
        self.assertTrue(
            all(
                label.get_color() == "#000000"
                for label in self.axes.get_legend().get_texts()
            )
        )
        self.assertTrue(all(text.get_color() == "#000000" for text in self.axes.texts))

    def test_long_plot_limits_ticks_but_keeps_every_bar(self):
        utterances = tuple(
            Data.Utterance(
                number=number,
                speaker=(
                    utilities.speaker00_name if number % 2 else utilities.speaker01_name
                ),
                words=number,
            )
            for number in range(1, 130)
        )
        plot = PlotMap.MapBarPlot(fig=self.figure)

        plot.plot(replace(utilities.get_plot_options(), map=utterances))

        y_ticks = list(self.axes.get_yticks())
        self.assertEqual(len(self.axes.patches), 129)
        self.assertLessEqual(len(y_ticks), PlotMap.MapBarPlot.max_y_ticks)
        self.assertEqual(y_ticks[0], 1)
        self.assertEqual(y_ticks[-1], 129)

    def test_short_plot_has_tick_for_every_utterance(self):
        self.assertEqual(PlotMap.MapBarPlot._get_utterance_ticks(3), [1, 2, 3])

    def test_axes_and_optional_decorations_can_be_hidden(self):
        plot = PlotMap.MapBarPlot(fig=self.figure)
        plot.plot(
            replace(
                utilities.get_plot_options(),
                show_title=False,
                labels=False,
                grid=False,
                legend=False,
                xaxis=False,
                yaxis=False,
            )
        )

        self.assertFalse(
            any(label.get_visible() for label in self.axes.get_xticklabels())
        )
        self.assertEqual(list(self.axes.get_yticks()), [])
        self.assertEqual(self.axes.get_title(loc="left"), "")
        self.assertEqual(len(self.axes.texts), 0)
        self.assertIsNone(self.axes.get_legend())
        self.assertFalse(any(line.get_visible() for line in self.axes.get_xgridlines()))

    def test_empty_plot_still_applies_canvas_style(self):
        plot = PlotMap.MapBarPlot(fig=self.figure)

        plot.plot(replace(utilities.get_plot_options(), map=()))

        self.assertEqual(len(self.axes.patches), 0)
        self.assertTrue(
            all(not spine.get_visible() for spine in self.axes.spines.values())
        )

    def test_legend_ignores_blank_and_duplicate_labels(self):
        options = utilities.get_plot_options(
            participants=(
                Data.ParticipantOptions(
                    utilities.speaker00_name,
                    utilities.speaker00_type,
                    "Shared",
                    utilities.speaker00_color,
                ),
                Data.ParticipantOptions(
                    utilities.speaker01_name,
                    utilities.speaker01_type,
                    "Shared",
                    utilities.speaker01_color,
                ),
            )
        )
        plot = PlotMap.MapBarPlot(fig=self.figure)

        plot.plot(options)

        self.assertEqual(
            [text.get_text() for text in self.axes.get_legend().get_texts()],
            ["Shared"],
        )

    def test_save_uses_print_friendly_settings(self):
        plot = PlotMap.MapBarPlot(fig=self.figure)
        plot.plot(utilities.get_plot_options())
        self.figure.savefig = MagicMock()

        plot.save("chart.png")

        self.figure.savefig.assert_called_once_with(
            "chart.png",
            dpi=300,
            facecolor=self.figure.get_facecolor(),
            bbox_inches="tight",
        )

    def test_save_supports_pdf_svg_and_png(self):
        plot = PlotMap.MapBarPlot(fig=self.figure)
        plot.plot(utilities.get_plot_options())

        with tempfile.TemporaryDirectory() as directory:
            signatures = {
                "pdf": b"%PDF",
                "svg": b"<?xml",
                "png": b"\x89PNG\r\n\x1a\n",
            }
            for extension, signature in signatures.items():
                with self.subTest(extension=extension):
                    path = Path(directory) / f"chart.{extension}"
                    plot.save(path)
                    self.assertTrue(path.is_file())
                    self.assertTrue(path.read_bytes().startswith(signature))
