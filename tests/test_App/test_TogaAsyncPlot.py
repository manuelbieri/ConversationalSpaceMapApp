import asyncio
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import utilities

import conversationalspacemapapp.App.TogaApp.app as TogaApp
import conversationalspacemapapp.Types.Data as Data


class TestTogaPlotRendering(unittest.TestCase):
    def setUp(self):
        parser = utilities.get_parser_mock()
        app = utilities.get_app_mock(parser=parser)
        self.options = Data.PlotOptions(app=app, title="Background plot")

    def test_draw_chart_returns_rendered_png_and_savable_plot(self):
        plot, image_data = TogaApp.ConversationalSpaceMapAppToga.draw_chart(
            self.options,
            width=320,
            height=240,
        )

        self.assertEqual(image_data[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(plot.fig.bbox.width, 320)
        self.assertEqual(plot.fig.bbox.height, 240)
        self.assertEqual(plot.ax.get_title(), "Background plot")

    def test_chart_image_action_is_reused(self):
        app = object.__new__(TogaApp.ConversationalSpaceMapAppToga)
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
        self.assertEqual(action.width, 640)
        self.assertEqual(action.height, 480)
        app.chart.redraw.assert_called_once_with()

    def test_resize_updates_live_canvas_and_queues_new_plot(self):
        app = object.__new__(TogaApp.ConversationalSpaceMapAppToga)
        app._chart_width = 500
        app._chart_height = 400
        app._chart_image_action = SimpleNamespace(width=500, height=400)
        app.parser = object()
        app._update_plot = MagicMock()
        canvas = MagicMock()

        app._resize_chart(canvas, width=800, height=600)

        self.assertEqual(app._chart_width, 800)
        self.assertEqual(app._chart_height, 600)
        self.assertEqual(app._chart_image_action.width, 800)
        self.assertEqual(app._chart_image_action.height, 600)
        canvas.redraw.assert_called_once_with()
        app._update_plot.assert_called_once_with()


class TestTogaPlotQueue(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.app = object.__new__(TogaApp.ConversationalSpaceMapAppToga)
        self.app.map = None
        self.app.save = SimpleNamespace(enabled=False)
        self.app._set_chart_image = MagicMock()

    async def test_rendering_runs_outside_event_loop_thread(self):
        event_loop_thread = threading.get_ident()
        render_threads = []

        def draw_chart(options, width, height):
            render_threads.append(threading.get_ident())
            return "plot", b"image"

        self.app.draw_chart = draw_chart
        self.app._plot_generation = 1
        self.app._pending_plot = (1, "options", 320, 240)

        await self.app._render_pending_plots()

        self.assertEqual(len(render_threads), 1)
        self.assertNotEqual(render_threads[0], event_loop_thread)
        self.assertEqual(self.app.map, "plot")
        self.app._set_chart_image.assert_called_once_with(b"image", 320, 240)
        self.assertTrue(self.app.save.enabled)

    async def test_only_latest_pending_render_is_applied(self):
        first_started = threading.Event()
        release_first = threading.Event()

        def draw_chart(options, width, height):
            if options == "first":
                first_started.set()
                release_first.wait(timeout=2)
            return options, options.encode()

        self.app.draw_chart = draw_chart
        self.app._plot_generation = 1
        self.app._pending_plot = (1, "first", 320, 240)
        render_task = asyncio.create_task(self.app._render_pending_plots())

        for _ in range(100):
            if first_started.is_set():
                break
            await asyncio.sleep(0.001)
        self.assertTrue(first_started.is_set())

        self.app._plot_generation = 2
        self.app._pending_plot = (2, "latest", 640, 480)
        release_first.set()
        await asyncio.wait_for(render_task, timeout=3)

        self.assertEqual(self.app.map, "latest")
        self.app._set_chart_image.assert_called_once_with(b"latest", 640, 480)

    async def test_render_failure_preserves_previous_plot(self):
        def draw_chart(options, width, height):
            raise RuntimeError("render failed")

        self.app.map = "existing plot"
        self.app.draw_chart = draw_chart
        self.app._plot_generation = 1
        self.app._pending_plot = (1, "options", 320, 240)

        with patch.object(TogaApp.traceback, "print_exc"):
            await self.app._render_pending_plots()

        self.assertEqual(self.app.map, "existing plot")
        self.app._set_chart_image.assert_not_called()
        self.assertTrue(self.app.save.enabled)


class TestTogaEntrypoint(unittest.TestCase):
    def test_main_launches_toga(self):
        import conversationalspacemapapp.__main__ as entrypoint

        app = MagicMock()
        with patch.object(entrypoint.TogaApp, "main", return_value=app):
            entrypoint.main()

        app.main_loop.assert_called_once_with()
