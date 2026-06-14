"""
Generate a 5-second branded end card for Trace Memorial reels.
Uses Pillow for the image, FFmpeg to convert to video.
Output: reels/output/endcard-trace-memorial.mp4
"""

import subprocess
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REELS_DIR = Path(__file__).parent
PNG_OUT = REELS_DIR / "output" / "endcard-trace-memorial.png"
VIDEO_OUT = REELS_DIR / "output" / "endcard-trace-memorial.mp4"
DURATION = 5
W, H = 720, 1280

# Brand colours
BG = "#fdfaf0"
TEXT_DARK = "#2d1f0e"
TEXT_FADED = "#2d1f0e"
LEAF_COLOUR = "#2d1f0e"

# Palette strip colours (panel bg, softer tones)
PALETTE = [
    "#fae8dc",  # Sunset
    "#f7f0d8",  # Golden
    "#f7dcea",  # Rose
    "#e6f0e6",  # Meadow
    "#ddeeff",  # Sky
    "#e0ecf4",  # Ocean
    "#ede0f7",  # Lavender
    "#e4ece0",  # Forest
    "#e8e8e8",  # Monochrome
]

# Font paths
FONT_GEORGIA = r"C:\Windows\Fonts\georgia.ttf"
FONT_GEORGIA_BOLD = r"C:\Windows\Fonts\georgiab.ttf"
FONT_SEGOE = r"C:\Windows\Fonts\segoeui.ttf"
FONT_SEGOE_LIGHT = r"C:\Windows\Fonts\segoeuil.ttf"


def draw_leaf(draw: ImageDraw, cx: int, cy: int, size: int, colour: str, stroke: int = 3):
    """Draw a vesica-piscis leaf mark (outline only, with centre line)."""
    # Two arcs forming a pointed oval
    r = size
    # Left arc centre and right arc centre
    offset = int(r * 0.6)
    bbox_left = [cx - r - offset, cy - r, cx + offset, cy + r]
    bbox_right = [cx - offset, cy - r, cx + r + offset, cy + r]
    draw.arc(bbox_left, start=-60, end=60, fill=colour, width=stroke)
    draw.arc(bbox_right, start=120, end=240, fill=colour, width=stroke)
    # Centre vertical line
    top_y = cy - int(r * 0.87)
    bot_y = cy + int(r * 0.87)
    draw.line([(cx, top_y), (cx, bot_y)], fill=colour, width=stroke)


def make_endcard():
    PNG_OUT.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # --- Palette strip at top ---
    strip_h = 18
    swatch_w = W // len(PALETTE)
    for i, colour in enumerate(PALETTE):
        x0 = i * swatch_w
        x1 = x0 + swatch_w if i < len(PALETTE) - 1 else W
        draw.rectangle([x0, 0, x1, strip_h], fill=colour)

    # --- Leaf mark ---
    leaf_cx = W // 2
    leaf_cy = 380
    draw_leaf(draw, leaf_cx, leaf_cy, size=70, colour=LEAF_COLOUR, stroke=3)

    # --- Wordmark: trace.memorial ---
    try:
        font_trace = ImageFont.truetype(FONT_GEORGIA_BOLD, 56)
        font_memorial = ImageFont.truetype(FONT_GEORGIA, 56)
    except Exception:
        font_trace = ImageFont.load_default()
        font_memorial = font_trace

    wordmark_y = 500
    # Measure "trace" and ".memorial" separately
    trace_text = "trace"
    memorial_text = ".memorial"
    bb_trace = draw.textbbox((0, 0), trace_text, font=font_trace)
    bb_mem = draw.textbbox((0, 0), memorial_text, font=font_memorial)
    trace_w = bb_trace[2] - bb_trace[0]
    mem_w = bb_mem[2] - bb_mem[0]
    total_w = trace_w + mem_w
    start_x = (W - total_w) // 2

    draw.text((start_x, wordmark_y), trace_text, font=font_trace, fill=TEXT_DARK)
    # .memorial at ~50% opacity — simulate with a lighter brown
    draw.text((start_x + trace_w, wordmark_y), memorial_text, font=font_memorial, fill="#8a6a4a")

    # --- Thin divider ---
    div_y = wordmark_y + 80
    draw.line([(W // 2 - 100, div_y), (W // 2 + 100, div_y)], fill="#c8b89a", width=1)

    # --- Tagline ---
    try:
        font_tagline = ImageFont.truetype(FONT_SEGOE_LIGHT, 30)
    except Exception:
        font_tagline = ImageFont.truetype(FONT_SEGOE, 30)

    tagline = "A permanent home for their story."
    bb = draw.textbbox((0, 0), tagline, font=font_tagline)
    tw = bb[2] - bb[0]
    draw.text(((W - tw) // 2, div_y + 24), tagline, font=font_tagline, fill=TEXT_DARK)

    # --- Label (small, spaced) ---
    try:
        font_label = ImageFont.truetype(FONT_SEGOE, 18)
    except Exception:
        font_label = ImageFont.load_default()

    label = "MEMORIAL PAGES FOR THE ANIMALS WE LOVED"
    bb = draw.textbbox((0, 0), label, font=font_label)
    lw = bb[2] - bb[0]
    draw.text(((W - lw) // 2, div_y + 90), label, font=font_label, fill="#8a6a4a")

    # --- Website ---
    try:
        font_web = ImageFont.truetype(FONT_GEORGIA, 28)
    except Exception:
        font_web = ImageFont.load_default()

    website = "trace.memorial"
    bb = draw.textbbox((0, 0), website, font=font_web)
    ww = bb[2] - bb[0]
    draw.text(((W - ww) // 2, div_y + 160), website, font=font_web, fill=TEXT_DARK)

    # --- Palette strip at bottom (mirror of top) ---
    for i, colour in enumerate(PALETTE):
        x0 = i * swatch_w
        x1 = x0 + swatch_w if i < len(PALETTE) - 1 else W
        draw.rectangle([x0, H - strip_h, x1, H], fill=colour)

    img.save(PNG_OUT)
    print(f"PNG saved: {PNG_OUT}")

    # Convert PNG to 5-second video
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
