import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from run_pipeline_dry_run import run_pipeline


class PipelineDryRunTests(unittest.TestCase):
    def test_missing_song_folder_stops_cleanly(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = run_pipeline(Path(tmp), "TR099")
        self.assertFalse(report["passed"])
        self.assertFalse(report["youtube_upload_enabled"])
        self.assertIn("klasörü bulunamadı", report["blockers"][0])

    def test_unready_song_stops_before_visual_steps(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "songs" / "TR009_Test"
            folder.mkdir(parents=True)
            (folder / "song.mp3").write_bytes(b"same")
            (folder / "lyrics.txt").write_text("test", encoding="utf-8")
            (folder / "metadata.json").write_text(json.dumps({
                "id": "TR009", "title": "Test", "status": "audio_uploaded_lyrics_check",
                "usage_status": "available", "audio_file": "song.mp3", "lyrics_file": "lyrics.txt"
            }), encoding="utf-8")
            report = run_pipeline(root, "TR009")
        self.assertFalse(report["passed"])
        self.assertEqual(len(report["steps"]), 1)
        self.assertIn("status", " ".join(report["blockers"]))

if __name__ == "__main__":
    unittest.main()
