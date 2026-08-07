from matplotlib.axes import Axes
from matplotlib.figure import Figure

import conversationalspacemapapp.Types.Data as Data


class MapBarPlot:
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
        xlim_num = max(abs(utterance.words) for utterance in options.map) * 1.1
        for utterance in options.map:
            self.ax.barh(
                utterance.number,
                utterance.words
                * options.get_participant_type(utterance.speaker).constant,
                align="center",
                height=0.8,
                color=options.get_participant_color(utterance.speaker),
                label=options.get_participant_label(utterance.speaker),
            )
        index = [*range(1, len(options.map) + 1)]

        # Set x-axis
        self.ax.set_xlim([-xlim_num, xlim_num])
        if not options.xaxis:
            self.ax.set(xticklabels=[])
            self.ax.tick_params(bottom=False)

        # Set grid
        if options.grid:
            self.ax.xaxis.grid(
                True, linestyle="--", which="major", color="grey", alpha=0.25
            )

        # Set y-axis
        self.ax.set_ylim([-2, max(index) + 2])
        if options.yaxis:
            self.ax.set_yticks(index)
            self.ax.set_ylabel("Utterance (bottom = start of interview)")
        else:
            self.ax.set(yticklabels=[])
            self.ax.tick_params(left=False)

        # Set plot labels
        if options.show_title:
            self.ax.set_title(options.title)
        if options.labels:
            self.ax.text(
                xlim_num / 2,
                -1,
                options.interviewee_label + "'s words per utterance",
                horizontalalignment="center",
            )
            self.ax.text(
                -xlim_num / 2,
                -1,
                options.interviewer_label + "'s words per utterance",
                horizontalalignment="center",
            )
        if options.legend:
            self.ax.legend(loc="upper left")
            self._remove_duplicate_labels_legend()

    def _remove_duplicate_labels_legend(self):
        handles, labels = self.ax.get_legend_handles_labels()
        unique = [
            (h, l)
            for i, (h, l) in enumerate(zip(handles, labels))
            if l not in labels[:i]
        ]
        self.ax.legend(*zip(*unique))

    def save(self, filename: str):
        self.fig.savefig(filename, dpi=300)
