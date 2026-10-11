import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import subprocess

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from validate_render import validate_render  # noqa: E402


class RenderValidationTests(unittest.TestCase):
    def test_missing_file_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = validate_render(Path(tmp) / "missing.mp4")
        self.assertFalse(result["passed"])
        self.assertIn("MP4 dosyası bulunamadı.", result["errors"])

    def test_valid_vertical_video_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "preview.mp4"
            path.write_bytes(b"fake mp4 bytes")
            payload = {
                "streams": [
                    {"codec_type": "video", "codec_name": "h264", "width": 1080, "height": 1920, "duration": "12.0"},
                    {"codec_type": "audio", "codec_name": "aac", "duration": "12.0"},
                ],
                "format": {"duration": "12.0"},
            }
            completed = subprocess.CompletedProcess(args=[], returncode=0, stdout=json.dumps(payload), stderr="")
            with patch("validate_render.subprocess.run", return_value=completed):
                result = validate_render(path)
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["width"], 1080)
        self.assertEqual(result["height"], 1920)

    def test_wrong_resolution_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "preview.mp4"
            path.write_bytes(b"fake mp4 bytes")
            payload = {
                "streams": [
                    {"codec_type": "video", "codec_name": "h264", "width": 1920, "height": 1080},
                    {"codec_type": "audio", "codec_name": "aac", "duration": "12.0"},
                ],
                "format": {"duration": "12.0"},
            }
            completed = subprocess.CompletedProcess(args=[], returncode=0, stdout=json.dumps(payload), stderr="")
            with patch("validate_render.subprocess.run", return_value=completed):
                result = validate_render(path)
        self.assertFalse(result["passed"])
        self.assertTrue(any("Çözünürlük" in item for item in result["errors"]))

    def test_duration_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "preview.mp4"
            path.write_bytes(b"fake mp4 bytes")
            payload = {
                "streams": [
                    {"codec_type": "video", "codec_name": "h264", "width": 1080, "height": 1920},
                    {"codec_type": "audio", "codec_name": "aac", "duration": "10.0"},
                ],
                "format": {"duration": "14.0"},
            }
            completed = subprocess.CompletedProcess(args=[], returncode=0, stdout=json.dumps(payload), stderr="")
            with patch("validate_render.subprocess.run", return_value=completed):
                result = validate_render(path)
        self.assertFalse(result["passed"])
        self.assertTrue(any("süreleri arasındaki fark" in item for item in result["errors"]))


if __name__ == "__main__":
    unittest.main()
