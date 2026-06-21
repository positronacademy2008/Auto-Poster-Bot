"""Publish Positron Academy media with a validated content strategy."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Set
from urllib.parse import quote

import requests

from positron_content import ContentGenerator, ContentState, GeneratedCaption


BASE_DIR = Path(__file__).resolve().parent
VIDEO_FOLDER = BASE_DIR / "video"
IMAGE_FOLDER = BASE_DIR / "images"
POSTED_FILE = BASE_DIR / "posted.txt"
CONTENT_PLAN_FILE = BASE_DIR / "content_plan.json"
CONTENT_STATE_FILE = BASE_DIR / "content_state.json"

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}

FB_PAGE_ID = os.getenv("FB_PAGE_ID", "").strip()
ACCESS_TOKEN = os.getenv("FB_PAGE_TOKEN", "").strip()
IG_ACCOUNT_ID = os.getenv("IG_ACCOUNT_ID", "").strip()
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY", "").strip()
MEDIA_BRANCH = os.getenv("MEDIA_BRANCH", "main").strip()
GRAPH_API_VERSION = os.getenv("GRAPH_API_VERSION", "v22.0").strip()

HTTP_TIMEOUT_SECONDS = int(os.getenv("HTTP_TIMEOUT_SECONDS", "90"))
PLATFORM_DELAY_SECONDS = int(os.getenv("PLATFORM_DELAY_SECONDS", "15"))
MEDIA_DELAY_SECONDS = int(os.getenv("MEDIA_DELAY_SECONDS", "30"))
PROCESSING_POLL_SECONDS = int(os.getenv("PROCESSING_POLL_SECONDS", "30"))
PROCESSING_MAX_ATTEMPTS = int(os.getenv("PROCESSING_MAX_ATTEMPTS", "20"))

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(message)s",
)
LOGGER = logging.getLogger("positron-auto-poster")
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "PositronAcademyAutoPoster/2.0"})

# Windows shells commonly default to cp1252, which cannot print Hindi-content
# emoji. UTF-8 keeps previews and redirected logs portable across environments.
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8")


class GraphAPIError(RuntimeError):
    """A sanitized Meta Graph API error."""


def graph_request(method: str, url: str, **kwargs: Any) -> Dict[str, Any]:
    """Call the Graph API and return JSON without ever logging credentials."""

    try:
        response = SESSION.request(
            method,
            url,
            timeout=HTTP_TIMEOUT_SECONDS,
            **kwargs,
        )
    except requests.RequestException as exc:
        raise GraphAPIError(f"Network request failed: {exc}") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise GraphAPIError(
            f"Graph API returned HTTP {response.status_code} with non-JSON content"
        ) from exc

    if not response.ok or "error" in payload:
        error = payload.get("error", {})
        message = error.get("message", payload)
        code = error.get("code", "unknown")
        raise GraphAPIError(
            f"Graph API HTTP {response.status_code}, code {code}: {message}"
        )
    return payload


def raw_media_url(folder: str, filename: str) -> str:
    """Return the public raw GitHub URL used by Meta to fetch an asset."""

    if not GITHUB_REPOSITORY:
        raise ValueError("GITHUB_REPOSITORY is required for remote media publishing")
    safe_path = "/".join(quote(part, safe="") for part in (folder, filename))
    safe_branch = quote(MEDIA_BRANCH, safe="")
    return (
        f"https://raw.githubusercontent.com/{GITHUB_REPOSITORY}/"
        f"{safe_branch}/{safe_path}"
    )


def get_posted_files() -> Set[str]:
    if not POSTED_FILE.exists():
        return set()
    return {
        line.strip()
        for line in POSTED_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def save_posted_files(posted: Iterable[str]) -> None:
    """Persist posted media atomically to avoid a half-written progress file."""

    temporary_path = POSTED_FILE.with_suffix(".txt.tmp")
    content = "".join(f"{item}\n" for item in sorted(set(posted)))
    temporary_path.write_text(content, encoding="utf-8")
    os.replace(temporary_path, POSTED_FILE)


def media_key(folder: str, filename: str) -> str:
    return f"{folder}/{filename}"


def was_posted(posted: Set[str], folder: str, filename: str) -> bool:
    # Bare filenames keep compatibility with the original posted.txt format.
    return media_key(folder, filename) in posted or filename in posted


def reset_completed_loop(
    posted: Set[str], folder: str, all_files: list[str], pending: list[str]
) -> list[str]:
    if not all_files or pending:
        return pending
    LOGGER.info("Resetting completed %s media loop", folder)
    for filename in all_files:
        posted.discard(media_key(folder, filename))
        posted.discard(filename)
    return all_files.copy()


def list_media(folder: Path, extensions: Set[str]) -> list[str]:
    if not folder.exists():
        LOGGER.warning("Media folder not found: %s", folder)
        return []
    return sorted(
        path.name
        for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() in extensions
    )


def wait_until_instagram_media_ready(creation_id: str) -> bool:
    status_url = (
        f"https://graph.facebook.com/{GRAPH_API_VERSION}/{creation_id}"
    )
    for attempt in range(1, PROCESSING_MAX_ATTEMPTS + 1):
        status = graph_request(
            "GET",
            status_url,
            params={"fields": "status_code", "access_token": ACCESS_TOKEN},
        ).get("status_code")
        LOGGER.info(
            "Instagram processing status %s (attempt %s/%s)",
            status,
            attempt,
            PROCESSING_MAX_ATTEMPTS,
        )
        if status == "FINISHED":
            return True
        if status in {"ERROR", "EXPIRED"}:
            return False
        if attempt < PROCESSING_MAX_ATTEMPTS:
            time.sleep(PROCESSING_POLL_SECONDS)
    return False


def post_to_instagram(
    folder: str,
    filename: str,
    is_video: bool,
    generated: GeneratedCaption,
) -> bool:
    if not IG_ACCOUNT_ID:
        LOGGER.info("Instagram skipped: IG_ACCOUNT_ID is not configured")
        return False
    try:
        media_url = raw_media_url(folder, filename)
        account_url = (
            f"https://graph.facebook.com/{GRAPH_API_VERSION}/{IG_ACCOUNT_ID}"
        )
        payload: Dict[str, str] = {
            "caption": generated.caption,
            "access_token": ACCESS_TOKEN,
        }
        if is_video:
            payload.update({"media_type": "REELS", "video_url": media_url})
        else:
            payload["image_url"] = media_url

        LOGGER.info(
            "Instagram: creating %s for %s [%s / %s]",
            "reel" if is_video else "image",
            filename,
            generated.category_label,
            generated.template_name,
        )
        creation_id = graph_request(
            "POST", f"{account_url}/media", data=payload
        ).get("id")
        if not creation_id:
            raise GraphAPIError("Instagram did not return a creation ID")

        if not wait_until_instagram_media_ready(creation_id):
            raise GraphAPIError(
                "Instagram media did not finish processing; it was not force-published"
            )

        publication = graph_request(
            "POST",
            f"{account_url}/media_publish",
            data={"creation_id": creation_id, "access_token": ACCESS_TOKEN},
        )
        LOGGER.info("Instagram publish succeeded: %s", publication.get("id"))
        return True
    except (GraphAPIError, OSError, ValueError) as exc:
        LOGGER.error("Instagram publish failed for %s: %s", filename, exc)
        return False


def post_to_facebook(
    folder: str,
    filename: str,
    is_video: bool,
    generated: GeneratedCaption,
) -> bool:
    if not FB_PAGE_ID:
        LOGGER.info("Facebook skipped: FB_PAGE_ID is not configured")
        return False
    try:
        page_url = (
            f"https://graph.facebook.com/{GRAPH_API_VERSION}/{FB_PAGE_ID}"
        )
        if is_video:
            response = graph_request(
                "POST",
                f"{page_url}/videos",
                data={
                    "description": generated.caption,
                    "file_url": raw_media_url(folder, filename),
                    "access_token": ACCESS_TOKEN,
                },
            )
        else:
            local_path = BASE_DIR / folder / filename
            with local_path.open("rb") as media_file:
                response = graph_request(
                    "POST",
                    f"{page_url}/photos",
                    data={
                        "caption": generated.caption,
                        "access_token": ACCESS_TOKEN,
                    },
                    files={"source": media_file},
                )
        LOGGER.info(
            "Facebook publish succeeded for %s [%s / %s]: %s",
            filename,
            generated.category_label,
            generated.template_name,
            response.get("id"),
        )
        return True
    except (GraphAPIError, OSError, ValueError) as exc:
        LOGGER.error("Facebook publish failed for %s: %s", filename, exc)
        return False


def publish_asset(
    folder: str,
    filename: str,
    is_video: bool,
    generated: GeneratedCaption,
) -> bool:
    facebook_success = post_to_facebook(folder, filename, is_video, generated)
    if FB_PAGE_ID and IG_ACCOUNT_ID and PLATFORM_DELAY_SECONDS:
        LOGGER.info("Waiting %s seconds between platforms", PLATFORM_DELAY_SECONDS)
        time.sleep(PLATFORM_DELAY_SECONDS)
    instagram_success = post_to_instagram(folder, filename, is_video, generated)
    return facebook_success or instagram_success


def run_live() -> int:
    if not ACCESS_TOKEN:
        LOGGER.error("FB_PAGE_TOKEN is required")
        return 2
    if not FB_PAGE_ID and not IG_ACCOUNT_ID:
        LOGGER.error("Configure FB_PAGE_ID, IG_ACCOUNT_ID, or both")
        return 2

    generator = ContentGenerator(CONTENT_PLAN_FILE)
    state = ContentState(CONTENT_STATE_FILE)
    posted = get_posted_files()

    all_images = list_media(IMAGE_FOLDER, IMAGE_EXTENSIONS)
    all_videos = list_media(VIDEO_FOLDER, VIDEO_EXTENSIONS)
    pending_images = [
        name for name in all_images if not was_posted(posted, "images", name)
    ]
    pending_videos = [
        name for name in all_videos if not was_posted(posted, "video", name)
    ]

    pending_images = reset_completed_loop(
        posted, "images", all_images, pending_images
    )
    pending_videos = reset_completed_loop(posted, "video", all_videos, pending_videos)
    save_posted_files(posted)

    published_any = False
    queue = [
        ("images", pending_images[0], False) if pending_images else None,
        ("video", pending_videos[0], True) if pending_videos else None,
    ]
    for queue_index, item in enumerate(filter(None, queue)):
        folder, filename, is_video = item
        generated = generator.generate(
            state.next_index, "reel" if is_video else "image"
        )
        LOGGER.info(
            "Selected content #%s: %s / %s",
            generated.index,
            generated.category_label,
            generated.template_name,
        )
        if publish_asset(folder, filename, is_video, generated):
            posted.add(media_key(folder, filename))
            save_posted_files(posted)
            state.advance()
            published_any = True

        if queue_index == 0 and pending_images and pending_videos and MEDIA_DELAY_SECONDS:
            LOGGER.info("Waiting %s seconds before the next media item", MEDIA_DELAY_SECONDS)
            time.sleep(MEDIA_DELAY_SECONDS)

    if not any(queue):
        LOGGER.warning("No supported files were found in images/ or video/")
    return 0 if published_any or not any(queue) else 1


def run_preview(count: int, media_type: str, start_index: int) -> int:
    generator = ContentGenerator(CONTENT_PLAN_FILE)
    for offset in range(count):
        index = start_index + offset
        selected_type = media_type
        if media_type == "alternating":
            selected_type = "image" if offset % 2 == 0 else "reel"
        generated = generator.generate(index, selected_type)
        print(
            f"\n=== #{index} | {generated.category_label} | "
            f"{generated.template_name} | {selected_type.upper()} ===\n"
        )
        print(generated.caption)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Print generated captions without publishing or changing progress",
    )
    parser.add_argument("--count", type=int, default=10, help="Preview caption count")
    parser.add_argument(
        "--media-type",
        choices=("image", "reel", "alternating"),
        default="alternating",
        help="Media type used by preview mode",
    )
    parser.add_argument(
        "--start-index", type=int, default=0, help="First sequence index for preview"
    )
    parser.add_argument(
        "--strategy",
        action="store_true",
        help="Print profile optimization and engagement suggestions as JSON",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.count < 1:
        LOGGER.error("--count must be at least 1")
        return 2
    if args.start_index < 0:
        LOGGER.error("--start-index cannot be negative")
        return 2
    if args.strategy:
        generator = ContentGenerator(CONTENT_PLAN_FILE)
        print(json.dumps(generator.strategy_summary(), ensure_ascii=False, indent=2))
        return 0
    if args.preview:
        return run_preview(args.count, args.media_type, args.start_index)
    return run_live()


if __name__ == "__main__":
    sys.exit(main())
