"""Validate music prompts for newly added songs (TR009+).

The first eight packages are grandfathered. New packages must embed the full
lyrics directly in the prompt and include an explicit music-style profile.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SONGS = ROOT / "songs"


def normalize(value: str) -> str:
    value = value.casefold().replace("ı", "i")
    return re.sub(r"\s+", " ", value).strip()


def validate_new_prompts(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    style_profiles: dict[str, str] = {}
    for metadata_path in sorted((root / "songs").glob("TR*/metadata.json")):
        folder = metadata_path.parent
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{folder.name}: metadata okunamadı: {exc}")
            continue
        song_id = str(metadata.get("id", folder.name.split("_", 1)[0]))
        number_match = re.fullmatch(r"TR(\d+)", song_id)
        if not number_match or int(number_match.group(1)) < 9:
            continue

        prompt_path = folder / str(metadata.get("music_prompt_file", "music_prompt.txt"))
        lyrics_path = folder / str(metadata.get("lyrics_file", "lyrics.txt"))
        if not prompt_path.is_file():
            errors.append(f"{song_id}: music_prompt.txt eksik.")
            continue
        if not lyrics_path.is_file():
            errors.append(f"{song_id}: lyrics.txt eksik.")
            continue

        prompt = prompt_path.read_text(encoding="utf-8")
        lyrics = lyrics_path.read_text(encoding="utf-8")
        normalized_prompt = normalize(prompt)
        normalized_lyrics = lyric_body(lyrics)
        if not normalized_lyrics or normalized_lyrics not in normalized_prompt:
            errors.append(
                f"{song_id}: lyrics.txt içeriğinin tamamı music_prompt.txt içinde bulunmalı."
            )

        style_line = next(
            (line.strip() for line in prompt.splitlines()
             if re.search(r"(müzik karakteri|müzik tarzı|music style|style profile|ana tür)", line, re.I)),
            "",
        )
        if not style_line:
            errors.append(f"{song_id}: açık bir müzik tarzı/profil satırı eksik.")
        else:
            normalized_style = normalize(style_line)
            if normalized_style in style_profiles:
                errors.append(
                    f"{song_id}: müzik tarzı satırı {style_profiles[normalized_style]} ile birebir aynı; çeşitlendir."
                )
            else:
                style_profiles[normalized_style] = song_id

    return errors


def main() -> int:
    errors = validate_new_prompts()
    if errors:
        print("MÜZİK PROMPT KONTROLÜ BAŞARISIZ:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("MÜZİK PROMPT KONTROLÜ BAŞARILI (TR009+)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
