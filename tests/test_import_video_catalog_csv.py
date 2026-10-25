import csv, json, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "app" / "import_video_catalog_csv.py"

class TestImportVideoCatalogCSV(unittest.TestCase):
    def test_matches_real_files_and_reports_missing_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            csv_path = base / "video_catalog_500.csv"
            inbox = base / "inbox" / "RENKLER"
            inbox.mkdir(parents=True)
            out = base / "upload_batch"
            with csv_path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "video_id","theme_code","theme_tr","scene_no","title_tr","character",
                    "setting","learning_goal_tr","duration_target_sec","aspect_ratio",
                    "prompt_seg1","prompt_seg2","prompt_seg3","prompt_seg4","prompt_seg5",
                    "negative_prompt","tags","loopable"
                ])
                writer.writeheader()
                writer.writerow({
                    "video_id":"CLIP001","theme_code":"RENKLER","theme_tr":"Renkler",
                    "scene_no":"1","title_tr":"Kırmızı Laleler","character":"duckling",
                    "setting":"red tulips","learning_goal_tr":"Renkleri tanımak",
                    "duration_target_sec":"30","aspect_ratio":"9:16",
                    "prompt_seg1":"A chubby duckling waves hello and hops happily.","prompt_seg2":"two","prompt_seg3":"three",
                    "prompt_seg4":"four","prompt_seg5":"five","negative_prompt":"blur",
                    "tags":"çocuk şarkısı; renkler","loopable":"yes"
                })
                writer.writerow({
                    "video_id":"CLIP002","theme_code":"RENKLER","theme_tr":"Renkler",
                    "scene_no":"1","title_tr":"Mavi Kelebekler","character":"duckling",
                    "setting":"blue flowers","learning_goal_tr":"Renkleri tanımak",
                    "duration_target_sec":"30","aspect_ratio":"9:16",
                    "prompt_seg1":"one","prompt_seg2":"two","prompt_seg3":"three",
                    "prompt_seg4":"four","prompt_seg5":"five","negative_prompt":"blur",
                    "tags":"çocuk şarkısı; renkler","loopable":"yes"
                })
            (inbox / "CLIP001.mp4").write_bytes(b"fake-mp4-test-data")
            result = subprocess.run([
                sys.executable, str(SCRIPT), "--csv", str(csv_path),
                "--inbox", str(base / "inbox"), "--out", str(out)
            ], capture_output=True, text=True, check=True)
            report = json.loads((out / "import-report.json").read_text(encoding="utf-8"))
            sidecar = json.loads((out / "CLIP001.json").read_text(encoding="utf-8"))
            self.assertEqual(report["csv_records"], 2)
            self.assertEqual(report["found_video_files"], 1)
            self.assertEqual(report["missing_video_ids"], ["CLIP002"])
            self.assertFalse(sidecar["approved"])
            self.assertIn("el sallama", sidecar["actions"])
            self.assertIn("zıplama", sidecar["actions"])
            self.assertEqual(sidecar["asset_url"], "")
            self.assertTrue((out / "CLIP001.mp4").is_file())

if __name__ == "__main__":
    unittest.main()
