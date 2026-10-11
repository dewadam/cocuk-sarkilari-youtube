import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from validate_music_prompts import validate_new_prompts  # noqa: E402


class MusicPromptValidationTests(unittest.TestCase):
    def make_song(self, root: Path, prompt: str, lyrics: str):
        folder = root / "songs" / "TR009_Test"
        folder.mkdir(parents=True)
        (folder / "lyrics.txt").write_text(lyrics, encoding="utf-8")
        (folder / "music_prompt.txt").write_text(prompt, encoding="utf-8")
        (folder / "metadata.json").write_text(json.dumps({
            "id": "TR009",
            "lyrics_file": "lyrics.txt",
            "music_prompt_file": "music_prompt.txt"
        }), encoding="utf-8")

    def test_full_lyrics_and_style_are_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_song(root, "Müzik tarzı: vals ve akustik gitar\n[ŞARKI SÖZLERİ]\nMerhaba dünya", "Merhaba dünya")
            self.assertEqual(validate_new_prompts(root), [])

    def test_path_only_prompt_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_song(root, "Müzik tarzı: vals ve akustik gitar\nSözler lyrics.txt dosyasındadır.", "Merhaba dünya")
            self.assertTrue(any("tamamı" in error for error in validate_new_prompts(root)))

    def test_missing_style_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_song(root, "[ŞARKI SÖZLERİ]\nMerhaba dünya", "Merhaba dünya")
            self.assertTrue(any("tarz" in error for error in validate_new_prompts(root)))


if __name__ == "__main__":
    unittest.main()
