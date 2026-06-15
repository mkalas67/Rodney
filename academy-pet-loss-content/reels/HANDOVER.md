# Reels Pipeline Handover
Date: 2026-06-14

## What this project is

Two brands, 35 short-form reels total:
- Academy for Pet Loss (20 reels) — professional training in pet bereavement support
- Trace Memorial (15 reels) — memorial pages for pets

All scripts are in `D:\Rodney\academy-pet-loss-content\reels\`

---

## Current state

### Generation (Veo clips via Google Vertex AI)
- Academy: ALL 20 reels done. Clips in `reels/output/academy/`
- Trace Memorial: reels 1–9 done and composed. Reels 10–15 still generating.
  Check by looking for folders in `reels/output/trace-memorial/` — if 10–15 exist with `clip-*.mp4` files inside, they are ready to compose.

### Composition (text burn + music + end card)
- Academy: ALL 20 reels composed. `*-with-endcard.mp4` files in each subfolder.
- Trace Memorial: reels 1–9 composed. Reels 10–15 need composing once clips are ready.

### Facebook scheduling
- All posts are defined in `reels/post_schedule.json` with dates, captions, and Facebook post IDs.
- Facebook only allows scheduling up to ~30 days ahead via the API.
- As of 14 June, everything up to 11 July is scheduled on Facebook.
- Posts beyond 11 July are `pending` in the JSON and will schedule automatically when you run the script again on or after ~15 July.

**What is scheduled on Facebook right now:**
- Academy reels: 1, 7, 14, 3, 10, 16, 2, 8, 15, 4, 11, 17 (16 Jun – 11 Jul)
- Trace Memorial reels: 1, 9, 3, 5, 2 (17 Jun – 8 Jul)
- Academy static posts: 1, 2 (21 Jun, 5 Jul)
- Trace Memorial static posts: 1, 2 (22 Jun, 6 Jul)

**Still pending (files ready but beyond 30-day window):**
- Academy reels: 5, 9, 18, 6, 12, 19, 13, 20 (14 Jul – 30 Jul)
- Trace reels: 4, 6, 7, 8 (15 Jul – 5 Aug)
- Academy static posts: 3, 4 (19 Jul, 2 Aug)
- Trace Memorial static posts: 3, 4, 5, 6 (20 Jul – 10 Aug)

**Still pending (files not yet ready):**
- Trace reels: 10, 11, 12, 13, 14, 15 — clips not yet generated

---

## What still needs doing

### Step 1 — Compose Trace Memorial reels 10–15
Once the clip folders exist and contain `clip-*.mp4` files, run:

```
cd D:\Rodney\academy-pet-loss-content
python reels/compose_reel.py --brand trace-memorial --reel 10
python reels/compose_reel.py --brand trace-memorial --reel 11
python reels/compose_reel.py --brand trace-memorial --reel 12
python reels/compose_reel.py --brand trace-memorial --reel 13
python reels/compose_reel.py --brand trace-memorial --reel 14
python reels/compose_reel.py --brand trace-memorial --reel 15
```

Each produces `*-with-endcard.mp4` in the reel's output subfolder.

### Step 2 — Run the scheduler again (~15 July)
Run this from the reels folder with credentials loaded:

```
cd D:\Rodney\academy-pet-loss-content\reels
python facebook_scheduler.py
```

This will schedule all the posts that are currently pending due to the 30-day Facebook limit.
Run it again once Trace reels 10–15 are composed — the script skips anything already scheduled
and picks up whatever is new.

### Step 3 — Renew Facebook token before 13 August
The token was renewed on 14 June 2026 and expires 13 August 2026.
Last post in the schedule is 10 August. Renew the token before then.
Token is in `D:\Rodney\.claude\settings.local.json` under `FACEBOOK_ACADEMY_LONG_TOKEN`.
Renewal is a single API call — ask Claude to do it.

---

## Key file locations

| What | Where |
|---|---|
| All reel scripts | `D:\Rodney\academy-pet-loss-content\reels\` |
| Academy clips + composed reels | `reels/output/academy/` |
| Trace Memorial clips + composed reels | `reels/output/trace-memorial/` |
| Static images (raw) | `reels/output/academy/static/`, `reels/output/trace-memorial/static/` |
| Static images (text overlay applied) | `reels/output/academy/static/processed/`, `reels/output/trace-memorial/static/processed/` |
| End card videos | `reels/output/endcard-academy.mp4`, `reels/output/endcard-trace-memorial.mp4` |
| Post schedule + captions | `reels/post_schedule.json` |
| Facebook scheduler script | `reels/facebook_scheduler.py` |
| Text overlay script | `reels/text_overlay.py` |
| Content strategy | `D:\DD\reels-content-strategy.md` |
| Music | `reels/music/academy/`, `reels/music/trace-memorial/` |
| Reel markdown files (prompts + text) | `reels/academy/`, `reels/trace-memorial/` |

## Credentials

Facebook token: in `D:\Rodney\.claude\settings.local.json` under `FACEBOOK_ACADEMY_LONG_TOKEN`
Facebook token expiry: 2026-08-13
Facebook App ID: 1568606104974138
Academy page ID: 1076317922236905
Trace Memorial page ID: 1104616522737038

Service account (Vertex AI / GCS): `D:\Checked_credentials\Academy for Pet Loss and Trace Memorial\academy-for-pet-loss-a00ae8a5b6cb.json`
GCS bucket: `academy-reels-output` (europe-west2)

## Git

Repo: `D:\Rodney\academy-pet-loss-content` (GitHub: mkalas67/Rodney, branch: master)
All pipeline scripts are committed and pushed. Output files are gitignored.
