"""
Reel composition script
Concatenates Veo clips, burns in on-screen text, mixes music.

Usage:
  python compose_reel.py --brand academy --reel 1
  python compose_reel.py --brand trace-memorial --reel 1
"""

import argparse
import re
import subprocess
import tempfile
from pathlib import Path

REELS_DIR = Path(__file__).parent
CLIP_DURATION = 8
MUSIC_DIR = REELS_DIR / "music"
OUTPUT_DIR = REELS_DIR / "output"

FONT_PATH = r"C\:/Windows/Fonts/segoeui.ttf"
TEXT_MARGIN = 50         # horizontal margin from each edge
TEXT_TOP_START = 80      # pixels from top of frame where text block begins
WRAP_CHARS = 26          # max characters per line before wrapping
BOX_PADDING = 10         # padding inside the text background box

ENDCARD = {
    "academy":       OUTPUT_DIR / "endcard-academy.mp4",
    "trace-memorial": OUTPUT_DIR / "endcard-trace-memorial.mp4",
}

BRAND_CONFIG = {
    "academy": {
        "text_color": "0xFFFFFF",          # white — readable on any background
        "box_color": "0x1E2B3C@0.55",      # brand navy, 55% opacity
        "fontfile": FONT_PATH,
        "fontsize": 44,
        "music_dir": MUSIC_DIR / "academy",
    },
    "trace-memorial": {
        "text_color": "0xFFFFFF",
        "box_color": "0x0A0A0A@0.50",      # near-black, 50% opacity
        "fontfile": FONT_PATH,
        "fontsize": 42,
        "music_dir": MUSIC_DIR / "trace-memorial",
    },
}

MUSIC_MAP = {
    "academy": {
        "track-a": "track-a-folding-maple.mp3",
        "track-b": "track-b-copper-conductor.mp3",
        "track-c": "Still Water Piano.mp3",
    },
    "trace-memorial": {
        "track-d": "track-d-long-decay-room.mp3",
        "track-e": "track eHeld Breath.mp3",
        "track-f": "track fPaper After Rain.mp3",
    },
}


def wrap_line(text: str, max_chars: int = WRAP_CHARS) -> list[str]:
    """Break a single line into multiple lines at word boundaries."""
    if len(text) <= max_chars:
        return [text]
    words = text.split()
    lines, current = [], ""
    for word in words:
        if current and len(current) + 1 + len(word) > max_chars:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        lines.append(current)
    return lines


def escape_drawtext(text: str) -> str:
    """Escape special characters for FFmpeg drawtext filter."""
    text = text.replace("\\", "\\\\")
    text = text.replace("'", "’")   # replace smart quote to avoid escaping hell
    text = text.replace('"', '“')   # same for double quotes
    text = text.replace(":", "\\:")
    text = text.replace(",", "\\,")
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    return text


def parse_reel(md_path: Path) -> dict:
    """Parse on-screen text, suno track, and clip count from reel markdown."""
    text = md_path.read_text(encoding="utf-8")

    # Suno track
    track_match = re.search(r"\*\*Suno track:\*\*\s*(Track-\w+)", text, re.IGNORECASE)
    suno_track = track_match.group(1).lower() if track_match else "track-a"

    # On-screen text section
    text_match = re.search(r"## On-screen text\n\n(.+?)(?=\n## |\Z)", text, re.DOTALL)
    raw = text_match.group(1).strip() if text_match else ""

    # Split by blank lines into groups
    groups = [g.strip() for g in re.split(r"\n\n+", raw) if g.strip()]

    return {"suno_track": suno_track, "groups": groups}


def distribute_text(groups: list[str], num_clips: int, clip_duration: float) -> list[tuple]:
    """
    Distribute text groups across clips.
    Returns list of (start_sec, end_sec, lines) tuples.
    Lines is a list of strings (one per line in the group).
    """
    total_duration = num_clips * clip_duration
    time_per_group = total_duration / len(groups)
    entries = []

    for i, group in enumerate(groups):
        start = i * time_per_group + 0.4
        end = (i + 1) * time_per_group - 0.4
        raw_lines = [l.strip() for l in group.split("\n") if l.strip()]
        # Wrap any line that's too long for the frame
        wrapped = []
        for l in raw_lines:
            wrapped.extend(wrap_line(l))
        entries.append((start, end, wrapped))

    return entries


