"""
Reel generation script — Academy for Pet Loss + Trace Memorial
Reads Veo prompts from reel markdown files, calls Veo API, uploads to GCS.

Usage:
  python generate_reels.py                        # generate all reels
  python generate_reels.py --brand academy --reels 1,2    # first 2 Academy reels
  python generate_reels.py --brand trace-memorial --reels 1,2
  python generate_reels.py --brand academy --reels 1      # single reel
"""

import argparse
import base64
import re
import time
import requests as http_requests
from pathlib import Path
from google import genai
from google.genai import types
from google.cloud import storage
from google.oauth2 import service_account
import google.auth.transport.requests

SERVICE_ACCOUNT_FILE = r"D:\Checked_credentials\Academy for Pet Loss and Trace Memorial\academy-for-pet-loss-a00ae8a5b6cb.json"
GCP_PROJECT = "academy-for-pet-loss"
GCP_LOCATION = "us-central1"
GCS_BUCKET = "academy-reels-output"
REELS_DIR = Path(__file__).parent
VEO_MODEL = "veo-2.0-generate-001"
POLL_INTERVAL = 15  # seconds between status checks


def parse_veo_prompts(md_path: Path) -> list[str]:
    """Extract Veo prompts from a reel markdown file."""
    text = md_path.read_text(encoding="utf-8")
    # Each prompt follows a '### Clip N' heading
    prompts = re.findall(r"### Clip \d+\n(.+?)(?=\n###|\Z)", text, re.DOTALL)
    return [p.strip() for p in prompts]


def upload_to_gcs(local_path: Path, gcs_path: str, bucket) -> str:
    blob = bucket.blob(gcs_path)
    blob.upload_from_filename(str(local_path))
    return f"gs://{GCS_BUCKET}/{gcs_path}"


def poll_vertex_operation(operation_name: str, credentials) -> dict:
    """Poll a Vertex AI publisher model long-running operation via fetchPredictOperation."""
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    url = (
        f"https://{GCP_LOCATION}-aiplatform.googleapis.com/v1"
        f"/projects/{GCP_PROJECT}/locations/{GCP_LOCATION}"
        f"/publishers/google/models/{VEO_MODEL}:fetchPredictOperation"
    )
    headers = {"Authorization": f"Bearer {credentials.token}", "Content-Type": "application/json"}
    response = http_requests.post(url, headers=headers, json={"operationName": operation_name})
    response.raise_for_status()
    return response.json()


def generate_clip(client, credentials, prompt: str, output_path: Path) -> bool:
    """Generate a single 8-second clip and save to output_path. Returns success."""
    print(f"  Generating: {output_path.name}")
    print(f"  Prompt: {prompt[:80]}...")

    try:
        operation = client.models.generate_videos(
            model=VEO_MODEL,
            prompt=prompt,
            config=types.GenerateVideosConfig(
                aspect_ratio="9:16",
                duration_seconds=8,
                number_of_videos=1,
            ),
        )

        print(f"    Operation: {operation.name}")

        # Poll via Vertex AI REST API until done
        while True:
            time.sleep(POLL_INTERVAL)
            print(f"    Polling...")
            result = poll_vertex_operation(operation.name, credentials)
            if result.get("done"):
                break

        if "error" in result:
            print(f"    Operation failed: {result['error']}")
            return False

        videos = result.get("response", {}).get("videos", [])
        if not videos:
            print(f"    No videos in response: {result.get('response')}")
            return False

        encoded = videos[0].get("bytesBase64Encoded", "")
        if not encoded:
            print(f"    No video bytes in response: {videos[0].keys()}")
            return False

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(base64.b64decode(encoded))
        print(f"    Saved: {output_path}")
        return True

    except Exception as e:
        print(f"    Error: {e}")
        return False


def process_reel(md_path: Path, client, credentials, gcs_bucket, dry_run=False):
    reel_name = md_path.stem
    brand = md_path.parent.name
    prompts = parse_veo_prompts(md_path)

    if not prompts:
        print(f"  No prompts found in {md_path.name} — skipping")
        return

    print(f"\n{'='*60}")
    print(f"Reel: {brand}/{reel_name} ({len(prompts)} clips)")

    for i, prompt in enumerate(prompts, 1):
        clip_filename = f"clip-{i:02d}.mp4"
        local_path = REELS_DIR / "output" / brand / reel_name / clip_filename
        gcs_path = f"{brand}/{reel_name}/{clip_filename}"

        if dry_run:
            print(f"  [DRY RUN] Would generate: {gcs_path}")
            print(f"  Prompt: {prompt[:100]}")
            continue

        success = generate_clip(client, credentials, prompt, local_path)
        if success:
            uri = upload_to_gcs(local_path, gcs_path, gcs_bucket)
            print(f"    Uploaded: {uri}")


def get_reel_files(brand: str, reel_numbers: list[int] | None) -> list[Path]:
    brand_dir = REELS_DIR / brand
    if not brand_dir.exists():
        raise FileNotFoundError(f"Brand folder not found: {brand_dir}")

    files = sorted(brand_dir.glob("*.md"))
    if reel_numbers:
        files = [f for f in files if int(f.stem.split("-")[0]) in reel_numbers]
    return files


def main():
    parser = argparse.ArgumentParser(description="Generate reels via Veo API")
    parser.add_argument("--brand", choices=["academy", "trace-memorial", "all"], default="all")
    parser.add_argument("--reels", help="Comma-separated reel numbers, e.g. 1,2")
    parser.add_argument("--dry-run", action="store_true", help="Parse prompts without calling API")
    args = parser.parse_args()

    reel_numbers = [int(n) for n in args.reels.split(",")] if args.reels else None

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    client = genai.Client(
        vertexai=True,
        project=GCP_PROJECT,
        location=GCP_LOCATION,
        credentials=credentials,
    )
    storage_client = storage.Client(project=GCP_PROJECT, credentials=credentials)
    gcs_bucket = storage_client.bucket(GCS_BUCKET)

    brands = ["academy", "trace-memorial"] if args.brand == "all" else [args.brand]

    for brand in brands:
        files = get_reel_files(brand, reel_numbers)
        if not files:
            print(f"No matching reel files for brand '{brand}'")
            continue
        for md_path in files:
            process_reel(md_path, client, credentials, gcs_bucket, dry_run=args.dry_run)

    print("\nDone.")


if __name__ == "__main__":
    main()
