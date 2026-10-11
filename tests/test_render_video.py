import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from render_video import list_scene_images, find_song_folder  # noqa: E402


class RenderVideoHelpersTests(unittest.TestCase):
    def test_scene_images_sort_numerically(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            visuals = folder / "visuals"
            visuals.mkdir()
            for name in ("scene_10.png", "scene_02.png", "scene_01.jpg", "notes.txt"):
                (visuals / name).write_bytes(b"test")
            self.assertEqual(
                [p.name for p in list_scene_images(folder)],
                ["scene_01.jpg", "scene_02.png", "scene_10.png"],
            )

    def test_missing_visuals_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(list_scene_images(Path(tmp)), [])

    def test_song_folder_is_resolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "songs" / "TR009_Test").mkdir(parents=True)
            self.assertEqual(find_song_folder(root, "TR009").name, "TR009_Test")


if __name__ == "__main__":
    unittest.main()