def build_drawtext_filters(entries: list[tuple], cfg: dict) -> list[str]:
    """Build list of drawtext filter strings, one per text line per entry."""
    fontfile = cfg["fontfile"]
    fontsize = cfg["fontsize"]
    color = cfg["text_color"]
    box_color = cfg["box_color"]
    line_spacing = fontsize + 14
    filters = []

    for start, end, lines in entries:
        for j, line in enumerate(lines):
            escaped = escape_drawtext(line)
            y = TEXT_TOP_START + j * line_spacing
            x = f"max({TEXT_MARGIN}\\, min((w-text_w)/2\\, w-text_w-{TEXT_MARGIN}))"
            f = (
                f"drawtext=fontfile='{fontfile}'"
                f":text='{escaped}'"
                f":fontcolor='{color}'"
                f":fontsize={fontsize}"
                f":x={x}"
                f":y={y}"
                f":box=1:boxcolor='{box_color}':boxborderw={BOX_PADDING}"
                f":enable='between(t,{start:.2f},{end:.2f})'"
            )
            filters.append(f)

    return filters


def compose_reel(brand: str, reel_num: int):
    cfg = BRAND_CONFIG[brand]
    brand_dir = REELS_DIR / brand
    md_files = sorted(brand_dir.glob("*.md"))
    md_files = [f for f in md_files if int(f.stem.split("-")[0]) == reel_num]

    if not md_files:
        print(f"No markdown file found for {brand} reel {reel_num}")
        return

    md_path = md_files[0]
    reel_name = md_path.stem
    parsed = parse_reel(md_path)

    clip_dir = OUTPUT_DIR / brand / reel_name
    clips = sorted(clip_dir.glob("clip-*.mp4"))

    if not clips:
        print(f"No clips found at {clip_dir}")
        return

    num_clips = len(clips)
    total_duration = num_clips * CLIP_DURATION

    print(f"Composing: {brand}/{reel_name}")
    print(f"  Clips: {num_clips} x {CLIP_DURATION}s = {total_duration}s")
    print(f"  Text groups: {len(parsed['groups'])}")
    print(f"  Track: {parsed['suno_track']}")

    # Write concat list
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        concat_file = Path(f.name)
        for clip in clips:
            f.write(f"file '{clip}'\n")

    # Build drawtext filters
    entries = distribute_text(parsed["groups"], num_clips, CLIP_DURATION)
    drawtext_filters = build_drawtext_filters(entries, cfg)
    vf = ",".join(drawtext_filters) if drawtext_filters else "null"

    # Resolve music file
    track_key = parsed["suno_track"].replace(" ", "")  # e.g. "track-b"
    music_filename = MUSIC_MAP.get(brand, {}).get(track_key)
    music_path = cfg["music_dir"] / music_filename if music_filename else None

    output_path = clip_dir / f"{reel_name}-final.mp4"

    if music_path and music_path.exists():
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_file),
            "-stream_loop", "-1", "-i", str(music_path),
            "-filter_complex",
            f"[0:v]{vf}[vout];[1:a]volume=0.6,afade=t=out:st={total_duration - 2}:d=2[aout]",
            "-map", "[vout]",
            "-map", "[aout]",
            "-t", str(total_duration),
            "-c:v", "libx264", "-crf", "18", "-preset", "medium",
            "-c:a", "aac", "-b:a", "192k",
            str(output_path),
        ]
    else:
        print("  No music file found — composing video only")
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_file),
            "-vf", vf,
            "-c:v", "libx264", "-crf", "18", "-preset", "medium",
            str(output_path),
        ]

    print(f"  Output: {output_path}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  FFmpeg error:\n{result.stderr[-2000:]}")
        concat_file.unlink(missing_ok=True)
        return

    size_mb = output_path.stat().st_size / 1_000_000
    print(f"  Done. File size: {size_mb:.1f} MB")
    concat_file.unlink(missing_ok=True)

    # Append end card
    endcard_path = ENDCARD.get(brand)
    if endcard_path and endcard_path.exists():
        final_path = clip_dir / f"{reel_name}-with-endcard.mp4"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            ec_list = Path(f.name)
            f.write(f"file '{output_path}'\n")
            f.write(f"file '{endcard_path}'\n")
        cmd_ec = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", str(ec_list),
            "-c", "copy",
            str(final_path),
        ]
        result_ec = subprocess.run(cmd_ec, capture_output=True, text=True)
        ec_list.unlink(missing_ok=True)
        if result_ec.returncode != 0:
            print(f"  End card append error:\n{result_ec.stderr[-1000:]}")
        else:
            size_mb = final_path.stat().st_size / 1_000_000
            print(f"  With end card: {final_path.name} ({size_mb:.1f} MB)")
    else:
        print(f"  No end card found at {endcard_path} — skipping")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--brand", required=True, choices=["academy", "trace-memorial"])
    parser.add_argument("--reel", required=True, type=int)
    args = parser.parse_args()
    compose_reel(args.brand, args.reel)


if __name__ == "__main__":
    main()
