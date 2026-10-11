import sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
from export_visual_prompt_pack import build_pack

class VisualPromptPackTests(unittest.TestCase):
    def test_pack_contains_scene_prompts_and_character_guide(self):
        data = {"id":"TR009","title":"Minik Bulut","scenes":[
            {"scene":1,"start_seconds":0,"end_seconds":10,"visual_focus":"bulut","image_generation_prompt":"Friendly cloud in a 3D garden."},
            {"scene":2,"start_seconds":10,"end_seconds":20,"visual_focus":"yağmur","image_generation_prompt":"Gentle rain in the same garden."}]}
        with tempfile.TemporaryDirectory() as tmp:
            created = build_pack(data, Path(tmp))
            folder = Path(tmp) / "TR009"
            self.assertTrue((folder / "character_bible.md").is_file())
            self.assertTrue((folder / "scene_01_prompt.txt").is_file())
            self.assertTrue((folder / "scene_02_prompt.txt").is_file())
            self.assertTrue((folder / "README.md").is_file())
            self.assertEqual(len(created), 4)
    def test_empty_prompt_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                build_pack({"id":"TR010","scenes":[{"scene":1,"image_generation_prompt":""}]}, Path(tmp))
if __name__ == "__main__":
    unittest.main()
