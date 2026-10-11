import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from validate_assets import validate_assets, validate_srt  # noqa: E402


class AssetPreflightTests(unittest.TestCase):
    def make_package(self, root: Path, scene_count: int = 6) -> Path:
        folder = root / "songs" / "TR009_Test"
        visuals = folder / "visuals"
        visuals.mkdir(parents=True)
        (folder / "song.mp3").write_bytes(b"placeholder")
        (folder / "metadata.json").write_text(
            '{"id":"TR009","audio_file":"song.mp3"}', encoding="utf-8"
        )
        for number in range(1, scene_count + 1):
            (visuals / f"scene_{number:02d}.png").write_bytes(b"placeholder")
        return folder

    def test_six_contiguous_scenes_pass_without_captions(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = self.make_package(Path(tmp))
            report = validate_assets(folder)
        self.assertTrue(report["passed"], report["errors"])
        self.assertEqual(report["scene_count"], 6)
        self.assertTrue(report["warnings"])

    def test_scene_number_gap_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = self.make_package(Path(tmp))
            (folder / "visuals" / "scene_03.png").unlink()
            (folder / "visuals" / "scene_07.png").write_bytes(b"placeholder")
            report = validate_assets(folder)
        self.assertFalse(report["passed"])
        self.assertTrue(any("kesintisiz" in error for error in report["errors"]))

    def test_bad_srt_timing_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = self.make_package(Path(tmp))
            (folder / "captions.srt").write_text(
                "1\n00:00:03,000 --> 00:00:02,000\nMerhaba\n", encoding="utf-8"
            )
            report = validate_assets(folder)
        self.assertFalse(report["passed"])
        self.assertTrue(any("bitiş zamanı" in error for error in report["errors"]))

    def test_valid_srt_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "captions.srt"
            path.write_text(
                "1\n00:00:00,500 --> 00:00:01,500\nMerhaba\n\n"
                "2\n00:00:01,600 --> 00:00:02,500\nDünya\n", encoding="utf-8"
            )
            self.assertEqual(validate_srt(path), [])


if __name__ == "__main__":
    unittest.main()
