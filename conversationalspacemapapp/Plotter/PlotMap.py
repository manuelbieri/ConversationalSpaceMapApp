import math

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

import conversationalspacemapapp.Types.Data as Data


class MapBarPlot:
    background_color = "#FFFFFF"
    text_color = "#000000"
    muted_text_color = "#000000"
    grid_color = "#E2E8F0"
    zero_line_color = "#94A3B8"
    max_y_ticks = 12

    def __init__(
        self,
        fig: Figure,
        ax: Axes = None,
    ):
        self.fig = fig
        if ax is None:
            self.ax = self.fig.gca()
        else:
            self.ax = ax
        self.ax.clear()

    def plot(self, options: Data.PlotOptions):
        self._apply_modern_style()
        if not options.map:
            return

        xlim_num = max(abs(utterance.words) for utterance in options.map) * 1.1
        for utterance in options.map:
            self.ax.barh(
                utterance.number,
                utterance.words
                * options.get_participant_type(utterance.speaker).constant,
                align="center",
                height=0.64,
                color=options.get_participant_color(utterance.speaker),
                edgecolor="none",
                label=options.get_participant_label(utterance.speaker),
                zorder=3,
            )
        index = [*range(1, len(options.map) + 1)]

        # Set x-axis
        self.ax.set_xlim([-xlim_num, xlim_num])
        self.ax.xaxis.set_major_formatter(FuncFormatter(self._format_word_count))
        self.ax.tick_params(
            axis="x",
            bottom=False,
            labelbottom=options.xaxis,
            colors=self.muted_text_color,
            labelsize=9,
        )
        if not options.xaxis:
            self.ax.set_xlabel("")

        # Set grid
        if options.grid:
            self.ax.xaxis.grid(
                True,
                linestyle="-",
                linewidth=0.8,
                which="major",
                color=self.grid_color,
            )
        else:
            self.ax.xaxis.grid(False)
        self.ax.axvline(
            0,
            color=self.zero_line_color,
            linewidth=1.2,
            zorder=2,
        )

        # Set y-axis
        self.ax.set_ylim([0.25, max(index) + 0.75])
        self.ax.tick_params(
            axis="y",
            left=False,
            labelleft=options.yaxis,
            colors=self.muted_text_color,
            labelsize=9,
        )
        if options.yaxis:
            self.ax.set_yticks(self._get_utterance_ticks(len(index)))
            self.ax.set_ylabel(
                "Utterance · start at bottom",
                color=self.muted_text_color,
                fontsize=10,
                labelpad=10,
            )
        else:
            self.ax.set_yticks([])

        # Set plot labels
        if options.show_title:
            self.ax.set_title(
                options.title,
                loc="center",
                color=self.text_color,
                fontsize=15,
                fontweight="bold",
                pad=18,
            )
        if options.labels:
            self.ax.text(
                0.25,
                -0.08,
                options.interviewer_label + " · words per utterance",
                transform=self.ax.transAxes,
                horizontalalignment="center",
                verticalalignment="top",
                color=self.muted_text_color,
                fontsize=9,
                clip_on=False,
            )
            self.ax.text(
                0.75,
                -0.08,
                options.interviewee_label + " · words per utterance",
                transform=self.ax.transAxes,
                horizontalalignment="center",
                verticalalignment="top",
                color=self.muted_text_color,
                fontsize=9,
                clip_on=False,
            )
        if options.legend:
            self._add_legend()

    def _apply_modern_style(self):
        self.fig.patch.set_facecolor(self.background_color)
        self.ax.set_facecolor(self.background_color)
        self.ax.set_axisbelow(True)
        for spine in self.ax.spines.values():
            spine.set_visible(False)

    @staticmethod
    def _format_word_count(value, position):
        return f"{abs(value):g}"

    @classmethod
    def _get_utterance_ticks(cls, number_of_utterances: int) -> list[int]:
        if number_of_utterances <= cls.max_y_ticks:
            return list(range(1, number_of_utterances + 1))

        step = math.ceil((number_of_utterances - 1) / (cls.max_y_ticks - 1))
        ticks = list(range(1, number_of_utterances + 1, step))
        if ticks[-1] != number_of_utterances:
            ticks.append(number_of_utterances)
        return ticks

    def _add_legend(self):
        handles, labels = self.ax.get_legend_handles_labels()
        unique = {}
        for handle, label in zip(handles, labels):
            if label and not label.startswith("_") and label not in unique:
                unique[label] = handle

        if unique:
            legend = self.ax.legend(
                unique.values(),
                unique.keys(),
                loc="upper left",
                bbox_to_anchor=(1.01, 1),
                borderaxespad=0,
                frameon=False,
                fontsize=9,
            )
            for label in legend.get_texts():
                label.set_color(self.text_color)

    def save(self, filename: str):
        self.fig.savefig(
            filename,
            dpi=300,
            facecolor=self.fig.get_facecolor(),
            bbox_inches="tight",
        )
