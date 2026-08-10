import asyncio
import io
from collections.abc import Callable
from dataclasses import dataclass

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from conversationalspacemapapp.Plotter.PlotMap import MapBarPlot
from conversationalspacemapapp.Types.Data import PlotOptions


@dataclass(frozen=True, slots=True)
class RenderedChart:
    plot: MapBarPlot
    image_data: bytes
    width: int
    height: int


class MatplotlibChartRenderer:
    layout_dpi = 100

    def __init__(self, *, dpi: int = 300) -> None:
        if dpi <= 0:
            raise ValueError("dpi must be positive")
        self.dpi = dpi

    def render(self, options: PlotOptions, width: int, height: int) -> RenderedChart:
        if width < 1 or height < 1:
            raise ValueError("chart dimensions must be positive")
        figure = Figure(
            figsize=(width / self.layout_dpi, height / self.layout_dpi),
            dpi=self.dpi,
        )
        canvas = FigureCanvasAgg(figure)
        plot = MapBarPlot(fig=figure)
        plot.plot(options=options)
        figure.tight_layout()

        image = io.BytesIO()
        canvas.print_png(image)
        return RenderedChart(plot, image.getvalue(), width, height)


@dataclass(frozen=True, slots=True)
class PlotRenderRequest:
    generation: int
    options: PlotOptions
    width: int
    height: int


class LatestPlotRenderCoordinator:
    """Serializes renders and only applies the newest submitted result."""

    def __init__(self, renderer: MatplotlibChartRenderer) -> None:
        self.renderer = renderer
        self._generation = 0
        self._pending: PlotRenderRequest | None = None

    @property
    def generation(self) -> int:
        return self._generation

    @property
    def has_pending(self) -> bool:
        return self._pending is not None

    def submit(self, options: PlotOptions, width: int, height: int) -> int:
        self._generation += 1
        self._pending = PlotRenderRequest(
            self._generation,
            options,
            width,
            height,
        )
        return self._generation

    async def run(
        self,
        on_result: Callable[[RenderedChart], None],
        on_error: Callable[[Exception], None],
    ) -> None:
        while self._pending is not None:
            request = self._pending
            self._pending = None
            try:
                result = await asyncio.to_thread(
                    self.renderer.render,
                    request.options,
                    request.width,
                    request.height,
                )
            except asyncio.CancelledError:
                raise
            except Exception as error:
                if request.generation == self._generation:
                    on_error(error)
                continue

            if request.generation == self._generation:
                on_result(result)
