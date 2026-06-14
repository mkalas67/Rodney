# Reels Pipeline Handover
Date: 2026-06-14

## What this project is

Two brands, 35 short-form reels total:
- Academy for Pet Loss (20 reels) — professional training in pet bereavement support
- Trace Memorial (15 reels) — memorial pages for pets

All scripts are in `D:\Rodney\academy-pet-loss-content\reels\`

## Current state

### Generation (Veo clips via Google Vertex AI)
- Academy: ALL 20 reels done. Clips in `reels/output/academy/`
- Trace Memorial: reels 1-9 done. Reels 10-15 still generating in the background.
  Check by looking for folders in `reels/output/trace-memorial/` — if 10-15 exist with clip-*.mp4 files inside, they are done.

### Composition (text burn + music + end card)
- Academy: ALL 20 reels composed. `*-with-endcard.mp4` files exist in each subfolder.
- Trace Memorial: reels 1-9 composed. Reels 10-15 need composing once clips are ready.

## What still needs doing

### Step 1 — Compose Trace Memorial reels 10-15
Wait until the clip folders exist and contain clip-*.mp4 files, then run:

```
cd D:\Rodney\academy-pet-loss-content
python reels/compose_reel.py --brand trace-memorial --reel 10
python reels/compose_reel.py --brand trace-memorial --reel 11
python reels/compose_reel.py --brand trace-memorial --reel 12
python reels/compose_reel.py --brand trace-memorial --reel 13
python reels/compose_reel.py --brand trace-memorial --reel 14
python reels/compose_reel.py --brand trace-memorial --reel 15
```

Each one produces `*-final.mp4` and `*-with-endcard.mp4`. The with-endcard version is what gets posted.

### Step 2 — Post schedule
This has not been created yet. The next session needs to:
- Decide posting frequency and platforms (Instagram, Facebook, TikTok)
- Create a schedule interleaving Academy and Trace Memorial reels
  (suggested opening order is in `D:\DD\reels-content-strategy.md` under "Sequencing suggestion")
- Write captions for each reel
- Set up scheduled posting

## Key file locations

| What | Where |
|---|---|
| All reel scripts | `D:\Rodney\academy-pet-loss-content\reels\` |
| Academy clips + composed reels | `reels/output/academy/` |
| Trace Memorial clips + composed reels | `reels/output/trace-memorial/` |
| End card videos | `reels/output/endcard-academy.mp4`, `reels/output/endcard-trace-memorial.mp4` |
| Content strategy | `D:\DD\reels-content-strategy.md` |
| Music | `reels/music/academy/`, `reels/music/trace-memorial/` |
| Reel markdown files (prompts + text) | `reels/academy/`, `reels/trace-memorial/` |
| Facebook scheduler (from earlier session) | `reels/facebook_scheduler.py` |
| Post schedule JSON (from earlier session) | `reels/post_schedule.json` |

## Credentials

Service account: `D:\Checked_credentials\Academy for Pet Loss and Trace Memorial\academy-for-pet-loss-a00ae8a5b6cb.json`
GCS bucket: `academy-reels-output` (europe-west2)
Facebook token: in `D:\Rodney\.claude/settings.local.json` under `FACEBOOK_ACADEMY_LONG_TOKEN`

## Git

Repo: `D:\Rodney\academy-pet-loss-content` (GitHub: mkalas67/Rodney, branch: master)
All pipeline scripts are committed and pushed. Output files are gitignored.
