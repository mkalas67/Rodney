#!/usr/bin/env python3
"""
Overlay quote text on a static image for Facebook posting.
Usage: python text_overlay.py <input_image> <text> <output_image> <brand>
brand: academy | trace-memorial
"""

import sys
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BRANDS = {
    "academy": {
        "text_color": (61, 50, 40),
        "overlay_color": (245, 238, 228),
        "overlay_alpha": 175,
        "brand_name": "Academy for Pet Loss",
    },
    "trace-memorial": {
        "text_color": (245, 240, 235),
        "overlay_color": (25, 20, 15),
        "overlay_alpha": 165,
        "brand_name": "Trace Memorial",
    },
}

OUTPUT_SIZE = (1080, 1080)
FONT_REGULAR = r"C:\Windows\Fonts\segoeui.ttf"
FONT_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"


def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines = []
    current = []
    for word in words:
        test = " ".join(current + [word])
        bbox = draw.textbbox((0, 0), test, font=font)
        w = bbox[2] - bbox[0]
        if w > max_width and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


def overlay_text(input_path, text, output_path, brand):
    config = BRANDS[brand]

    img = Image.open(input_path).convert("RGBA")
    img = img.resize(OUTPUT_SIZE, Image.LANCZOS)

    # Semi-transparent overlay on lower half
    overlay = Image.new("RGBA", OUTPUT_SIZE, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    overlay_top = int(OUTPUT_SIZE[1] * 0.52)
    r, g, b = config["overlay_color"]
    draw_overlay.rectangle(
        [(0, overlay_top), OUTPUT_SIZE],
        fill=(r, g, b, config["overlay_alpha"]),
    )
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    padding = 70
    text_area_width = OUTPUT_SIZE[0] - (padding * 2)

    try:
        quote_font = ImageFont.truetype(FONT_BOLD, 54)
    except OSError:
        quote_font = ImageFont.load_default()

    try:
        brand_font = ImageFont.truetype(FONT_REGULAR, 28)
    except OSError:
        brand_font = ImageFont.load_default()

    lines = wrap_text(text, quote_font, text_area_width, draw)
    line_height = 54 + 14
    total_text_height = len(lines) * line_height

    available_height = OUTPUT_SIZE[1] - overlay_top - 70
    text_start_y = overlay_top + (available_height - total_text_height) // 2 - 10

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=quote_font)
        w = bbox[2] - bbox[0]
        x = (OUTPUT_SIZE[0] - w) // 2
        y = text_start_y + (i * line_height)
        draw.text((x, y), line, font=quote_font, fill=config["text_color"])

    brand_bbox = draw.textbbox((0, 0), config["brand_name"], font=brand_font)
    brand_w = brand_bbox[2] - brand_bbox[0]
    brand_x = (OUTPUT_SIZE[0] - brand_w) // 2
    brand_y = OUTPUT_SIZE[1] - 46
    draw.text((brand_x, brand_y), config["brand_name"], font=brand_font, fill=config["text_color"])

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(output_path, "PNG")
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python text_overlay.py <input> <text> <output> <brand>")
        sys.exit(1)
    overlay_text(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
