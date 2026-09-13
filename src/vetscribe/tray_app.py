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
