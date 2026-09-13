import logging

import pystray
from PIL import Image, ImageDraw

from vetscribe.pipeline import PipelineState

logger = logging.getLogger("vetscribe.tray_app")

ICON_SIZE = 64

STATE_COLORS = {
    PipelineState.IDLE: "green",
    PipelineState.RECORDING: "red",
    PipelineState.PROCESSING: "yellow",
}


def build_icon_image(color: str) -> Image.Image:
    image = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((4, 4, ICON_SIZE - 4, ICON_SIZE - 4), fill=color)
    return image


class TrayApp:
    def __init__(self, pipeline, on_open_settings=None, on_show_note=None):
        self.pipeline = pipeline
        self.hotkey_listener = None
        self.offline_queue = None
        self.on_open_settings = on_open_settings or (lambda: None)
        self.on_show_note = on_show_note or (lambda soap_text: None)
        self.icon = pystray.Icon(
            "vetscribe",
            icon=build_icon_image(STATE_COLORS[PipelineState.IDLE]),
            title="VetScribe Assistant",
            menu=self._build_menu(),
        )

    def _build_menu(self):
        return pystray.Menu(
            pystray.MenuItem(self._status_text, None, enabled=False),
            pystray.MenuItem(
                "Open Last SOAP Note",
                lambda icon, item: self.open_last_note(),
                enabled=lambda item: self.pipeline.last_soap_text is not None,
            ),
            pystray.MenuItem("Settings", lambda icon, item: self.open_settings()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", lambda icon, item: self.quit()),
        )

    def _status_text(self, item):
        return f"Status: {self.pipeline.state.value.capitalize()}"

    def attach_hotkey_listener(self, hotkey_listener):
        self.hotkey_listener = hotkey_listener

    def attach_offline_queue(self, offline_queue):
        self.offline_queue = offline_queue

    def update_icon_for_state(self):
        self.icon.icon = build_icon_image(STATE_COLORS[self.pipeline.state])

    def on_hotkey_triggered(self):
        previous_state = self.pipeline.state
        self.pipeline.toggle_recording()
        logger.info(
            "state transition: %s -> %s", previous_state.value, self.pipeline.state.value
        )
        self.update_icon_for_state()

    def open_last_note(self):
        if self.pipeline.last_soap_text:
            self.on_show_note(self.pipeline.last_soap_text)

    def open_settings(self):
        self.on_open_settings()

    def quit(self):
        logger.info("shutting down")
        if self.hotkey_listener is not None:
            self.hotkey_listener.stop()
        if self.pipeline.state == PipelineState.RECORDING:
            self.pipeline.recorder.stop()
        if self.offline_queue is not None:
            self.offline_queue.stop()
        self.icon.stop()
