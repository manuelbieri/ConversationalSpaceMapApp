import textwrap
from dataclasses import dataclass
from pathlib import Path

from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from matplotlib.patches import FancyBboxPatch

from conversationalspacemapapp.App.TranscriptPresentation import TranscriptMessage


@dataclass(frozen=True, slots=True)
class TranscriptPdfBlock:
    message: TranscriptMessage
    lines: tuple[str, ...]
    continued: bool
    final: bool
    height: float


class TranscriptPdfRenderer:
    """Render transcript chat messages into a print-ready, paginated PDF."""

    page_width = 595.28
    page_height = 841.89
    margin = 40.0
    header_height = 42.0
    footer_height = 26.0
    bubble_width = 370.0
    bubble_gap = 9.0
    bubble_padding = 9.0
    label_height = 14.0
    line_height = 13.0
    timestamp_height = 12.0
    fallback_colors = (
        "#006C63",
        "#176B35",
        "#185A88",
        "#8A3154",
        "#795B00",
        "#62419A",
        "#166C68",
        "#4F5B62",
    )

    def save(
        self,
        path: Path | str,
        messages: tuple[TranscriptMessage, ...],
        *,
        title: str,
    ) -> None:
        path = Path(path)
        if path.suffix.lower() != ".pdf":
            raise ValueError("Transcript export path must use the .pdf extension")

        pages = self.paginate(messages)
        with PdfPages(path) as pdf:
            metadata = pdf.infodict()
            metadata["Title"] = title
            metadata["Author"] = "ConversationalSpaceMapApp"
            metadata["Subject"] = "Interview transcript"
            for page_number, blocks in enumerate(pages, start=1):
                figure = self._render_page(
                    blocks,
                    title=title,
                    page_number=page_number,
                    page_count=len(pages),
                )
                pdf.savefig(figure)
                figure.clear()

    def paginate(
        self,
        messages: tuple[TranscriptMessage, ...],
    ) -> tuple[tuple[TranscriptPdfBlock, ...], ...]:
        if not messages:
            return ((),)

        page_capacity = (
            self.page_height - self.margin * 2 - self.header_height - self.footer_height
        )
        pages: list[list[TranscriptPdfBlock]] = [[]]
        remaining = page_capacity

        for message in messages:
            lines = list(self._wrap_text(message.text))
            first_chunk = True
            while lines:
                label_height = self.label_height if message.label else 0.0
                fixed_height = self.bubble_padding * 2 + label_height
                final_height = fixed_height
                if message.timestamp:
                    final_height += self.timestamp_height
                max_final_lines = int((remaining - final_height) // self.line_height)

                if len(lines) <= max_final_lines:
                    line_count = len(lines)
                    final = True
                else:
                    line_count = int((remaining - fixed_height) // self.line_height)
                    final = False

                if line_count < 1:
                    pages.append([])
                    remaining = page_capacity
                    continue

                chunk = tuple(lines[:line_count])
                del lines[:line_count]
                height = fixed_height + len(chunk) * self.line_height
                if final and message.timestamp:
                    height += self.timestamp_height
                block = TranscriptPdfBlock(
                    message=message,
                    lines=chunk,
                    continued=not first_chunk,
                    final=final,
                    height=height,
                )
                pages[-1].append(block)
                remaining -= height + self.bubble_gap
                first_chunk = False

        return tuple(tuple(page) for page in pages)

    def _wrap_text(self, text: str) -> tuple[str, ...]:
        wrapped: list[str] = []
        for paragraph in text.splitlines() or [""]:
            wrapped.extend(
                textwrap.wrap(
                    paragraph,
                    width=68,
                    replace_whitespace=False,
                    drop_whitespace=True,
                    break_long_words=True,
                    break_on_hyphens=False,
                )
                or [""]
            )
        return tuple(wrapped)

    def _render_page(
        self,
        blocks: tuple[TranscriptPdfBlock, ...],
        *,
        title: str,
        page_number: int,
        page_count: int,
    ) -> Figure:
        figure = Figure(
            figsize=(self.page_width / 72, self.page_height / 72),
            facecolor="#FFFFFF",
        )
        axes = figure.add_axes((0, 0, 1, 1))
        axes.set_xlim(0, self.page_width)
        axes.set_ylim(0, self.page_height)
        axes.axis("off")

        display_title = textwrap.shorten(
            " ".join(title.split()),
            width=64,
            placeholder="...",
        )
        axes.text(
            self.margin,
            self.page_height - self.margin,
            display_title,
            color="#000000",
            fontsize=13,
            fontweight="bold",
            ha="left",
            va="top",
        )
        header_line_y = self.page_height - self.margin - 24
        axes.plot(
            (self.margin, self.page_width - self.margin),
            (header_line_y, header_line_y),
            color="#E2E8F0",
            linewidth=0.8,
        )

        y = self.page_height - self.margin - self.header_height
        if not blocks:
            axes.text(
                self.page_width / 2,
                y - 30,
                "No transcript entries",
                color="#5D6B73",
                fontsize=11,
                ha="center",
                va="top",
            )

        for block in blocks:
            x = self._block_x(block.message.alignment)
            bottom = y - block.height
            bubble = FancyBboxPatch(
                (x, bottom),
                self.bubble_width,
                block.height,
                boxstyle="round,pad=0.0,rounding_size=6",
                linewidth=0.8,
                edgecolor="#D7DEE5",
                facecolor="#F8FAFC",
            )
            axes.add_patch(bubble)
            text_x = x + self.bubble_padding
            text_y = y - self.bubble_padding
            if block.message.label:
                label = block.message.label
                if block.continued:
                    label += " (continued)"
                axes.text(
                    text_x,
                    text_y,
                    label,
                    color=self._message_color(block.message),
                    fontsize=9,
                    fontweight="bold",
                    ha="left",
                    va="top",
                )
                text_y -= self.label_height

            axes.text(
                text_x,
                text_y,
                "\n".join(block.lines),
                color="#000000",
                fontsize=9.5,
                linespacing=self.line_height / 9.5,
                ha="left",
                va="top",
            )
            if block.final and block.message.timestamp:
                axes.text(
                    x + self.bubble_width - self.bubble_padding,
                    bottom + self.bubble_padding / 2,
                    block.message.timestamp.replace("\u2013", "-"),
                    color="#5D6B73",
                    fontsize=7.5,
                    ha="right",
                    va="bottom",
                )
            y = bottom - self.bubble_gap

        axes.text(
            self.page_width / 2,
            self.margin / 2,
            f"Page {page_number} of {page_count}",
            color="#5D6B73",
            fontsize=8,
            ha="center",
            va="center",
        )
        return figure

    def _block_x(self, alignment: str) -> float:
        if alignment == "interviewer":
            return self.margin
        if alignment == "interviewee":
            return self.page_width - self.margin - self.bubble_width
        return (self.page_width - self.bubble_width) / 2

    def _message_color(self, message: TranscriptMessage) -> str:
        return message.color or self.fallback_colors[message.speaker_index]
