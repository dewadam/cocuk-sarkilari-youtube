import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from build_storyboards import build_storyboard  # noqa: E402


class StoryboardDraftTests(unittest.TestCase):
    def test_storyboard_is_vertical_and_has_timed_scenes(self):
        topic = {
            "id": "TR001",
            "theme": "Renkler Bahçesi",
            "learning_goal": "Temel renkleri tanıma",
            "visual_motifs": ["kırmızı balon", "sarı güneş", "mavi uçurtma"],
        }
        project = {
            "language": "tr-TR",
            "visual_style": "stylized_high_quality_3d",
            "target_duration_seconds": {"min": 90, "max": 150},
        }
        with tempfile.TemporaryDirectory() as tmp:
            storyboard = build_storyboard(topic, Path(tmp), project)
        self.assertEqual(storyboard["aspect_ratio"], "9:16")
        self.assertEqual(len(storyboard["scenes"]), 6)
        self.assertEqual(storyboard["scenes"][0]["start_seconds"], 0)
        self.assertEqual(
            storyboard["scenes"][-1]["end_seconds"],
            storyboard["duration_seconds"],
        )
        self.assertTrue(storyboard["duration_is_provisional"])
        self.assertIn("image_generation_prompt", storyboard["scenes"][0])
        self.assertIn("lyric_cue_draft", storyboard["scenes"][0])


if __name__ == "__main__":
    unittest.main()
