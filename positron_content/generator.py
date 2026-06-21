"""Deterministic, validated social content generation for Positron Academy."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


INSTAGRAM_CAPTION_LIMIT = 2_200
EXPECTED_DISTRIBUTION = {
    "educational": 4,
    "student_success": 3,
    "admission": 2,
    "trending_funny": 1,
}


@dataclass(frozen=True)
class GeneratedCaption:
    """A caption and the metadata used to generate it."""

    index: int
    category: str
    category_label: str
    course_key: str
    course_name: str
    template_name: str
    media_type: str
    hook: str
    value: str
    cta: str
    hashtags: str
    caption: str


class ContentState:
    """Persists the next successful-post index using an atomic file replace."""

    def __init__(self, path: Path | str = "content_state.json") -> None:
        self.path = Path(path)
        self.next_index = 0
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.next_index = max(0, int(data.get("next_index", 0)))
        except (json.JSONDecodeError, OSError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid content state at {self.path}: {exc}") from exc

    def advance(self) -> None:
        self.next_index += 1
        self.save()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary_path.write_text(
            json.dumps({"next_index": self.next_index}, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary_path, self.path)


class ContentGenerator:
    """Builds captions from the editable strategy in ``content_plan.json``."""

    def __init__(self, config_path: Path | str = "content_plan.json") -> None:
        self.config_path = Path(config_path)
        try:
            self.config: Dict[str, Any] = json.loads(
                self.config_path.read_text(encoding="utf-8")
            )
        except (json.JSONDecodeError, OSError) as exc:
            raise ValueError(f"Unable to load content plan {self.config_path}: {exc}") from exc
        self.validate_config()

    def validate_config(self) -> None:
        cycle: List[str] = self.config.get("distribution_cycle", [])
        counts = {category: cycle.count(category) for category in EXPECTED_DISTRIBUTION}
        if len(cycle) != 10 or counts != EXPECTED_DISTRIBUTION:
            raise ValueError(
                "distribution_cycle must contain exactly 10 entries with a 4/3/2/1 split"
            )

        categories = self.config.get("category_templates", {})
        missing_categories = set(EXPECTED_DISTRIBUTION) - set(categories)
        if missing_categories:
            raise ValueError(f"Missing category templates: {sorted(missing_categories)}")

        courses = self.config.get("courses", [])
        expected_templates = {
            "PTI Admission",
            "BSTC Admission",
            "B.Ed Admission",
            "ANM Admission",
            "CET Preparation",
        }
        actual_templates = {course.get("template_name") for course in courses}
        if actual_templates != expected_templates:
            raise ValueError("All five required reusable course templates must be configured")

        hashtags = self.config.get("local_hashtags", [])
        if len(hashtags) != 8 or any(not tag.startswith("#") for tag in hashtags):
            raise ValueError("Exactly eight valid local hashtags are required")

        if not self.config.get("reel_ending"):
            raise ValueError("A reel ending is required")

    def generate(self, index: int, media_type: str) -> GeneratedCaption:
        """Generate one validated image or reel caption for a sequence index."""

        if index < 0:
            raise ValueError("index cannot be negative")
        if media_type not in {"image", "reel"}:
            raise ValueError("media_type must be 'image' or 'reel'")

        cycle = self.config["distribution_cycle"]
        courses = self.config["courses"]
        category = cycle[index % len(cycle)]
        course = courses[index % len(courses)]
        category_template = self.config["category_templates"][category]

        # Each full distribution cycle moves to the next wording variant.
        variant_index = (index // len(cycle)) % len(category_template["hooks"])
        fields = dict(course)
        fields["course"] = course["display_name"]
        hook = category_template["hooks"][variant_index].format(**fields)
        value = category_template["values"][variant_index].format(**fields)

        academy = self.config["academy"]
        cta_lines = [line.format(**academy) for line in self.config["cta"]]
        cta = "\n".join(cta_lines)
        hashtags = " ".join(self.config["local_hashtags"])

        sections = [hook, value, cta, hashtags]
        if media_type == "reel":
            sections.append(self.config["reel_ending"])
        caption = "\n\n".join(sections)

        generated = GeneratedCaption(
            index=index,
            category=category,
            category_label=category_template["label"],
            course_key=course["key"],
            course_name=course["display_name"],
            template_name=course["template_name"],
            media_type=media_type,
            hook=hook,
            value=value,
            cta=cta,
            hashtags=hashtags,
            caption=caption,
        )
        self.validate_caption(generated)
        return generated

    def validate_caption(self, generated: GeneratedCaption) -> None:
        """Fail closed if a required caption component is missing."""

        caption = generated.caption
        if not generated.hook or not generated.value:
            raise ValueError("Caption hook and value are required")
        if generated.cta not in caption:
            raise ValueError("Caption CTA is missing")
        for hashtag in self.config["local_hashtags"]:
            if hashtag not in caption:
                raise ValueError(f"Caption is missing local hashtag {hashtag}")
        if generated.media_type == "reel" and not caption.endswith(
            self.config["reel_ending"]
        ):
            raise ValueError("Reel caption does not end with the required sentence")
        if len(caption) > INSTAGRAM_CAPTION_LIMIT:
            raise ValueError(
                f"Caption has {len(caption)} characters; Instagram limit is {INSTAGRAM_CAPTION_LIMIT}"
            )

    def strategy_summary(self) -> Dict[str, Any]:
        """Return the profile and engagement playbook for other tools or UIs."""

        return {
            "profile_optimization": self.config["profile_optimization"],
            "engagement": self.config["engagement"],
        }
