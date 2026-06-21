# Positron Academy Auto-Poster Bot

Production-ready Facebook and Instagram posting for media stored in this repository's `images/` and `video/` folders. The bot now generates a validated caption for every asset instead of reusing one hard-coded caption.

## What the system enforces

- Exact 10-post content cycle: 40% educational, 30% student success, 20% admission, 10% trending/funny educational.
- Reusable PTI Admission, BSTC Admission, B.Ed Admission, ANM Admission, and CET Preparation templates.
- Every caption contains a hook, useful content, Follow/DM/WhatsApp CTAs, and all eight local hashtags.
- Every reel ends with the required Positron Academy follow sentence.
- Captions are validated before any Meta API call and kept below Instagram's 2,200-character limit.
- Student-success copy avoids invented names, ranks, and results. Add verified student proof manually when consent is available.

The editable strategy lives in [`content_plan.json`](content_plan.json). Profile and engagement guidance is also summarized in [`CONTENT_PLAYBOOK.md`](CONTENT_PLAYBOOK.md).

## Media behavior

Keep adding assets to the existing folders:

```text
images/       .png, .jpg, .jpeg
video/        .mp4, .mov, .avi
```

Each live run selects the first unposted image and video in filename order. Progress is stored with folder-aware keys in `posted.txt`; the old bare-filename format remains supported. When every file in one folder has been posted, that folder's loop resets independently.

`content_state.json` advances only after at least one platform successfully publishes an asset. This keeps the 4/3/2/1 distribution tied to successful posts, not failed attempts.

## Preview captions locally

Install dependencies and preview a complete content cycle without credentials or state changes:

```powershell
python -m pip install -r requirements.txt
python bot.py --preview --count 10
```

Useful commands:

```powershell
# Reels only, beginning at cycle index 10
python bot.py --preview --count 5 --media-type reel --start-index 10

# Print profile, poll, story, schedule, and reel-topic suggestions
python bot.py --strategy

# Run validation tests
python -m unittest discover -s tests -v
```

## GitHub Actions setup

Add these repository secrets under **Settings → Secrets and variables → Actions**:

| Secret | Purpose |
|---|---|
| `FB_PAGE_TOKEN` | Meta access token used for Facebook and Instagram publishing |
| `FB_PAGE_ID` | Facebook Page ID |
| `IG_ACCOUNT_ID` | Instagram professional account ID |

The workflow supplies `GITHUB_REPOSITORY` automatically so Meta can fetch raw media from this repository. The media files must be accessible to Meta through their raw GitHub URLs.

Optional environment variables:

| Variable | Default | Purpose |
|---|---:|---|
| `GRAPH_API_VERSION` | `v22.0` | Override when upgrading the Meta Graph API version |
| `MEDIA_BRANCH` | `main` | Branch containing public media |
| `HTTP_TIMEOUT_SECONDS` | `90` | Request timeout |
| `PROCESSING_POLL_SECONDS` | `30` | Instagram processing poll interval |
| `PROCESSING_MAX_ATTEMPTS` | `20` | Maximum Instagram processing checks |
| `PLATFORM_DELAY_SECONDS` | `15` | Delay between Facebook and Instagram |
| `MEDIA_DELAY_SECONDS` | `30` | Delay between image and video |

The workflow runs once daily at 6:00 PM IST, posts one image and one reel when available, runs tests first, and commits only `posted.txt` plus `content_state.json`. A concurrency lock prevents overlapping runs.

## Editing content safely

Edit values in `content_plan.json`; do not remove required keys. Keep the 10-item `distribution_cycle` at exactly four `educational`, three `student_success`, two `admission`, and one `trending_funny` entries. Run the tests before committing.

The required reel ending is intentionally appended after hashtags, so it remains the literal final sentence of every reel caption.
