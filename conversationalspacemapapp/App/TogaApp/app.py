import asyncio
import pathlib
import platform
import traceback
from collections.abc import Callable
from dataclasses import dataclass

import toga
from toga.constants import BOLD, CENTER, COLUMN
from toga.style import Pack

from conversationalspacemapapp.App.AboutRenderer import AboutRenderer
from conversationalspacemapapp.App.Conversation import (
    ConversationSession,
    PlotSettings,
)
from conversationalspacemapapp.App.FileHistory import FileHistoryRepository
from conversationalspacemapapp.App.PlotRendering import (
    LatestPlotRenderCoordinator,
    MatplotlibChartRenderer,
    RenderedChart,
)
from conversationalspacemapapp.App.TranscriptRenderer import TranscriptRenderer
from conversationalspacemapapp.App.TranscriptPdfRenderer import TranscriptPdfRenderer
from conversationalspacemapapp.App.TranscriptPresentation import (
    TranscriptPresentation,
)
from conversationalspacemapapp.Plotter import StylePicker
from conversationalspacemapapp.Types import Constants, Data


@dataclass(slots=True)
class ParticipantWidgets:
    role: toga.Selection
    label: toga.TextInput
    color: toga.TextInput
    color_buttons: tuple[toga.Button, ...]


@dataclass(frozen=True, slots=True)
class StatisticCardData:
    title: str
    value: str
    detail: str
    color: str


