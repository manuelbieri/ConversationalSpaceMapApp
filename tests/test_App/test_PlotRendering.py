import asyncio
import struct
import threading
import unittest
from unittest.mock import MagicMock

from tests import utilities

from conversationalspacemapapp.App.PlotRendering import (
    LatestPlotRenderCoordinator,
    MatplotlibChartRenderer,
    RenderedChart,
)


class TestMatplotlibChartRenderer(unittest.TestCase):
    def test_render_returns_png_and_savable_plot(self):
        result = MatplotlibChartRenderer().render(
            utilities.get_plot_options(title="Background plot"),
            width=320,
            height=240,
        )

        self.assertIsInstance(result, RenderedChart)
        self.assertEqual(result.image_data[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(
            struct.unpack(">II", result.image_data[16:24]),
            (960, 720),
        )
        self.assertEqual(result.plot.fig.bbox.width, 960)
        self.assertEqual(result.plot.fig.bbox.height, 720)
        self.assertEqual(result.plot.fig.dpi, 300)
        self.assertEqual(result.plot.ax.get_title(), "Background plot")
        self.assertEqual((result.width, result.height), (320, 240))

    def test_invalid_dpi_and_dimensions_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "dpi must be positive"):
            MatplotlibChartRenderer(dpi=0)
        renderer = MatplotlibChartRenderer()
        for width, height in [(0, 10), (10, 0), (-1, 10)]:
            with self.subTest(width=width, height=height):
                with self.assertRaisesRegex(ValueError, "dimensions must be positive"):
                    renderer.render(utilities.get_plot_options(), width, height)


class TestLatestPlotRenderCoordinator(unittest.IsolatedAsyncioTestCase):
    async def test_rendering_runs_off_event_loop_and_applies_result(self):
        event_loop_thread = threading.get_ident()
        render_threads = []
        expected = RenderedChart(MagicMock(), b"image", 320, 240)
        renderer = MagicMock()

        def render(options, width, height):
            render_threads.append(threading.get_ident())
            return expected

        renderer.render.side_effect = render
        coordinator = LatestPlotRenderCoordinator(renderer)
        on_result = MagicMock()
        on_error = MagicMock()

        generation = coordinator.submit(utilities.get_plot_options(), 320, 240)
        await coordinator.run(on_result, on_error)

        self.assertEqual(generation, 1)
        self.assertEqual(coordinator.generation, 1)
        self.assertFalse(coordinator.has_pending)
        self.assertNotEqual(render_threads[0], event_loop_thread)
        on_result.assert_called_once_with(expected)
        on_error.assert_not_called()

    async def test_only_latest_pending_render_is_applied(self):
        first_started = threading.Event()
        release_first = threading.Event()
        renderer = MagicMock()

        def render(options, width, height):
            if width == 320:
                first_started.set()
                release_first.wait(timeout=2)
            return RenderedChart(
                MagicMock(name=str(width)), bytes(str(width), "ascii"), width, height
            )

        renderer.render.side_effect = render
        coordinator = LatestPlotRenderCoordinator(renderer)
        on_result = MagicMock()
        coordinator.submit(utilities.get_plot_options(title="first"), 320, 240)
        task = asyncio.create_task(coordinator.run(on_result, MagicMock()))
        await asyncio.to_thread(first_started.wait, 2)
        self.assertTrue(first_started.is_set())
        coordinator.submit(utilities.get_plot_options(title="latest"), 640, 480)
        release_first.set()
        await asyncio.wait_for(task, timeout=3)

        on_result.assert_called_once()
        self.assertEqual(on_result.call_args.args[0].width, 640)
        self.assertEqual(renderer.render.call_count, 2)

    async def test_current_failure_is_reported_and_old_failure_is_ignored(self):
        renderer = MagicMock()
        renderer.render.side_effect = RuntimeError("render failed")
        coordinator = LatestPlotRenderCoordinator(renderer)
        on_result = MagicMock()
        on_error = MagicMock()

        coordinator.submit(utilities.get_plot_options(), 320, 240)
        await coordinator.run(on_result, on_error)

        on_result.assert_not_called()
        on_error.assert_called_once()
        self.assertEqual(str(on_error.call_args.args[0]), "render failed")

    async def test_stale_failure_is_ignored_in_favor_of_latest_result(self):
        first_started = threading.Event()
        release_first = threading.Event()
        renderer = MagicMock()

        def render(options, width, height):
            if width == 320:
                first_started.set()
                release_first.wait(timeout=2)
                raise RuntimeError("stale failure")
            return RenderedChart(MagicMock(), b"latest", width, height)

        renderer.render.side_effect = render
        coordinator = LatestPlotRenderCoordinator(renderer)
        on_result = MagicMock()
        on_error = MagicMock()
        coordinator.submit(utilities.get_plot_options(), 320, 240)
        task = asyncio.create_task(coordinator.run(on_result, on_error))
        await asyncio.to_thread(first_started.wait, 2)
        coordinator.submit(utilities.get_plot_options(), 640, 480)
        release_first.set()

        await asyncio.wait_for(task, timeout=3)

        on_error.assert_not_called()
        on_result.assert_called_once()
        self.assertEqual(on_result.call_args.args[0].image_data, b"latest")

    async def test_cancellation_is_propagated(self):
        started = threading.Event()
        release = threading.Event()
        renderer = MagicMock()

        def render(options, width, height):
            started.set()
            release.wait(timeout=2)
            return RenderedChart(MagicMock(), b"image", width, height)

        renderer.render.side_effect = render
        coordinator = LatestPlotRenderCoordinator(renderer)
        coordinator.submit(utilities.get_plot_options(), 320, 240)
        task = asyncio.create_task(coordinator.run(MagicMock(), MagicMock()))
        await asyncio.to_thread(started.wait, 2)

        task.cancel()
        release.set()
        with self.assertRaises(asyncio.CancelledError):
            await task
