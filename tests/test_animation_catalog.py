import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from animation_catalog import normalize, score_clip, validate_clip

class AnimationCatalogTests(unittest.TestCase):
    def test_turkish_normalization(self):
        self.assertEqual(normalize("Tavşan zıplıyor, ÇİFTLİK!"), "tavsan zipliyor ciftlik")

    def test_keyword_match_ranks(self):
        clip = {
            "category": "hayvan", "tags": ["tavşan", "zıplama"],
            "keywords": ["tavşan zıplıyor"], "characters": ["tavşan"],
            "actions": ["zıplama"], "environments": ["çiftlik"], "moods": ["neşeli"]
        }
        score, matched = score_clip(clip, "Tavşan çiftlikte zıplıyor")
        self.assertGreater(score, 0)
        self.assertTrue(matched)

    def test_clip_schema_requires_asset_url(self):
        errors = validate_clip({
            "clip_id":"ANIM_001", "file_name":"rabbit.mp4", "category":"animal",
            "tags":["rabbit"], "keywords":["rabbit hop"], "duration_seconds":30,
            "loopable":True, "asset_url":"https://github.com/example/repo/releases/download/x/rabbit.mp4"
        })
        self.assertEqual(errors, [])

if __name__ == "__main__":
    unittest.main()
