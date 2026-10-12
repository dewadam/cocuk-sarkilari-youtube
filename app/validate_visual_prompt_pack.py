"""Validate generated scene prompts and character bibles before artifact upload."""
from __future__ import annotations

import argparse
from pathlib import Path


def validate(root: Path, song_id: str | None = None) -> list[str]:
    errors: list[str] = []
    folders = [root / song_id] if song_id else sorted(p for p in root.iterdir() if p.is_dir())
    if not folders or any(not p.is_dir() for p in folders):
        return [f"Görsel istem paketi klasörü bulunamadı: {root}"]
    for folder in folders:
        bible_path = folder / "character_bible.md"
        readme_path = folder / "README.md"
        prompts = sorted(folder.glob("scene_*_prompt.txt"))
        if not bible_path.is_file():
            errors.append(f"{folder.name}: character_bible.md eksik")
            continue
        if not readme_path.is_file():
            errors.append(f"{folder.name}: README.md eksik")
        bible = bible_path.read_text(encoding="utf-8")
        if "Ana karakter" not in bible or "sabit tutulacak kurallar" not in bible:
            errors.append(f"{folder.name}: karakter rehberi eksik veya bozuk")
        if "Henüz karakter tasarımı tanımlı değildir" in bible:
            errors.append(f"{folder.name}: eski boş karakter rehberi bulundu")
        if len(prompts) < 6:
            errors.append(f"{folder.name}: en az 6 sahne istemi bekleniyor, bulunan {len(prompts)}")
        for prompt_path in prompts:
            prompt = prompt_path.read_text(encoding="utf-8")
            for required in ("CHARACTER DESIGN LOCK", "Vertical 9:16", "No text"):
                if required.casefold() not in prompt.casefold():
                    errors.append(f"{folder.name}/{prompt_path.name}: '{required}' ifadesi eksik")
                    break
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default="output/visual-prompt-pack")
    parser.add_argument("--song-id")
    args = parser.parse_args()
    errors = validate(Path(args.input_dir), args.song_id)
    if errors:
        print("Görsel istem paketi kontrolü başarısız:")
        print("\\n".join(f"- {error}" for error in errors))
        return 1
    print("Görsel istem paketi kontrolü başarılı: karakter rehberi ve sahne istemleri tutarlı.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
