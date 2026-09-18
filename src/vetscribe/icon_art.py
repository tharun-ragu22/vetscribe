"""Vector-ish artwork for the VetScribe logo: a cute dog holding a notepad.

The tray icon encodes pipeline state through the colour of the dog's collar
(green = idle, red = recording, yellow = processing), so the drawing takes an
``accent`` colour. Everything is drawn on a 4x supersampled canvas and then
downscaled with LANCZOS, which makes the small tray/taskbar renderings far
crisper than drawing straight at 16-32px would.

The collar is drawn as a flat-filled band; ``COLLAR_SAMPLE`` (in 0..1 canvas
coordinates) points at a spot deep inside it whose colour survives the
downscale unchanged, which is what the tray-icon state tests sample.
"""

from PIL import Image, ImageDraw

# A point inside the solid collar band, in fractions of the icon's width/height.
# Sampling here yields exactly the accent colour (no anti-aliasing, nothing
# drawn on top), which the state-colour tests rely on.
COLLAR_SAMPLE = (0.34, 0.80)

_SUPERSAMPLE = 4

# Palette for a friendly golden/tan dog.
_FUR = (240, 200, 130, 255)
_FUR_DARK = (206, 158, 92, 255)
_EAR = (176, 122, 66, 255)
_MUZZLE = (252, 232, 196, 255)
_NOSE = (60, 44, 40, 255)
_EYE = (56, 42, 38, 255)
_WHITE = (255, 255, 255, 255)
_PAPER = (250, 250, 248, 255)
_PAPER_EDGE = (208, 208, 200, 255)
_LINE = (150, 176, 210, 255)
_OUTLINE = (108, 74, 44, 255)


def _rgba(color):
    """Accept a PIL colour name or an RGB(A) tuple, return an RGBA tuple."""
    if isinstance(color, str):
        img = Image.new("RGBA", (1, 1), color)
        return img.getpixel((0, 0))
    if len(color) == 3:
        return (*color, 255)
    return color


def render_logo(size: int, accent="green") -> Image.Image:
    """Render the dog-with-notepad logo at ``size`` px with an accent collar."""
    accent = _rgba(accent)
    s = size * _SUPERSAMPLE
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def box(x0, y0, x1, y1):
        return (x0 * s, y0 * s, x1 * s, y1 * s)

    lw = max(1, round(s * 0.012))

    # --- Ears (drawn first so the head overlaps their inner edge) ---
    d.ellipse(box(0.06, 0.24, 0.30, 0.62), fill=_EAR, outline=_OUTLINE, width=lw)
    d.ellipse(box(0.70, 0.24, 0.94, 0.62), fill=_EAR, outline=_OUTLINE, width=lw)

    # --- Collar band (behind the head, state-coloured) ---
    d.rounded_rectangle(
        box(0.16, 0.62, 0.84, 0.84), radius=s * 0.05, fill=accent, outline=_OUTLINE, width=lw
    )
    # A little tag hanging off the collar.
    d.ellipse(box(0.46, 0.80, 0.54, 0.90), fill=(255, 214, 92, 255), outline=_OUTLINE, width=lw)

    # --- Head ---
    d.ellipse(box(0.16, 0.14, 0.84, 0.72), fill=_FUR, outline=_OUTLINE, width=lw)

    # --- Muzzle ---
    d.ellipse(box(0.34, 0.40, 0.66, 0.68), fill=_MUZZLE, outline=_OUTLINE, width=lw)

    # --- Eyes (with highlight) ---
    for cx in (0.37, 0.63):
        d.ellipse(box(cx - 0.055, 0.32, cx + 0.055, 0.44), fill=_EYE)
        d.ellipse(box(cx - 0.01, 0.34, cx + 0.03, 0.38), fill=_WHITE)

    # --- Nose ---
    d.ellipse(box(0.44, 0.47, 0.56, 0.56), fill=_NOSE)
    d.ellipse(box(0.465, 0.485, 0.5, 0.515), fill=(120, 100, 96, 255))

    # --- Notepad, tucked at the lower-right as if held up ---
    pad = box(0.58, 0.58, 0.96, 0.95)
    d.rounded_rectangle(pad, radius=s * 0.02, fill=_PAPER, outline=_PAPER_EDGE, width=lw)
    # Spiral binding across the top.
    for i in range(5):
        x = 0.62 + i * 0.07
        d.line((x * s, 0.565 * s, x * s, 0.615 * s), fill=_OUTLINE, width=max(1, round(s * 0.01)))
    # Ruled lines.
    for j in range(4):
        y = 0.68 + j * 0.06
        d.line((0.63 * s, y * s, 0.91 * s, y * s), fill=_LINE, width=max(1, round(s * 0.012)))

    return img.resize((size, size), Image.LANCZOS)
