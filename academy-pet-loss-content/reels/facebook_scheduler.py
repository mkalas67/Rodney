#!/usr/bin/env python3
"""
Facebook scheduler for Academy for Pet Loss and Trace Memorial.

Reads post_schedule.json, finds pending posts whose files are ready,
uploads them to Facebook, and schedules them to publish at the assigned time.

Run this script whenever new reel or static image files are ready.
Posts are skipped if their file does not yet exist — safe to run repeatedly.

Usage: python facebook_scheduler.py [--dry-run]
"""

import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

BASE_DIR = Path(__file__).parent
SCHEDULE_FILE = BASE_DIR / "post_schedule.json"

LONDON_TZ = ZoneInfo("Europe/London")
API_VERSION = "v21.0"
GRAPH_URL = f"https://graph.facebook.com/{API_VERSION}"

PAGE_IDS = {
    "academy": os.environ.get("FACEBOOK_ACADEMY_PAGE_ID", ""),
    "trace-memorial": os.environ.get("FACEBOOK_TRACE_MEMORIAL_PAGE_ID", ""),
}
USER_TOKEN = os.environ.get("FACEBOOK_ACADEMY_LONG_TOKEN", "")

DRY_RUN = "--dry-run" in sys.argv


def get_page_tokens():
    resp = requests.get(f"{GRAPH_URL}/me/accounts", params={"access_token": USER_TOKEN})
    resp.raise_for_status()
    tokens = {}
    for page in resp.json()["data"]:
        for key, page_id in PAGE_IDS.items():
            if page["id"] == page_id:
                tokens[key] = page["access_token"]
    missing = [k for k in PAGE_IDS if k not in tokens]
    if missing:
        raise RuntimeError(f"Could not retrieve page tokens for: {missing}")
    return tokens


def to_unix_ts(date_str, time_str):
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    dt = dt.replace(tzinfo=LONDON_TZ)
    return int(dt.timestamp())


def upload_reel(page_id, page_token, file_path, title, caption, scheduled_ts):
    """Upload video to Facebook and schedule it."""
    file_path = Path(file_path)
    file_size = file_path.stat().st_size

    # Initialise resumable upload
    init_resp = requests.post(
        f"{GRAPH_URL}/{page_id}/videos",
        data={
            "upload_phase": "start",
            "file_size": file_size,
            "access_token": page_token,
        },
    )
    init_resp.raise_for_status()
    init_data = init_resp.json()
    upload_session_id = init_data["upload_session_id"]
    video_id = init_data["video_id"]
    start_offset = int(init_data["start_offset"])
    end_offset = int(init_data["end_offset"])

    # Upload in chunks (Facebook returns chunk boundaries)
    with open(file_path, "rb") as f:
        while start_offset < file_size:
            f.seek(start_offset)
            chunk = f.read(end_offset - start_offset)
            chunk_resp = requests.post(
                f"{GRAPH_URL}/{page_id}/videos",
                data={
                    "upload_phase": "transfer",
                    "upload_session_id": upload_session_id,
                    "start_offset": start_offset,
                    "access_token": page_token,
                },
                files={"video_file_chunk": chunk},
            )
            chunk_resp.raise_for_status()
            chunk_data = chunk_resp.json()
            start_offset = int(chunk_data["start_offset"])
            end_offset = int(chunk_data["end_offset"])

    # Finish and schedule
    finish_resp = requests.post(
        f"{GRAPH_URL}/{page_id}/videos",
        data={
            "upload_phase": "finish",
            "upload_session_id": upload_session_id,
            "title": title,
            "description": caption,
            "scheduled_publish_time": scheduled_ts,
            "published": "false",
            "access_token": page_token,
        },
    )
    finish_resp.raise_for_status()
    return video_id


def upload_photo(page_id, page_token, file_path, caption, scheduled_ts):
    """Upload image to Facebook and schedule it as a post."""
    with open(file_path, "rb") as f:
        resp = requests.post(
            f"{GRAPH_URL}/{page_id}/photos",
            data={
                "caption": caption,
                "scheduled_publish_time": scheduled_ts,
                "published": "false",
                "access_token": page_token,
            },
            files={"source": f},
        )
    resp.raise_for_status()
    return resp.json()["id"]


def apply_text_overlay(post, base_dir):
    """Run text_overlay.py to produce the processed image."""
    raw = base_dir / post["file"]
    processed = base_dir / post["processed_file"]
    if processed.exists():
        return processed
    print(f"  Applying text overlay...")
    subprocess.run(
        [
            sys.executable,
            str(base_dir / "text_overlay.py"),
            str(raw),
            post["overlay_text"],
            str(processed),
            post["page"],
        ],
        check=True,
    )
    return processed


def process_post(post, page_tokens, base_dir):
    page = post["page"]
    page_id = PAGE_IDS[page]
    page_token = page_tokens[page]
    scheduled_ts = to_unix_ts(post["scheduled_date"], post["scheduled_time"])

    if post["type"] == "static":
        file_path = apply_text_overlay(post, base_dir)
        return upload_photo(page_id, page_token, file_path, post["caption"], scheduled_ts)
    else:
        file_path = base_dir / post["file"]
        return upload_reel(page_id, page_token, file_path, post["title"], post["caption"], scheduled_ts)


def main():
    if not USER_TOKEN:
        print("ERROR: FACEBOOK_ACADEMY_LONG_TOKEN not set.")
        sys.exit(1)

    with open(SCHEDULE_FILE) as f:
        schedule = json.load(f)

    if DRY_RUN:
        print("DRY RUN — no posts will be uploaded.\n")

    page_tokens = {} if DRY_RUN else get_page_tokens()

    scheduled_count = 0
    skipped_count = 0
    error_count = 0

    for post in schedule["posts"]:
        if post["status"] != "pending":
            continue

        file_key = "processed_file" if post["type"] == "static" else "file"
        check_file = BASE_DIR / post["file"]

        if not check_file.exists():
            print(f"[SKIP]  {post['id']} — file not ready")
            skipped_count += 1
            continue

        scheduled_dt = f"{post['scheduled_date']} {post['scheduled_time']} London"
        print(f"[POST]  {post['id']} -> {scheduled_dt}")

        if DRY_RUN:
            scheduled_count += 1
            continue

        try:
            post_id = process_post(post, page_tokens, BASE_DIR)
            post["status"] = "scheduled"
            post["facebook_post_id"] = str(post_id)
            post["scheduled_at"] = datetime.now().isoformat()
            print(f"        Scheduled. Facebook ID: {post_id}")
            scheduled_count += 1
        except requests.HTTPError as e:
            body = e.response.text if e.response is not None else "no body"
            print(f"        ERROR: {e} | {body}")
            error_count += 1
        except Exception as e:
            print(f"        ERROR: {e}")
            error_count += 1

    if not DRY_RUN:
        with open(SCHEDULE_FILE, "w") as f:
            json.dump(schedule, f, indent=2)

    print(f"\nDone. Scheduled: {scheduled_count}  |  Skipped (not ready): {skipped_count}  |  Errors: {error_count}")


if __name__ == "__main__":
    main()
