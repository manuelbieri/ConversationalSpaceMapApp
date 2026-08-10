import asyncio
import pathlib
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import matplotlib
import toga

matplotlib.use("Agg")

import tests.TestResources as TestResources

from conversationalspacemapapp.App.Conversation import PlotSettings
from conversationalspacemapapp.App.FileHistory import FileHistoryRepository
from conversationalspacemapapp.App.PlotRendering import RenderedChart
from conversationalspacemapapp.App.TogaApp import app as TogaApp
from conversationalspacemapapp.Plotter import StylePicker
from conversationalspacemapapp.Types import Constants, Data


def bare_app() -> TogaApp.ConversationalSpaceMapAppToga:
    return object.__new__(TogaApp.ConversationalSpaceMapAppToga)


class TestTogaHandlers(unittest.TestCase):
    def test_history_repository_uses_toga_data_path(self):
        app = bare_app()
        with tempfile.TemporaryDirectory() as directory:
            app._history_repository = None
            app._paths = SimpleNamespace(data=pathlib.Path(directory))

            repository = app.history_repository

            self.assertEqual(
                repository.path,
                pathlib.Path(directory) / "history.txt",
            )
            self.assertIn("App/assets/history.txt", repository.legacy_path.as_posix())
            self.assertIs(app.history_repository, repository)

    def test_path_properties_reflect_session(self):
        app = bare_app()
        app.session = SimpleNamespace(path=None, parser=None, is_loaded=False)

        self.assertIsNone(app.path)
        self.assertIsNone(app.parser)
        self.assertFalse(app.has_path)
        self.assertFalse(app.has_parser)
        self.assertIsNone(app.path_filename)
        self.assertEqual(app.path_as_str(), "")

        app.session.path = TestResources.path_short_transcript
        app.session.parser = object()
        app.session.is_loaded = True
        self.assertTrue(app.has_path)
        self.assertTrue(app.has_parser)
        self.assertEqual(app.path_filename, TestResources.path_short_transcript.name)
        self.assertEqual(
            app.path_as_str(), TestResources.path_short_transcript.as_posix()
        )

    def test_plot_handler_synchronizes_settings_before_rendering(self):
        app = bare_app()
        app.session = MagicMock(is_loaded=True)
        app._read_plot_settings = MagicMock(return_value=PlotSettings(title="New"))
        app._update_plot = MagicMock()
        app._set_info_layout = MagicMock()

        app.plot_handler()

        app.session.set_plot_settings.assert_called_once_with(PlotSettings(title="New"))
        app._update_plot.assert_called_once_with()
        app._set_info_layout.assert_called_once_with()

    def test_plot_handler_is_safe_before_loading(self):
        app = bare_app()
        app.session = MagicMock(is_loaded=False)
        app._update_plot = MagicMock()

        app.plot_handler()

        app._update_plot.assert_not_called()

    def test_participant_handlers_update_session_and_views(self):
        app = bare_app()
        app.session = MagicMock(is_loaded=True)
        app.plot_handler = MagicMock()
        app._set_transcript = MagicMock()
        role_widget = SimpleNamespace(value=Constants.Participant.Interviewee)
        label_widget = SimpleNamespace(value="Guest")

        app._participant_role_handler("Speaker", role_widget)
        app._participant_label_handler("Speaker", label_widget)

        app.session.set_participant_role.assert_called_once_with(
            "Speaker", Constants.Participant.Interviewee
        )
        app.session.set_participant_label.assert_called_once_with("Speaker", "Guest")
        self.assertEqual(app.plot_handler.call_count, 2)
        self.assertEqual(app._set_transcript.call_count, 2)

    def test_color_handler_updates_widget_session_and_plot(self):
        app = bare_app()
        app.session = MagicMock(is_loaded=True)
        app.plot_handler = MagicMock()
        app._set_transcript = MagicMock()
        app._color_button_hex = MagicMock(return_value="#AABBCC")
        color_widget = SimpleNamespace(value=None)
        color_button = object()

        app._participant_color_handler("Speaker", color_widget, color_button)

        self.assertEqual(color_widget.value, "#AABBCC")
        app.session.set_participant_color.assert_called_once_with("Speaker", "#AABBCC")
        app.plot_handler.assert_called_once_with(color_button)
        app._set_transcript.assert_called_once_with()

    def test_general_widget_values_create_plot_settings(self):
        app = bare_app()
        app.plot_title_input = SimpleNamespace(value=None)
        app.plot_title = SimpleNamespace(value=False)
        app.plot_labels = SimpleNamespace(value=False)
        app.interviewer_label_input = SimpleNamespace(value="Left")
        app.interviewee_label_input = SimpleNamespace(value=None)
        app.plot_yaxis = SimpleNamespace(value=False)
        app.plot_xaxis = SimpleNamespace(value=True)
        app.plot_legend = SimpleNamespace(value=False)
        app.plot_grid = SimpleNamespace(value=True)

        settings = app._read_plot_settings()

        self.assertEqual(settings.title, "")
        self.assertEqual(settings.interviewer_label, "Left")
        self.assertEqual(settings.interviewee_label, "")
        self.assertFalse(settings.show_title)
        self.assertFalse(settings.labels)
        self.assertFalse(settings.yaxis)
        self.assertTrue(settings.xaxis)
        self.assertFalse(settings.legend)
        self.assertTrue(settings.grid)

    def test_statistics_cards_use_session_values_and_participant_styles(self):
        app = bare_app()
        statistics = SimpleNamespace(
            total_words=10,
            total_utterances=2,
            speaker_count=2,
            average_words_per_utterance=5.0,
            words_by_participant={"A": 4, "B": 6},
            percentage_for=lambda speaker: {"A": 40.0, "B": 60.0}[speaker],
            utterances_for=lambda speaker: {"A": 1, "B": 1}[speaker],
            average_words_for=lambda speaker: {"A": 4.0, "B": 6.0}[speaker],
            longest_utterance_for=lambda speaker: {"A": 4, "B": 6}[speaker],
        )
        app.session = SimpleNamespace(
            is_loaded=True,
            statistics=lambda: statistics,
            participants=(
                SimpleNamespace(speaker="A", label="Host", color="#112233"),
                SimpleNamespace(speaker="B", label="Guest", color="#AABBCC"),
            ),
        )

        cards = app._statistics_card_data()

        self.assertEqual(
            cards,
            (
                TogaApp.StatisticCardData(
                    "Total words", "10", "across transcript", "#E2E8F0"
                ),
                TogaApp.StatisticCardData(
                    "Total utterances", "2", "speaker turns", "#E2E8F0"
                ),
                TogaApp.StatisticCardData("Speakers", "2", "identified", "#E2E8F0"),
                TogaApp.StatisticCardData(
                    "Average utterance", "5.0 words", "per utterance", "#E2E8F0"
                ),
                TogaApp.StatisticCardData(
                    "Host",
                    "4 words · 40.0%",
                    "1 utterance · 4.0 avg words · 4 max words",
                    "#112233",
                ),
                TogaApp.StatisticCardData(
                    "Guest",
                    "6 words · 60.0%",
                    "1 utterance · 6.0 avg words · 6 max words",
                    "#AABBCC",
                ),
            ),
        )

        app.session.is_loaded = False
        self.assertEqual(app._statistics_card_data(), ())

    def test_setting_statistics_replaces_scroll_content(self):
        app = bare_app()
        layout = object()
        app.statistics = SimpleNamespace(content=None)
        app._build_statistics_layout = MagicMock(return_value=layout)

        app._set_info_layout()

        self.assertIs(app.statistics.content, layout)

    def test_transcript_uses_session_state_and_injected_renderer(self):
        app = bare_app()
        utterances = (Data.Utterance(1, "A", 1, "Hello"),)
        app.session = MagicMock(utterances=utterances)
        app.session.roles_by_speaker.return_value = {
            "A": Constants.Participant.Interviewee
        }
        app.session.colors_by_speaker.return_value = {"A": "#ABCDEF"}
        app.session.labels_by_speaker.return_value = {"A": "Guest"}
        app.transcript_renderer = MagicMock()
        app.transcript_renderer.render.return_value = "<html>chat</html>"
        app.transcript = SimpleNamespace(content=None)

        app._set_transcript()

        app.transcript_renderer.render.assert_called_once_with(
            utterances,
            roles_by_speaker={"A": Constants.Participant.Interviewee},
            colors_by_speaker={"A": "#ABCDEF"},
            labels_by_speaker={"A": "Guest"},
        )
        self.assertEqual(app.transcript.content, "<html>chat</html>")

    def test_transcript_static_facade_remains_available(self):
        content = TogaApp.ConversationalSpaceMapAppToga._build_transcript_html(
            [Data.Utterance(1, "A", 1, "Hello")],
            {"A": Constants.Participant.Interviewer},
        )

        self.assertIn('class="message-row interviewer"', content)

    def test_chart_image_action_is_created_then_reused(self):
        app = bare_app()
        app._chart_image_action = None
        app.chart = MagicMock()
        action = SimpleNamespace(image=None, width=None, height=None)
        app.chart.draw_image.return_value = action

        with patch.object(TogaApp.toga, "Image", side_effect=lambda data: data):
            app._set_chart_image(b"first", 320, 240)
            app._set_chart_image(b"second", 640, 480)

        app.chart.draw_image.assert_called_once_with(
            b"first", x=0, y=0, width=320, height=240
        )
        self.assertEqual(action.image, b"second")
        self.assertEqual((action.width, action.height), (640, 480))
        app.chart.redraw.assert_called_once_with()

    def test_render_result_and_error_update_save_state(self):
        app = bare_app()
        app._set_chart_image = MagicMock()
        app.save = SimpleNamespace(enabled=False)
        plot = MagicMock()
        result = RenderedChart(plot, b"image", 320, 240)

        app._apply_rendered_chart(result)

        app._set_chart_image.assert_called_once_with(b"image", 320, 240)
        self.assertIs(app.map, plot)
        self.assertTrue(app.save.enabled)

        with patch.object(TogaApp.traceback, "print_exception") as print_exception:
            app._handle_render_error(RuntimeError("failed"))
        print_exception.assert_called_once()
        self.assertTrue(app.save.enabled)

        app.map = None
        with patch.object(TogaApp.traceback, "print_exception"):
            app._handle_render_error(RuntimeError("failed"))
        self.assertFalse(app.save.enabled)

    def test_resize_ignores_invalid_and_unchanged_sizes(self):
        app = bare_app()
        app._chart_width = 500
        app._chart_height = 400
        app._chart_image_action = None
        app.session = MagicMock(is_loaded=False)
        app._update_plot = MagicMock()
        canvas = MagicMock()

        app._resize_chart(canvas, 0, 10)
        app._resize_chart(canvas, 500, 400)

        app._update_plot.assert_not_called()
        canvas.redraw.assert_not_called()

    def test_resize_updates_canvas_and_queues_loaded_plot(self):
        app = bare_app()
        app._chart_width = 500
        app._chart_height = 400
        app._chart_image_action = SimpleNamespace(width=500, height=400)
        app.session = MagicMock(is_loaded=True)
        app._update_plot = MagicMock()
        canvas = MagicMock()

        app._resize_chart(canvas, 800.2, 599.8)

        self.assertEqual((app._chart_width, app._chart_height), (800, 600))
        self.assertEqual(
            (app._chart_image_action.width, app._chart_image_action.height),
            (800, 600),
        )
        canvas.redraw.assert_called_once_with()
        app._update_plot.assert_called_once_with()

    def test_update_plot_submits_options_and_starts_one_runner(self):
        app = bare_app()
        options = object()
        app.session = MagicMock(is_loaded=True)
        app.session.build_plot_options.return_value = options
        app.render_coordinator = MagicMock()
        app._chart_width = 320
        app._chart_height = 240
        app.save = SimpleNamespace(enabled=True)
        app._plot_task = None
        task = MagicMock()

        def create_task(coroutine):
            coroutine.close()
            return task

        app._impl = SimpleNamespace(
            loop=SimpleNamespace(create_task=MagicMock(side_effect=create_task))
        )

        app._update_plot()

        app.render_coordinator.submit.assert_called_once_with(options, 320, 240)
        self.assertFalse(app.save.enabled)
        self.assertIs(app._plot_task, task)

        task.done.return_value = False
        app._update_plot()
        self.assertEqual(app._impl.loop.create_task.call_count, 1)

        app.session.is_loaded = False
        app.render_coordinator.submit.reset_mock()
        app._update_plot()
        app.render_coordinator.submit.assert_not_called()

    def test_palette_changes_all_color_buttons(self):
        app = bare_app()
        buttons = tuple(
            SimpleNamespace(style=SimpleNamespace(background_color=None))
            for _ in range(8)
        )
        app.participant_widgets = {
            "A": SimpleNamespace(color_buttons=buttons),
        }
        app.color_palette = SimpleNamespace(value=StylePicker.Palette.Pastel)

        app._set_participants_color_selection(object())

        self.assertEqual(
            [button.style.background_color for button in buttons],
            StylePicker.Palette.Pastel.value,
        )

    def test_color_button_rgb_is_converted_to_hex(self):
        button = SimpleNamespace(
            style=SimpleNamespace(background_color=SimpleNamespace(r=1, g=2, b=255))
        )

        self.assertEqual(
            TogaApp.ConversationalSpaceMapAppToga._color_button_hex(button),
            "#0102FF",
        )

    def test_export_paths_use_the_selected_supported_extension(self):
        app = bare_app()
        for selected_format, extension in app.export_extensions.items():
            with self.subTest(selected_format=selected_format):
                app.file_format = SimpleNamespace(value=selected_format)
                self.assertEqual(app._selected_export_extension(), extension)
                self.assertEqual(
                    app._normalize_export_path("chart.wrong", extension),
                    pathlib.Path("chart" + extension),
                )

        with self.assertRaisesRegex(ValueError, "Unsupported export extension"):
            app._normalize_export_path("chart.txt", ".txt")

    def test_path_selection_only_loads_new_valid_file(self):
        app = bare_app()
        app.session = SimpleNamespace(path=None)
        app._load_path = MagicMock()

        app._path_selection_handler(SimpleNamespace(value=None))
        app._path_selection_handler(SimpleNamespace(value=pathlib.Path("missing")))
        app._path_selection_handler(
            SimpleNamespace(value=TestResources.path_short_transcript)
        )
        app.session.path = TestResources.path_short_transcript
        app._path_selection_handler(
            SimpleNamespace(value=TestResources.path_short_transcript)
        )

        app._load_path.assert_called_once_with(TestResources.path_short_transcript)

    def test_set_path_adds_new_selection_and_rejects_missing_file(self):
        class Selection:
            def __init__(self):
                self.items = []
                self._value = None

            @property
            def value(self):
                return self._value

            @value.setter
            def value(self, value):
                if value not in self.items:
                    raise ValueError(value)
                self._value = value

        app = bare_app()
        app.session = SimpleNamespace(path=None)
        app.path_input = Selection()
        app._load_path = MagicMock()

        app._set_path(TestResources.path_short_transcript)

        self.assertEqual(app.path_input.value, TestResources.path_short_transcript)
        app._load_path.assert_called_once_with(TestResources.path_short_transcript)
        with self.assertRaises(FileNotFoundError):
            app._set_path(pathlib.Path("missing.txt"))

    def test_load_path_orchestrates_views_and_persistence(self):
        app = bare_app()
        app.session = MagicMock(is_loaded=True)
        app._create_participants_layout = MagicMock()
        app._set_plot_title = MagicMock()
        app._read_plot_settings = MagicMock(return_value=PlotSettings())
        app._update_plot = MagicMock()
        app._set_info_layout = MagicMock()
        app._set_transcript = MagicMock()
        app._history_repository = MagicMock()
        app.clear_history_button = SimpleNamespace(enabled=False)
        app.plot = SimpleNamespace(enabled=False)
        app.transcript_export_button = SimpleNamespace(enabled=False)

        app._load_path(TestResources.path_short_transcript)

        app.session.load.assert_called_once_with(TestResources.path_short_transcript)
        app._create_participants_layout.assert_called_once_with()
        app._set_plot_title.assert_called_once_with()
        app.session.set_plot_settings.assert_called_once_with(PlotSettings())
        app._update_plot.assert_called_once_with()
        app._set_info_layout.assert_called_once_with()
        app._set_transcript.assert_called_once_with()
        app._history_repository.add.assert_called_once_with(
            TestResources.path_short_transcript
        )
        self.assertTrue(app.clear_history_button.enabled)
        self.assertTrue(app.plot.enabled)
        self.assertTrue(app.transcript_export_button.enabled)

    def test_widget_style_supports_all_padding_and_flex_combinations(self):
        widget = SimpleNamespace(style=SimpleNamespace())

        TogaApp.ConversationalSpaceMapAppToga._set_widget_style(widget)
        self.assertEqual(widget.style.flex, 1)
        self.assertEqual(widget.style.margin, 5)

        widget = SimpleNamespace(style=SimpleNamespace())
        TogaApp.ConversationalSpaceMapAppToga._set_widget_style(widget, flex=0)
        self.assertEqual(widget.style.flex, 0)
        self.assertEqual(widget.style.margin, 5)

        widget = SimpleNamespace(style=SimpleNamespace())
        TogaApp.ConversationalSpaceMapAppToga._set_widget_style(widget, padding=3)
        self.assertEqual(widget.style.flex, 1)
        self.assertEqual(widget.style.margin, 3)

        widget = SimpleNamespace(style=SimpleNamespace())
        TogaApp.ConversationalSpaceMapAppToga._set_widget_style(
            widget, padding=2, flex=4
        )
        self.assertEqual((widget.style.margin, widget.style.flex), (2, 4))

    def test_transparent_background_is_only_set_on_macos(self):
        widget = SimpleNamespace(style=SimpleNamespace(background_color=None))
        with patch.object(TogaApp.platform, "platform", return_value="macOS-15"):
            TogaApp.ConversationalSpaceMapAppToga._set_transparent_background(widget)
        self.assertEqual(widget.style.background_color, "transparent")

        widget.style.background_color = None
        with patch.object(TogaApp.platform, "platform", return_value="Linux"):
            TogaApp.ConversationalSpaceMapAppToga._set_transparent_background(widget)
        self.assertIsNone(widget.style.background_color)