class ConversationalSpaceMapAppToga(toga.App):
    """Toga composition root for the conversational-space-map application."""

    save_file_formats = ["PDF", "SVG", "PNG"]
    export_extensions = {
        "PDF": ".pdf",
        "SVG": ".svg",
        "PNG": ".png",
    }
    default_padding = 5
    default_flex = 1
    default_chart_width = 500
    default_chart_height = 400

    def __init__(
        self,
        name: str,
        app_id: str,
        *,
        session: ConversationSession | None = None,
        history_repository: FileHistoryRepository | None = None,
        about_renderer: AboutRenderer | None = None,
        transcript_renderer: TranscriptRenderer | None = None,
        transcript_pdf_renderer: TranscriptPdfRenderer | None = None,
        chart_renderer: MatplotlibChartRenderer | None = None,
        render_coordinator: LatestPlotRenderCoordinator | None = None,
    ) -> None:
        default_color = StylePicker.Palette.available_palettes()[0].value[0]
        self.session = session or ConversationSession(default_color=default_color)
        self._history_repository = history_repository
        self.about_renderer = about_renderer or AboutRenderer()
        self.transcript_renderer = transcript_renderer or TranscriptRenderer()
        self.transcript_pdf_renderer = (
            transcript_pdf_renderer or TranscriptPdfRenderer()
        )
        self.chart_renderer = chart_renderer or MatplotlibChartRenderer()
        self.render_coordinator = render_coordinator or LatestPlotRenderCoordinator(
            self.chart_renderer
        )

        self.map = None
        self.participant_widgets: dict[str, ParticipantWidgets] = {}
        self._chart_image_action = None
        self._chart_width = self.default_chart_width
        self._chart_height = self.default_chart_height
        self._plot_task = None
        super().__init__(formal_name=name, app_id=app_id)

    @property
    def history_repository(self) -> FileHistoryRepository:
        if self._history_repository is None:
            legacy_path = pathlib.Path(__file__).parents[1] / "assets" / "history.txt"
            self._history_repository = FileHistoryRepository(
                self.paths.data / "history.txt",
                legacy_path=legacy_path,
            )
        return self._history_repository

    @property
    def parser(self):
        """Compatibility view of the parser owned by the session."""
        return self.session.parser

    @property
    def path(self) -> pathlib.Path | None:
        return self.session.path

    @property
    def has_path(self) -> bool:
        return self.path is not None and self.path.is_file()

    @property
    def path_filename(self) -> str | None:
        return self.path.name if self.has_path else None

    @property
    def has_parser(self) -> bool:
        return self.session.is_loaded

    def path_as_str(self) -> str:
        return self.path.as_posix() if self.has_path else ""

    def startup(self) -> None:
        self._create_window()

    def _create_window(self) -> None:
        home = self._create_home_layout()
        transcript = self._create_transcript_layout()
        about = self._create_about_layout()
        tab_menu = self._create_tab_menu(
            tabs=[["Home", home], ["Transcript", transcript], ["About", about]]
        )
        self._set_window(tab_menu)

    def _set_window(self, tab_menu: toga.OptionContainer) -> None:
        self.main_window = toga.MainWindow()
        self.main_window.content = tab_menu
        self.main_window.size = toga.Size(width=1300, height=1000)
        self.main_window.show()

    def _create_tab_menu(self, tabs) -> toga.OptionContainer:
        main_tab = toga.OptionContainer(content=tabs)
        self._set_widget_style(main_tab)
        self._set_transparent_background(main_tab)
        return main_tab

    def _create_home_layout(self) -> toga.Box:
        return self._set_home_window(
            self._create_plot_settings_layout(),
            self._create_initial_participants_layout(),
            self._create_info_layout(),
            self._create_chart(),
        )

    def _create_about_layout(self) -> toga.WebView:
        description = toga.WebView(content=self.about_renderer.render())
        self._set_widget_style(description)
        self._set_transparent_background(description)
        return description

    def _create_transcript_layout(self) -> toga.Box:
        self.transcript_export_button = self._button_factory(
            "Export transcript PDF",
            on_press=self.export_transcript_pdf_handler,
            enabled=self.has_parser,
        )
        self._set_widget_style(self.transcript_export_button, flex=0)
        self.transcript = toga.WebView(content=self._transcript_html())
        self._set_widget_style(self.transcript)
        self._set_transparent_background(self.transcript)
        toolbar = toga.Box(
            children=[self.transcript_export_button],
            style=Pack(align_items=CENTER),
        )
        return toga.Box(
            children=[toolbar, self.transcript],
            style=Pack(direction=COLUMN),
        )

    def _transcript_html(self) -> str:
        return self.transcript_renderer.render(
            self.session.utterances,
            roles_by_speaker=self.session.roles_by_speaker(),
            colors_by_speaker=self.session.colors_by_speaker(),
            labels_by_speaker=self.session.labels_by_speaker(),
        )

    def _set_transcript(self) -> None:
        self.transcript.content = self._transcript_html()

    @staticmethod
    def _build_transcript_html(
        utterances: list[Data.Utterance],
        roles_by_speaker: dict[str, Constants.Participant] | None = None,
    ) -> str:
        """Backward-compatible facade for callers that only need HTML rendering."""
        return TranscriptRenderer().render(utterances, roles_by_speaker)

    @staticmethod
    def _set_home_window(plot_settings, participants, label, chart) -> toga.Box:
        return toga.Box(
            children=[plot_settings, participants, label, chart],
            style=Pack(direction=COLUMN),
        )

    def _create_plot_settings_layout(self) -> toga.Box:
        self.file_format = toga.Selection(items=self.save_file_formats)
        self._set_widget_style(self.file_format, flex=0)
        history_items = self.history_repository.load()
        self.path_input = toga.Selection(
            items=history_items,
            on_change=self._path_selection_handler,
        )
        self._set_widget_style(self.path_input, flex=1)
        self.path_input.readonly = True

        self.button = self._button_factory("📄", on_press=self.open_handler)
        self._set_widget_style(self.button, flex=0)
        self.clear_history_button = self._button_factory(
            "Clear history",
            on_press=self.clear_history_handler,
            enabled=bool(history_items),
        )
        self._set_widget_style(self.clear_history_button, flex=0)
        self.plot = self._button_factory(
            "🖌",
            on_press=self.plot_handler,
            enabled=self.has_parser,
        )
        self._set_widget_style(self.plot, flex=0)
        self.save = self._button_factory(
            "💾",
            on_press=self.save_handler,
            enabled=False,
        )
        self._set_widget_style(self.save, flex=0)
        return toga.Box(
            children=[
                self.path_input,
                self.button,
                self.clear_history_button,
                self.plot,
                self.file_format,
                self.save,
            ],
            style=Pack(align_items=CENTER),
        )

    def _create_initial_participants_layout(self) -> toga.OptionContainer:
        self.participants_layout = toga.OptionContainer(
            content=[("General", self._create_general_participants_layout())],
            style=Pack(margin=self.default_padding, height=60),
        )
        return self.participants_layout

    def _create_general_participants_layout(self) -> toga.Box:
        self.color_palette = self._set_widget_style(
            toga.Selection(
                items=StylePicker.Palette.available_palettes(),
                on_change=self._set_participants_color_selection,
            )
        )
        self.plot_title = self._set_widget_style(
            toga.Switch(text="Title", on_change=self.plot_handler, value=True),
            flex=0,
        )
        self.plot_title_input = self._set_widget_style(
            toga.TextInput(placeholder="Title", on_change=self.plot_handler),
            flex=2,
        )
        self.interviewer_label_input = self._set_widget_style(
            toga.TextInput(
                value="Interviewer",
                placeholder="Interviewer label",
                on_change=self.plot_handler,
            )
        )
        self.interviewee_label_input = self._set_widget_style(
            toga.TextInput(
                value="Interviewee",
                placeholder="Interviewee label",
                on_change=self.plot_handler,
            )
        )
        self.plot_legend = self._set_widget_style(
            toga.Switch(text="Legend", on_change=self.plot_handler, value=True),
            flex=0,
        )
        self.plot_labels = self._set_widget_style(
            toga.Switch(text="Labels", on_change=self.plot_handler, value=True),
            flex=0,
        )
        self.plot_yaxis = self._set_widget_style(
            toga.Switch(text="Y-Axis", on_change=self.plot_handler, value=True),
            flex=0,
        )
        self.plot_xaxis = self._set_widget_style(
            toga.Switch(text="X-Axis", on_change=self.plot_handler, value=True),
            flex=0,
        )
        self.plot_grid = self._set_widget_style(
            toga.Switch(text="Grid", on_change=self.plot_handler, value=True),
            flex=0,
        )
        self._general_participants_layout = toga.Box(
            children=[
                self.plot_title_input,
                self.plot_title,
                self.plot_labels,
                self.interviewer_label_input,
                self.interviewee_label_input,
                self.plot_yaxis,
                self.plot_xaxis,
                self.plot_legend,
                self.plot_grid,
                self.color_palette,
            ],
            style=Pack(align_items=CENTER),
        )
        return self._general_participants_layout

    def _create_info_layout(self) -> toga.ScrollContainer:
        self.statistics = toga.ScrollContainer(
            horizontal=True,
            vertical=False,
            content=self._build_statistics_layout(),
            style=Pack(height=104, flex=0),
        )
        self._set_widget_style(self.statistics, flex=0)
        return self.statistics

    def _set_info_layout(self) -> None:
        self.statistics.content = self._build_statistics_layout()

    def _statistics_card_data(self) -> tuple[StatisticCardData, ...]:
        if not self.has_parser:
            return ()
        statistics = self.session.statistics()
        cards = [
            StatisticCardData(
                title="Total words",
                value=f"{statistics.total_words:,}",
                detail="across transcript",
                color="#E2E8F0",
            ),
            StatisticCardData(
                title="Total utterances",
                value=f"{statistics.total_utterances:,}",
                detail="speaker turns",
                color="#E2E8F0",
            ),
            StatisticCardData(
                title="Speakers",
                value=f"{statistics.speaker_count:,}",
                detail="identified",
                color="#E2E8F0",
            ),
            StatisticCardData(
                title="Average utterance",
                value=f"{statistics.average_words_per_utterance:.1f} words",
                detail="per utterance",
                color="#E2E8F0",
            ),
        ]
        cards.extend(
            StatisticCardData(
                title=participant.label,
                value=(
                    f"{statistics.words_by_participant.get(participant.speaker, 0):,} "
                    f"words · {statistics.percentage_for(participant.speaker):.1f}%"
                ),
                detail=self._participant_statistics_detail(
                    statistics,
                    participant.speaker,
                ),
                color=participant.color,
            )
            for participant in self.session.participants
        )
        return tuple(cards)

    @staticmethod
    def _participant_statistics_detail(statistics, speaker: str) -> str:
        utterances = statistics.utterances_for(speaker)
        noun = "utterance" if utterances == 1 else "utterances"
        return (
            f"{utterances:,} {noun} · "
            f"{statistics.average_words_for(speaker):.1f} avg words · "
            f"{statistics.longest_utterance_for(speaker):,} max words"
        )

    def _build_statistics_layout(self) -> toga.Box:
        return toga.Box(
            children=[
                self._create_statistic_card(card)
                for card in self._statistics_card_data()
            ],
            style=Pack(align_items=CENTER, gap=8),
        )

    @staticmethod
    def _create_statistic_card(card: StatisticCardData) -> toga.Box:
        accent = toga.Box(
            style=Pack(
                width=7,
                height=84,
                background_color=card.color,
            )
        )
        content = toga.Box(
            children=[
                toga.Label(
                    card.title,
                    style=Pack(
                        color="#000000",
                        font_size=10,
                        margin=(8, 10, 0, 10),
                    ),
                ),
                toga.Label(
                    card.value,
                    style=Pack(
                        color="#000000",
                        font_size=14,
                        font_weight=BOLD,
                        margin=(1, 10, 0, 10),
                    ),
                ),
                toga.Label(
                    card.detail,
                    style=Pack(
                        color="#475569",
                        font_size=9,
                        margin=(1, 10, 8, 10),
                    ),
                ),
            ],
            style=Pack(direction=COLUMN),
        )
        return toga.Box(
            children=[accent, content],
            style=Pack(
                height=84,
                background_color="#FFFFFF",
                align_items=CENTER,
            ),
        )

    def _create_chart(self) -> toga.Canvas:
        self.chart = toga.Canvas(style=Pack(flex=1), on_resize=self._resize_chart)
        self._set_widget_style(self.chart)
        return self.chart

    def _create_participants_layout(self) -> None:
        self._clear_participants_layout()
        for participant in self.session.participants:
            self.participants_layout.content.append(
                participant.speaker,
                self._create_participant_layout(participant.speaker),
            )

    def _clear_participants_layout(self) -> None:
        self.participants_layout.current_tab = 0
        for _ in range(1, len(self.participants_layout.content)):
            self.participants_layout.content.remove(1)
        self.participant_widgets.clear()

    def _create_participant_layout(self, speaker: str) -> toga.Box:
        participant = self.session.participant(speaker)
        role = toga.Selection(
            items=Constants.Participant,
            value=participant.role,
            on_change=lambda widget, name=speaker: self._participant_role_handler(
                name, widget
            ),
        )
        self._set_widget_style(role)
        label = toga.TextInput(
            value=participant.label,
            placeholder="Speaker name",
            on_change=lambda widget, name=speaker: self._participant_label_handler(
                name, widget
            ),
        )
        self._set_widget_style(label)
        color = toga.TextInput(value=participant.color, readonly=True)
        self._set_widget_style(color, flex=0)

        color_buttons: list[toga.Button] = []
        for palette_color in self.color_palette.value.value:
            color_button = self._set_widget_style(
                toga.Button(
                    "   ",
                    style=Pack(background_color=palette_color),
                    on_press=lambda widget, name=speaker, target=color: (
                        self._participant_color_handler(name, target, widget)
                    ),
                ),
                flex=0,
            )
            color_buttons.append(color_button)

        self.participant_widgets[speaker] = ParticipantWidgets(
            role=role,
            label=label,
            color=color,
            color_buttons=tuple(color_buttons),
        )
        return toga.Box(
            children=[role, label, color, *color_buttons],
            style=Pack(align_items=CENTER),
        )

    def _participant_role_handler(self, speaker: str, widget: toga.Selection) -> None:
        self.session.set_participant_role(speaker, widget.value)
        self.plot_handler(widget)
        self._set_transcript()

    def _participant_label_handler(self, speaker: str, widget: toga.TextInput) -> None:
        self.session.set_participant_label(speaker, widget.value)
        self.plot_handler(widget)
        self._set_transcript()

    def _participant_color_handler(
        self,
        speaker: str,
        color_widget: toga.TextInput,
        color_button: toga.Button,
    ) -> None:
        color = self._color_button_hex(color_button)
        color_widget.value = color
        self.session.set_participant_color(speaker, color)
        self.plot_handler(color_button)
        self._set_transcript()

    def _set_participants_color_selection(self, widget) -> None:
        for binding in self.participant_widgets.values():
            for index, color_button in enumerate(binding.color_buttons):
                color_button.style.background_color = self.color_palette.value.value[
                    index
                ]

    @staticmethod
    def _color_button_hex(color_button: toga.Button) -> str:
        color = color_button.style.background_color
        return StylePicker.ColorPicker.rgb2hex(color.r, color.g, color.b)

    def _read_plot_settings(self) -> PlotSettings:
        return PlotSettings(
            title=self.plot_title_input.value or "",
            show_title=self.plot_title.value,
            labels=self.plot_labels.value,
            interviewer_label=self.interviewer_label_input.value or "",
            interviewee_label=self.interviewee_label_input.value or "",
            yaxis=self.plot_yaxis.value,
            xaxis=self.plot_xaxis.value,
            legend=self.plot_legend.value,
            grid=self.plot_grid.value,
        )

    def plot_handler(self, widget=None) -> None:
        if not self.has_parser:
            return
        self.session.set_plot_settings(self._read_plot_settings())
        self._update_plot()
        self._set_info_layout()

    def _update_plot(self) -> None:
        if not self.has_parser:
            return
        self.render_coordinator.submit(
            self.session.build_plot_options(),
            self._chart_width,
            self._chart_height,
        )
        self.save.enabled = False
        if self._plot_task is None or self._plot_task.done():
            self._plot_task = self.loop.create_task(self._render_pending_plots())

    async def _render_pending_plots(self) -> None:
        await self.render_coordinator.run(
            self._apply_rendered_chart,
            self._handle_render_error,
        )

    def _apply_rendered_chart(self, result: RenderedChart) -> None:
        self._set_chart_image(result.image_data, result.width, result.height)
        self.map = result.plot
        self.save.enabled = True

    def _handle_render_error(self, error: Exception) -> None:
        traceback.print_exception(error)
        self.save.enabled = self.map is not None

    def _resize_chart(self, widget: toga.Canvas, width, height, **kwargs) -> None:
        width = round(width)
        height = round(height)
        if width < 1 or height < 1:
            return
        if width == self._chart_width and height == self._chart_height:
            return

        self._chart_width = width
        self._chart_height = height
        if self._chart_image_action is not None:
            self._chart_image_action.width = width
            self._chart_image_action.height = height
            widget.redraw()
        if self.has_parser:
            self._update_plot()

    def _set_chart_image(self, image_data: bytes, width: int, height: int) -> None:
        image = toga.Image(image_data)
        if self._chart_image_action is None:
            self._chart_image_action = self.chart.draw_image(
                image,
                x=0,
                y=0,
                width=width,
                height=height,
            )
        else:
            self._chart_image_action.image = image
            self._chart_image_action.width = width
            self._chart_image_action.height = height
            self.chart.redraw()

    async def open_handler(self, widget) -> None:
        path = await self._get_path()
        if path is not None and path.is_file():
            self._set_path(path)

    async def clear_history_handler(self, widget) -> None:
        dialog = toga.QuestionDialog(
            "Clear recent files?",
            "This removes the recent-file list but keeps the active transcript open.",
        )
        if not await self.main_window.dialog(dialog):
            return
        self.history_repository.clear()
        self.path_input.items = []
        self.clear_history_button.enabled = False

    async def _get_path(self) -> pathlib.Path | None:
        dialog = toga.OpenFileDialog("Open file", file_types=["txt"])
        return await self.main_window.dialog(dialog)

    def _path_selection_handler(self, widget) -> None:
        path = widget.value
        if path is not None and path.is_file() and path != self.session.path:
            self._load_path(path)

    def _set_path(self, path: pathlib.Path) -> None:
        path = pathlib.Path(path)
        if not path.is_file():
            raise FileNotFoundError(path)
        try:
            self.path_input.value = path
        except ValueError:
            self.path_input.items.append(path)
            self.path_input.value = path
        if self.session.path != path:
            self._load_path(path)

    def _load_path(self, path: pathlib.Path) -> None:
        self.session.load(path)
        self._create_participants_layout()
        self._set_plot_title()
        self.session.set_plot_settings(self._read_plot_settings())
        self._update_plot()
        self._set_info_layout()
        self._set_transcript()
        self.history_repository.add(path)
        self.clear_history_button.enabled = True
        self.plot.enabled = True
        self.transcript_export_button.enabled = True

    def _set_plot_title(self) -> None:
        if self.has_path:
            self.plot_title_input.value = "Conversational Space Map " + self.path.stem

    async def save_handler(self, widget) -> None:
        if not self.has_parser or self.map is None:
            return
        path = await self._get_save_path()
        if path is not None:
            self.map.save(path)

    async def export_transcript_pdf_handler(self, widget) -> None:
        if not self.has_parser:
            return
        path = await self._get_transcript_pdf_path()
        if path is None:
            return

        messages = TranscriptPresentation.build(
            self.session.utterances,
            self.session.roles_by_speaker(),
            self.session.colors_by_speaker(),
            self.session.labels_by_speaker(),
        )
        try:
            await asyncio.to_thread(
                self.transcript_pdf_renderer.save,
                path,
                messages,
                title=self._transcript_pdf_title(),
            )
        except Exception as error:
            traceback.print_exception(error)
            await self.main_window.dialog(
                toga.ErrorDialog(
                    "Could not export transcript",
                    str(error),
                )
            )

    async def _get_transcript_pdf_path(self) -> pathlib.Path | None:
        if not self.has_path:
            return None
        dialog = toga.SaveFileDialog(
            "Export transcript PDF",
            suggested_filename=f"{self.path.stem}_transcript.pdf",
            file_types=["pdf"],
        )
        path = await self.main_window.dialog(dialog)
        if path is None:
            return None
        return pathlib.Path(path).with_suffix(".pdf")

    def _transcript_pdf_title(self) -> str:
        if not self.has_path:
            return "Transcript"
        return f"Transcript - {self.path.stem}"

    async def _get_save_path(self) -> pathlib.Path | None:
        if not self.has_path:
            return None
        extension = self._selected_export_extension()
        dialog = toga.SaveFileDialog(
            "Save file",
            suggested_filename=self.path.stem + extension,
            file_types=[extension.removeprefix(".")],
        )
        path = await self.main_window.dialog(dialog)
        if path is None:
            return None
        return self._normalize_export_path(path, extension)

    def _selected_export_extension(self) -> str:
        selected_format = str(self.file_format.value or "PDF").upper()
        return self.export_extensions.get(selected_format, ".pdf")

    @staticmethod
    def _normalize_export_path(
        path: pathlib.Path | str,
        extension: str,
    ) -> pathlib.Path:
        extension = extension.lower()
        if extension not in ConversationalSpaceMapAppToga.export_extensions.values():
            raise ValueError(f"Unsupported export extension: {extension}")
        return pathlib.Path(path).with_suffix(extension)

    def _button_factory(
        self,
        label: str,
        on_press: Callable,
        enabled: bool = True,
        padding: float | None = None,
        flex: float | None = None,
    ) -> toga.Button:
        button = toga.Button(label, on_press=on_press)
        button.enabled = enabled
        self._set_widget_style(button, padding=padding, flex=flex)
        return button

    @staticmethod
    def _set_default_widget_flex(widget: toga.Widget) -> toga.Widget:
        widget.style.flex = ConversationalSpaceMapAppToga.default_flex
        return widget

    @staticmethod
    def _set_default_widget_padding(widget: toga.Widget) -> toga.Widget:
        widget.style.margin = ConversationalSpaceMapAppToga.default_padding
        return widget

    @staticmethod
    def _set_widget_style(
        widget: toga.Widget,
        padding: float | None = None,
        flex: float | None = None,
    ) -> toga.Widget:
        if padding is None and flex is None:
            ConversationalSpaceMapAppToga._set_default_widget_flex(widget)
            ConversationalSpaceMapAppToga._set_default_widget_padding(widget)
        elif padding is None:
            ConversationalSpaceMapAppToga._set_default_widget_padding(widget)
            widget.style.flex = flex
        elif flex is None:
            ConversationalSpaceMapAppToga._set_default_widget_flex(widget)
            widget.style.margin = padding
        else:
            widget.style.margin = padding
            widget.style.flex = flex
        return widget

    @staticmethod
    def _set_transparent_background(widget) -> None:
        if "macOS" in platform.platform():
            widget.style.background_color = "transparent"


def main() -> ConversationalSpaceMapAppToga:
    return ConversationalSpaceMapAppToga(
        "ConversationalSpaceMapApp",
        "ch.manuelbieri.conversationalspacemapapp",
    )
