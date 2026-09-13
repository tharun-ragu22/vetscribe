import pystray
from PIL import Image, ImageDraw

from vetscribe.pipeline import PipelineState

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
    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.icon = pystray.Icon(
            "vetscribe",
            icon=build_icon_image(STATE_COLORS[PipelineState.IDLE]),
            title="VetScribe Assistant",
        )

    def update_icon_for_state(self):
        self.icon.icon = build_icon_image(STATE_COLORS[self.pipeline.state])

    def on_hotkey_triggered(self):
        self.pipeline.toggle_recording()
        self.update_icon_for_state()
