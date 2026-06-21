import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from positron_content import ContentGenerator, ContentState


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "content_plan.json"


class ContentGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generator = ContentGenerator(PLAN_PATH)
        cls.plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))

    def test_distribution_is_exact_over_every_full_cycle(self):
        categories = [
            self.generator.generate(index, "reel").category for index in range(10)
        ]
        self.assertEqual(
            Counter(categories),
            Counter(
                {
                    "educational": 4,
                    "student_success": 3,
                    "admission": 2,
                    "trending_funny": 1,
                }
            ),
        )

    def test_every_reel_ends_with_required_sentence(self):
        required_ending = self.plan["reel_ending"]
        for index in range(30):
            with self.subTest(index=index):
                generated = self.generator.generate(index, "reel")
                self.assertTrue(generated.caption.endswith(required_ending))

    def test_normal_image_reel_pairing_makes_all_educational_posts_reels(self):
        for index in range(10):
            media_type = "image" if index % 2 == 0 else "reel"
            generated = self.generator.generate(index, media_type)
            if generated.category == "educational":
                self.assertEqual(generated.media_type, "reel")

    def test_every_caption_contains_hook_value_cta_and_local_hashtags(self):
        for media_type in ("image", "reel"):
            for index in range(30):
                with self.subTest(media_type=media_type, index=index):
                    generated = self.generator.generate(index, media_type)
                    self.assertIn(generated.hook, generated.caption)
                    self.assertIn(generated.value, generated.caption)
                    self.assertIn("Follow karein", generated.caption)
                    self.assertIn("DM karein", generated.caption)
                    self.assertIn("WhatsApp karein", generated.caption)
                    for hashtag in self.plan["local_hashtags"]:
                        self.assertIn(hashtag, generated.caption)
                    self.assertLessEqual(len(generated.caption), 2_200)

    def test_all_required_course_templates_are_rotated(self):
        templates = {
            self.generator.generate(index, "image").template_name
            for index in range(5)
        }
        self.assertEqual(
            templates,
            {
                "PTI Admission",
                "BSTC Admission",
                "B.Ed Admission",
                "ANM Admission",
                "CET Preparation",
            },
        )

    def test_wording_changes_between_distribution_cycles(self):
        first = self.generator.generate(0, "reel")
        second = self.generator.generate(10, "reel")
        self.assertEqual(first.category, second.category)
        self.assertEqual(first.course_key, second.course_key)
        self.assertNotEqual(first.hook, second.hook)
        self.assertNotEqual(first.value, second.value)

    def test_strategy_contains_requested_engagement_sections(self):
        strategy = self.generator.strategy_summary()
        self.assertGreaterEqual(len(strategy["profile_optimization"]), 5)
        engagement = strategy["engagement"]
        for section in (
            "poll_ideas",
            "story_ideas",
            "daily_posting_recommendations",
            "reel_topic_suggestions",
        ):
            self.assertTrue(engagement[section])


class ContentStateTests(unittest.TestCase):
    def test_state_advances_and_persists(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "state.json"
            state = ContentState(path)
            self.assertEqual(state.next_index, 0)
            state.advance()
            self.assertEqual(ContentState(path).next_index, 1)


if __name__ == "__main__":
    unittest.main()
