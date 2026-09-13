from unittest.mock import MagicMock

from vetscribe.pipeline import PipelineState
from vetscribe.tray_app import build_icon_image


def test_build_icon_image_returns_image_of_requested_color():
    image = build_icon_image("green")

    center_pixel = image.getpixel((image.width // 2, image.height // 2))
    assert center_pixel[:3] == (0, 128, 0)
