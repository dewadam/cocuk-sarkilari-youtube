import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from prepare_video import inspect_library  # noqa: E402


class VideoPreflightTests(unittest.TestCase):
    def make_package(self, root: Path, *, status="ready", usage="available",
                     with_audio=True, lyrics_match=True, audio_bytes=b"unique-audio"):
        folder = root / "songs" / "TR001_Test"
        folder.mkdir(parents=True)
        (folder / "lyrics.txt").write_text("Merhaba dünya", encoding="utf-8")
        if with_audio:
            (folder / "song.mp3").write_bytes(audio_bytes)
        metadata = {
            "id": "TR001",
            "title": "Test Şarkısı",
            "status": status,
            "usage_status": usage,
            "audio_file": "song.mp3",
            "lyrics_file": "lyrics.txt",
            "lyrics_must_match_final_audio": lyrics_match,
            "used_in_video_id": None,
        }
        (folder / "metadata.json").write_text(
            json.dumps(metadata), encoding="utf-8"
        )
        return folder

    def test_ready_unused_package_is_eligible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_package(root)
            report = inspect_library(root)
            self.assertEqual(report["eligible_count"], 1)
            self.assertEqual(report["selected_song"]["id"], "TR001")

    def test_unchecked_lyrics_still_allow_visual_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_package(root, status="audio_uploaded_lyrics_check")
            report = inspect_library(root)
            self.assertEqual(report["eligible_count"], 1)
            self.assertTrue(report["selected_song"]["preview_only"])

    def test_used_song_is_not_eligible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_package(root, usage="used")
            report = inspect_library(root)
            self.assertEqual(report["eligible_count"], 0)

    def test_missing_audio_is_not_eligible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_package(root, with_audio=False)
            report = inspect_library(root)
            self.assertEqual(report["eligible_count"], 0)
            self.assertIn("song.mp3 eksik", report["packages"][0]["blockers"])


if __name__ == "__main__":
    unittest.main()
