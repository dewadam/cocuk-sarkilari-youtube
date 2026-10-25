import json, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "app" / "publish_animation_batch.py"

class TestPublishAnimationBatch(unittest.TestCase):
    def test_refuses_unapproved_clip_before_release_upload(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            batch = base / "batch"
            batch.mkdir()
            (batch / "CLIP001.mp4").write_bytes(b"not-a-real-video-but-nonempty")
            sidecar = {
                "clip_id":"CLIP001","file_name":"CLIP001.mp4","category":"Renkler",
                "tags":["renkler"],"keywords":["kırmızı laleler"],"duration_seconds":30,
                "loopable":True,"asset_url":"","approved":False
            }
            (batch / "CLIP001.json").write_text(json.dumps(sidecar), encoding="utf-8")
            catalog = base / "catalog.json"
            catalog.write_text(json.dumps({
                "schema_version":1,"description":"test","updated_at":None,"clips":[]
            }), encoding="utf-8")
            result = subprocess.run([
                sys.executable, str(SCRIPT), "--batch-dir", str(batch),
                "--repo", "dewadam/cocuk-sarkilari-youtube",
                "--tag", "test-batch-001", "--catalog", str(catalog), "--dry-run"
            ], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("approved must be true", result.stderr)

if __name__ == "__main__":
    unittest.main()
