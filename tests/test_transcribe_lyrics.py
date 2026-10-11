import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from transcribe_lyrics import generate_draft, segments_to_srt, srt_timestamp  # noqa: E402


class FakeSegment:
    def __init__(self, start, end, text):
        self.start = start
        self.end = end
        self.text = text


class CaptionDraftTests(unittest.TestCase):
    def test_timestamp_rounding(self):
        self.assertEqual(srt_timestamp(61.2346), "00:01:01,235")

    def test_segments_become_valid_sequential_srt(self):
        srt = segments_to_srt([
            FakeSegment(0.0, 1.25, " Merhaba dünya "),
            FakeSegment(1.0, 2.0, "Nasılsın?"),
            FakeSegment(2.1, 2.1, "İyiyim."),
        ])
        self.assertIn("1\n00:00:00,000 --> 00:00:01,250\nMerhaba dünya", srt)
        self.assertIn("2\n00:00:01,250 --> 00:00:02,000\nNasılsın?", srt)
        self.assertIn("3\n00:00:02,100 --> 00:00:02,180\nİyiyim.", srt)

    def test_missing_audio_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(FileNotFoundError):
                generate_draft(root / "missing.mp3", root / "draft.srt", root / "report.json")

    def test_report_explicitly_requires_human_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio = root / "song.mp3"
            audio.write_bytes(b"fake audio")
            fake_info = types.SimpleNamespace(language="tr", language_probability=0.98)

            class FakeModel:
                def __init__(self, *args, **kwargs):
                    pass

                def transcribe(self, *args, **kwargs):
                    return iter([FakeSegment(0.1, 1.0, "Merhaba dünya")]), fake_info

            fake_module = types.SimpleNamespace(WhisperModel=FakeModel)
            with patch.dict(sys.modules, {"faster_whisper": fake_module}):
                report = generate_draft(audio, root / "draft.srt", root / "report.json")

            self.assertFalse(report["verified"])
            self.assertEqual(report["status"], "draft_requires_human_review")
            self.assertTrue((root / "draft.srt").is_file())
            saved = json.loads((root / "report.json").read_text(encoding="utf-8"))
            self.assertFalse(saved["verified"])
            self.assertEqual(saved["caption_count"], 1)


if __name__ == "__main__":
    unittest.main()
