"""
Generate a 5-second branded end card for Academy for Pet Loss reels.
Outputs: reels/output/endcard-academy.mp4

Run once — append to any reel with:
  ffmpeg -f concat -safe 0 -i list.txt -c copy final.mp4
"""

import subprocess
from pathlib import Path

REELS_DIR = Path(__file__).parent
OUTPUT = REELS_DIR / "output" / "endcard-academy.mp4"
FONT_PATH = r"C\:/Windows/Fonts/segoeui.ttf"
FONT_LORA = r"C\:/Windows/Fonts/georgia.ttf"   # closest serif on Windows to Lora
DURATION = 5
W, H = 720, 1280
BG_COLOR = "0x1E2B3C"        # brand navy
GOLD = "0xC9943A"            # brand gold (from Logo.tsx)
TEXT_LIGHT = "0xF8F6F2"      # off-white

# Contact details from SiteFooter
EMAIL = "academyforpetloss@gmail.com"
WEBSITE = "academyforpetloss.com"
TAGLINE = "Professional training in pet bereavement support"


def esc(t):
    return (t.replace("\\", "\\\\")
             .replace(":", "\\:")
             .replace("'", "'")
             .replace(",", "\\,")
             .replace("[", "\\[")
             .replace("]", "\\]"))


def build_endcard():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    # Layout (all y positions in pixels from top of 1280px frame)
    circle_cx, circle_cy, circle_r = W // 2, 390, 80
    letter_y = 430
    academy_y = 540
    forpetloss_y = 580
    divider_y = 630
    tagline_y = 680
    email_y = 800
    website_y = 860

    vf_parts = [
        # Solid background
        f"color=c=0x1E2B3C:size={W}x{H}:duration={DURATION}[bg]",
        "[bg]",

        # Circle outline
        f"drawbox=x={circle_cx - circle_r}:y={circle_cy - circle_r}"
        f":w={circle_r*2}:h={circle_r*2}:color={GOLD}@0.0:t=2",  # transparent fill

        # "A" letterform in gold (using Georgia as serif stand-in)
        f"drawtext=fontfile='{FONT_LORA}':text='A':fontcolor='{GOLD}':fontsize=96"
        f":x=(w-text_w)/2:y={letter_y - 48}",

        # Thin horizontal rule above wordmark (simulate vertical divider as horizontal for reel)
        f"drawbox=x={W//2 - 80}:y={academy_y - 24}:w=160:h=1:color={GOLD}@0.3:t=fill",

        # ACADEMY
        f"drawtext=fontfile='{FONT_LORA}':text='ACADEMY':fontcolor='{TEXT_LIGHT}':fontsize=44"
        f":x=(w-text_w)/2:y={academy_y}",

        # FOR PET LOSS
        f"drawtext=fontfile='{FONT_PATH}':text='FOR PET LOSS':fontcolor='{TEXT_LIGHT}@0.7':fontsize=18"
        f":x=(w-text_w)/2:y={forpetloss_y}",

        # Divider line
        f"drawbox=x=200:y={divider_y}:w=320:h=1:color={GOLD}@0.4:t=fill",

        # Tagline
        f"drawtext=fontfile='{FONT_PATH}':text='{esc(TAGLINE)}':fontcolor='{TEXT_LIGHT}@0.85':fontsize=26"
        f":x=(w-text_w)/2:y={tagline_y}",

        # Email
        f"drawtext=fontfile='{FONT_PATH}':text='{esc(EMAIL)}':fontcolor='{GOLD}':fontsize=26"
        f":x=(w-text_w)/2:y={email_y}",

        # Website
        f"drawtext=fontfile='{FONT_PATH}':text='{esc(WEBSITE)}':fontcolor='{TEXT_LIGHT}@0.7':fontsize=24"
        f":x=(w-text_w)/2:y={website_y}",
    ]

    drawtext_filters = [
        # Circle outline via drawbox (square clipped — FFmpeg has no circle primitive)
        f"drawbox=x={circle_cx - circle_r}:y={circle_cy - circle_r}"
        f":w={circle_r*2}:h={circle_r*2}:color={GOLD}:t=3",

        # "A" letterform
        f"drawtext=fontfile='{FONT_LORA}':text='A':fontcolor='{GOLD}':fontsize=96"
        f":x=(w-text_w)/2:y={letter_y - 48}",

        # Divider above wordmark
        f"drawbox=x={W//2 - 80}:y={academy_y - 24}:w=160:h=1:color={GOLD}@0.3:t=fill",

        # ACADEMY
        f"drawtext=fontfile='{FONT_LORA}':text='ACADEMY':fontcolor='{TEXT_LIGHT}':fontsize=44"
        f":x=(w-text_w)/2:y={academy_y}",

        # FOR PET LOSS
        f"drawtext=fontfile='{FONT_PATH}':text='FOR PET LOSS':fontcolor='{TEXT_LIGHT}@0.7':fontsize=18"
        f":x=(w-text_w)/2:y={forpetloss_y}",

        # Gold divider
        f"drawbox=x=200:y={divider_y}:w=320:h=1:color={GOLD}@0.4:t=fill",

        # Tagline
        f"drawtext=fontfile='{FONT_PATH}':text='{esc(TAGLINE)}':fontcolor='{TEXT_LIGHT}@0.85':fontsize=26"
        f":x=(w-text_w)/2:y={tagline_y}",

        # Email
        f"drawtext=fontfile='{FONT_PATH}':text='{esc(EMAIL)}':fontcolor='{GOLD}':fontsize=26"
        f":x=(w-text_w)/2:y={email_y}",

        # Website
        f"drawtext=fontfile='{FONT_PATH}':text='{esc(WEBSITE)}':fontcolor='{TEXT_LIGHT}@0.7':fontsize=24"
        f":x=(w-text_w)/2:y={website_y}",
    ]

    vf = ",".join(drawtext_filters)

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=0x1E2B3C:size={W}x{H}:duration={DURATION}",
        "-vf", vf,
        "-t", str(DURATION),
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-pix_fmt", "yuv420p",
        str(OUTPUT),
    ]

    print(f"Generating end card: {OUTPUT}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("FFmpeg error:")
        print(result.stderr[-3000:])
    else:
        size_mb = OUTPUT.stat().st_size / 1_000_000
        print(f"Done. {size_mb:.1f} MB")


if __name__ == "__main__":
    build_endcard()