class TestTogaFileHandlers(unittest.IsolatedAsyncioTestCase):
    async def test_open_handler_loads_selected_file(self):
        app = bare_app()
        app._get_path = AsyncMock(return_value=TestResources.path_short_transcript)
        app._set_path = MagicMock()

        await app.open_handler(object())

        app._set_path.assert_called_once_with(TestResources.path_short_transcript)

    async def test_open_handler_ignores_cancel_and_missing_file(self):
        app = bare_app()
        app._set_path = MagicMock()
        for result in [None, pathlib.Path("missing.txt")]:
            app._get_path = AsyncMock(return_value=result)
            await app.open_handler(object())
        app._set_path.assert_not_called()

    async def test_clear_history_confirms_and_keeps_active_session(self):
        app = bare_app()
        active_session = object()
        app.session = active_session
        app._history_repository = MagicMock()
        app.path_input = SimpleNamespace(items=[pathlib.Path("recent.txt")])
        app.clear_history_button = SimpleNamespace(enabled=True)
        app._main_window = SimpleNamespace(dialog=AsyncMock(return_value=True))
        dialog = object()

        with patch.object(TogaApp.toga, "QuestionDialog", return_value=dialog):
            await app.clear_history_handler(object())

        app._main_window.dialog.assert_awaited_once_with(dialog)
        app._history_repository.clear.assert_called_once_with()
        self.assertEqual(app.path_input.items, [])
        self.assertFalse(app.clear_history_button.enabled)
        self.assertIs(app.session, active_session)

    async def test_clear_history_can_be_cancelled(self):
        app = bare_app()
        app._history_repository = MagicMock()
        recent = [pathlib.Path("recent.txt")]
        app.path_input = SimpleNamespace(items=recent)
        app.clear_history_button = SimpleNamespace(enabled=True)
        app._main_window = SimpleNamespace(dialog=AsyncMock(return_value=False))

        with patch.object(TogaApp.toga, "QuestionDialog", return_value=object()):
            await app.clear_history_handler(object())

        app._history_repository.clear.assert_not_called()
        self.assertIs(app.path_input.items, recent)
        self.assertTrue(app.clear_history_button.enabled)

    async def test_save_handler_saves_rendered_map(self):
        app = bare_app()
        app.session = MagicMock(is_loaded=True)
        app.map = MagicMock()
        target = pathlib.Path("map.png")
        app._get_save_path = AsyncMock(return_value=target)

        await app.save_handler(object())

        app.map.save.assert_called_once_with(target)

    async def test_save_handler_ignores_unavailable_map_and_cancel(self):
        app = bare_app()
        app.session = MagicMock(is_loaded=False)
        app.map = None
        app._get_save_path = AsyncMock()
        await app.save_handler(object())
        app._get_save_path.assert_not_called()

        app.session.is_loaded = True
        app.map = MagicMock()
        app._get_save_path = AsyncMock(return_value=None)
        await app.save_handler(object())
        app.map.save.assert_not_called()

    async def test_transcript_pdf_export_uses_current_presentation(self):
        app = bare_app()
        utterances = (Data.Utterance(1, "A", 1, "Hello", "00:01", "00:02"),)
        app.session = MagicMock(
            is_loaded=True,
            path=TestResources.path_short_transcript,
            utterances=utterances,
        )
        app.session.roles_by_speaker.return_value = {
            "A": Constants.Participant.Interviewee
        }
        app.session.colors_by_speaker.return_value = {"A": "#ABCDEF"}
        app.session.labels_by_speaker.return_value = {"A": "Guest"}
        app.transcript_pdf_renderer = MagicMock()
        target = pathlib.Path("transcript.pdf")
        app._get_transcript_pdf_path = AsyncMock(return_value=target)

        await app.export_transcript_pdf_handler(object())

        args, kwargs = app.transcript_pdf_renderer.save.call_args
        self.assertEqual(args[0], target)
        self.assertEqual(args[1][0].label, "Guest")
        self.assertEqual(args[1][0].alignment, "interviewee")
        self.assertEqual(args[1][0].color, "#ABCDEF")
        self.assertEqual(
            kwargs["title"],
            f"Transcript - {TestResources.path_short_transcript.stem}",
        )

    async def test_transcript_pdf_export_handles_unavailable_cancel_and_error(self):
        app = bare_app()
        app.session = MagicMock(is_loaded=False, path=None)
        app._get_transcript_pdf_path = AsyncMock()

        await app.export_transcript_pdf_handler(object())
        app._get_transcript_pdf_path.assert_not_called()

        app.session.is_loaded = True
        app._get_transcript_pdf_path = AsyncMock(return_value=None)
        await app.export_transcript_pdf_handler(object())

        app.session.path = TestResources.path_short_transcript
        app.session.utterances = (Data.Utterance(1, "A", 1, "Hello"),)
        app.session.roles_by_speaker.return_value = {}
        app.session.colors_by_speaker.return_value = {}
        app.session.labels_by_speaker.return_value = {}
        app._get_transcript_pdf_path = AsyncMock(
            return_value=pathlib.Path("transcript.pdf")
        )
        app.transcript_pdf_renderer = MagicMock()
        app.transcript_pdf_renderer.save.side_effect = RuntimeError("disk full")
        error_dialog = object()
        app._main_window = SimpleNamespace(dialog=AsyncMock())

        with (
            patch.object(TogaApp.traceback, "print_exception"),
            patch.object(TogaApp.toga, "ErrorDialog", return_value=error_dialog),
        ):
            await app.export_transcript_pdf_handler(object())

        app._main_window.dialog.assert_awaited_once_with(error_dialog)

    async def test_render_pending_delegates_callbacks(self):
        app = bare_app()
        app.render_coordinator = MagicMock()
        app.render_coordinator.run = AsyncMock()

        await app._render_pending_plots()

        app.render_coordinator.run.assert_awaited_once_with(
            app._apply_rendered_chart,
            app._handle_render_error,
        )

    async def test_dialog_helpers_use_toga_dialogs(self):
        app = bare_app()
        app.session = SimpleNamespace(path=TestResources.path_short_transcript)
        app.file_format = SimpleNamespace(value="SVG")
        selected = TestResources.path_short_transcript
        app._main_window = SimpleNamespace(dialog=AsyncMock(return_value=selected))
        open_dialog = object()
        save_dialog = object()

        with patch.object(TogaApp.toga, "OpenFileDialog", return_value=open_dialog):
            self.assertEqual(await app._get_path(), selected)
        app._main_window.dialog.assert_awaited_with(open_dialog)

        app._main_window.dialog.reset_mock()
        with patch.object(
            TogaApp.toga, "SaveFileDialog", return_value=save_dialog
        ) as save_dialog_type:
            self.assertEqual(
                await app._get_save_path(),
                selected.with_suffix(".svg"),
            )
        save_dialog_type.assert_called_once_with(
            "Save file",
            suggested_filename=selected.stem + ".svg",
            file_types=["svg"],
        )
        app._main_window.dialog.assert_awaited_with(save_dialog)

        app._main_window.dialog.reset_mock()
        with patch.object(
            TogaApp.toga, "SaveFileDialog", return_value=save_dialog
        ) as transcript_dialog_type:
            self.assertEqual(
                await app._get_transcript_pdf_path(),
                selected.with_suffix(".pdf"),
            )
        transcript_dialog_type.assert_called_once_with(
            "Export transcript PDF",
            suggested_filename=f"{selected.stem}_transcript.pdf",
            file_types=["pdf"],
        )
        app._main_window.dialog.assert_awaited_with(save_dialog)

        app.session.path = None
        self.assertIsNone(await app._get_save_path())
        self.assertIsNone(await app._get_transcript_pdf_path())


class TestTogaAppIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary_directory = tempfile.TemporaryDirectory()
        history = pathlib.Path(cls.temporary_directory.name) / "history.txt"
        cls.app = TogaApp.ConversationalSpaceMapAppToga(
            "ConversationalSpaceMapApp",
            "ch.manuelbieri.conversationalspacemapapp.tests",
            history_repository=FileHistoryRepository(history),
        )

        async def start_app():
            cls.app.startup()

        cls.app.loop.run_until_complete(start_app())

    @classmethod
    def tearDownClass(cls):
        cls.temporary_directory.cleanup()

    def test_startup_builds_native_toga_views(self):
        self.assertIsInstance(self.app, toga.App)
        self.assertIsInstance(self.app.transcript, toga.WebView)
        self.assertIsInstance(self.app.transcript_export_button, toga.Button)
        self.assertIsInstance(self.app.about_renderer.render(), str)
        self.assertIsInstance(self.app.chart, toga.Canvas)
        self.assertIsInstance(self.app.statistics, toga.ScrollContainer)
        self.assertGreaterEqual(len(self.app.participants_layout.content), 1)
        self.assertEqual(
            self.app._general_participants_layout.style.align_items,
            TogaApp.CENTER,
        )

    def test_load_plot_and_role_aware_transcript(self):
        async def exercise_app():
            self.app._set_path(TestResources.path_multiple_speaker_transcript)
            await self.app._plot_task
            first, second, *_ = self.app.session.participants
            first_widget = self.app.participant_widgets[first.speaker].role
            second_widget = self.app.participant_widgets[second.speaker].role
            first_widget.value = Constants.Participant.Interviewer
            second_widget.value = Constants.Participant.Interviewee
            self.app._participant_role_handler(first.speaker, first_widget)
            self.app._participant_role_handler(second.speaker, second_widget)
            await self.app._plot_task

        self.app.loop.run_until_complete(exercise_app())

        self.assertIsNotNone(self.app._chart_image_action)
        self.assertIsNotNone(self.app.map)
        transcript_content = self.app._transcript_html()
        self.assertIn('class="message-row interviewer"', transcript_content)
        self.assertIn('class="message-row interviewee"', transcript_content)
        self.assertEqual(len(self.app.participant_widgets), 3)
        self.assertEqual(len(self.app.statistics.content.children), 7)
        self.assertTrue(
            all(
                binding.role.parent.style.align_items == TogaApp.CENTER
                for binding in self.app.participant_widgets.values()
            )
        )

    def test_change_color_palette(self):
        async def exercise_app():
            self.app._set_path(TestResources.path_multiple_speaker_transcript)
            await self.app._plot_task
            self.app.color_palette.value = StylePicker.Palette.Pastel
            self.app._set_participants_color_selection(self.app.color_palette)

        self.app.loop.run_until_complete(exercise_app())

        for binding in self.app.participant_widgets.values():
            self.assertEqual(
                [
                    self.app._color_button_hex(button).lower()
                    for button in binding.color_buttons
                ],
                [color.lower() for color in StylePicker.Palette.Pastel.value],
            )


class TestTogaEntrypoint(unittest.TestCase):
    def test_toga_main_uses_briefcase_identity(self):
        app = MagicMock()
        with patch.object(
            TogaApp,
            "ConversationalSpaceMapAppToga",
            return_value=app,
        ) as app_type:
            self.assertIs(TogaApp.main(), app)

        app_type.assert_called_once_with(
            "ConversationalSpaceMapApp",
            "ch.manuelbieri.conversationalspacemapapp",
        )

    def test_main_launches_toga(self):
        import conversationalspacemapapp.__main__ as entrypoint

        app = MagicMock()
        with patch.object(entrypoint.TogaApp, "main", return_value=app):
            entrypoint.main()

        app.main_loop.assert_called_once_with()
