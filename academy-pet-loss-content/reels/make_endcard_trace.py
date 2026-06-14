"""
Generate a 5-second branded end card for Trace Memorial reels.
Uses Pillow for the image, FFmpeg to convert to video.
Output: reels/output/endcard-trace-memorial.mp4
"""

import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REELS_DIR = Path(__file__).parent
PNG_OUT = REELS_DIR / "output" / "endcard-trace-memorial.png"
VIDEO_OUT = REELS_DIR / "output" / "endcard-trace-memorial.mp4"
DURATION = 5
W, H = 720, 1280

# Brand colours (from design system HTML)
INK       = "#2d1f0e"
INK_MUTED = "#6b4c30"   # .memorial and secondary text

# C2 garden wash — 4-corner bilinear gradient
WASH_TL = "#f2c4d0"   # soft rose (top-left)
WASH_TR = "#c4d4f4"   # periwinkle blue (top-right)
WASH_BL = "#f4e8b8"   # warm golden (bottom-left)
WASH_BR = "#e4f0d4"   # soft sage (bottom-right)

# Nine-palette spectrum strip (thin line at bottom)
PALETTE = [
    "#f0b89a",  # Sunset
    "#e8c97a",  # Golden
    "#e8a0c0",  # Rose
    "#8ec8a0",  # Meadow
    "#80b8e8",  # Sky
    "#78aed0",  # Ocean
    "#b090d8",  # Lavender
    "#90b880",  # Forest
    "#b8b8b8",  # Monochrome
]
STRIP_H = 8  # thin spectrum line, as in the brand profile image

# Font paths
FONT_GEORGIA      = r"C:\Windows\Fonts\georgia.ttf"
FONT_GEORGIA_BOLD = r"C:\Windows\Fonts\georgiab.ttf"
FONT_SEGOE        = r"C:\Windows\Fonts\segoeui.ttf"
FONT_SEGOE_LIGHT  = r"C:\Windows\Fonts\segoeuil.ttf"


def hex_to_rgb(h: str) -> tuple:
    return (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16))


def bilinear_gradient(img: Image.Image, tl: str, tr: str, bl: str, br: str):
    """Fill img with a 4-corner bilinear colour gradient."""
    w, h = img.size
    pixels = img.load()
    tl_r, tl_g, tl_b = hex_to_rgb(tl)
    tr_r, tr_g, tr_b = hex_to_rgb(tr)
    bl_r, bl_g, bl_b = hex_to_rgb(bl)
    br_r, br_g, br_b = hex_to_rgb(br)
    for y in range(h):
        ty = y / (h - 1)
        for x in range(w):
            tx = x / (w - 1)
            r = int((1-tx)*(1-ty)*tl_r + tx*(1-ty)*tr_r + (1-tx)*ty*bl_r + tx*ty*br_r)
            g = int((1-tx)*(1-ty)*tl_g + tx*(1-ty)*tr_g + (1-tx)*ty*bl_g + tx*ty*br_g)
            b = int((1-tx)*(1-ty)*tl_b + tx*(1-ty)*tr_b + (1-tx)*ty*bl_b + tx*ty*br_b)
            pixels[x, y] = (r, g, b)


def draw_leaf(draw: ImageDraw.Draw, cx: int, cy: int, size: int, colour: str, stroke: int = 3):
    """Draw a vesica-piscis leaf mark (outline only, with centre line)."""
    r = size
    offset = int(r * 0.6)
    bbox_left  = [cx - r - offset, cy - r, cx + offset, cy + r]
    bbox_right = [cx - offset, cy - r, cx + r + offset, cy + r]
    draw.arc(bbox_left,  start=-60, end=60,   fill=colour, width=stroke)
    draw.arc(bbox_right, start=120, end=240,  fill=colour, width=stroke)
    top_y = cy - int(r * 0.87)
    bot_y = cy + int(r * 0.87)
    draw.line([(cx, top_y), (cx, bot_y)], fill=colour, width=stroke)


def make_endcard():
    PNG_OUT.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGB", (W, H))
    bilinear_gradient(img, WASH_TL, WASH_TR, WASH_BL, WASH_BR)
    draw = ImageDraw.Draw(img)

    # --- Leaf mark ---
    leaf_cx = W // 2
    leaf_cy = 370
    draw_leaf(draw, leaf_cx, leaf_cy, size=110, colour=INK, stroke=4)

    # --- Wordmark: trace.memorial ---
    try:
        font_trace    = ImageFont.truetype(FONT_GEORGIA_BOLD, 92)
        font_memorial = ImageFont.truetype(FONT_GEORGIA, 92)
    except Exception:
        font_trace = font_memorial = ImageFont.load_default()

    trace_text    = "trace"
    memorial_text = ".memorial"
    bb_t  = draw.textbbox((0, 0), trace_text,    font=font_trace)
    bb_m  = draw.textbbox((0, 0), memorial_text, font=font_memorial)
    trace_w = bb_t[2] - bb_t[0]
    total_w = trace_w + (bb_m[2] - bb_m[0])
    wm_x    = (W - total_w) // 2
    wm_y    = leaf_cy + 200

    draw.text((wm_x,           wm_y), trace_text,    font=font_trace,    fill=INK)
    draw.text((wm_x + trace_w, wm_y), memorial_text, font=font_memorial, fill=INK_MUTED)

    # --- Hairline divider ---
    div_y = wm_y + 130
    draw.line([(W // 2 - 110, div_y), (W // 2 + 110, div_y)], fill="#c8b89a", width=2)

    # --- Tagline ---
    try:
        font_tagline = ImageFont.truetype(FONT_GEORGIA, 44)
    except Exception:
        font_tagline = ImageFont.load_default()

    tagline = "A permanent home for their story."
    bb = draw.textbbox((0, 0), tagline, font=font_tagline)
    draw.text(((W - (bb[2] - bb[0])) // 2, div_y + 40), tagline, font=font_tagline, fill=INK)

    # --- Sub-label ---
    try:
        font_label = ImageFont.truetype(FONT_SEGOE, 22)
    except Exception:
        font_label = ImageFont.load_default()

    label = "MEMORIAL PAGES FOR THE ANIMALS WE LOVED"
    bb = draw.textbbox((0, 0), label, font=font_label)
    draw.text(((W - (bb[2] - bb[0])) // 2, div_y + 140), label, font=font_label, fill=INK_MUTED)

    # --- URL ---
    try:
        font_url = ImageFont.truetype(FONT_GEORGIA, 38)
    except Exception:
        font_url = ImageFont.load_default()

    url = "www.trace.memorial"
    bb = draw.textbbox((0, 0), url, font=font_url)
    draw.text(((W - (bb[2] - bb[0])) // 2, div_y + 250), url, font=font_url, fill=INK)

    # --- Nine-palette spectrum strip at very bottom ---
    swatch_w = W // len(PALETTE)
    for i, colour in enumerate(PALETTE):
        x0 = i * swatch_w
        x1 = x0 + swatch_w if i < len(PALETTE) - 1 else W
        draw.rectangle([x0, H - STRIP_H, x1, H], fill=colour)

    img.save(PNG_OUT)
    print(f"PNG saved: {PNG_OUT}")

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(PNG_OUT),
        "-t", str(DURATION),
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-pix_fmt", "yuv420p",
        "-vf", "fps=25",
        str(VIDEO_OUT),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("FFmpeg error:", result.stderr[-1000:])
    else:
        size_mb = VIDEO_OUT.stat().st_size / 1_000_000
        print(f"Video saved: {VIDEO_OUT} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    make_endcard()
