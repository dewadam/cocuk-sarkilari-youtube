"""Pre-render validation for scene assets and optional SRT captions."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
SRT_TIME = re.compile(
    r"^(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> "
    r"(\d{2}):(\d{2}):(\d{2}),(\d{3})$"
)


def timestamp_ms(value: str) -> int:
    hours, minutes, rest = value.split(":")
    seconds, millis = rest.split(",")
    return ((int(hours) * 60 + int(minutes)) * 60 + int(seconds)) * 1000 + int(millis)


def list_images(folder: Path) -> list[Path]:
    visuals = folder / "visuals"
    if not visuals.is_dir():
        return []
    images = [p for p in visuals.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
    def key(path: Path):
        match = re.search(r"(\d+)", path.stem)
        return (int(match.group(1)) if match else 10**9, path.name.casefold())
    return sorted(images, key=key)


def validate_srt(path: Path) -> list[str]:
    errors = []
    try:
        content = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        return [f"Altyazı dosyası okunamadı: {exc}"]
    blocks = re.split(r"\r?\n\s*\r?\n", content.strip()) if content.strip() else []
    previous_end = -1
    for index, block in enumerate(blocks, start=1):
        lines = block.splitlines()
        if len(lines) < 3:
            errors.append(f"SRT blok {index}: en az sıra numarası, zaman ve metin satırı gerekli.")
            continue
        if not lines[0].strip().isdigit():
            errors.append(f"SRT blok {index}: sıra numarası sayısal değil.")
        match = SRT_TIME.fullmatch(lines[1].strip())
        if not match:
            errors.append(f"SRT blok {index}: zaman biçimi HH:MM:SS,mmm --> HH:MM:SS,mmm olmalı.")
            continue
        start = timestamp_ms(":".join(match.groups()[0:3]) + "," + match.group(4))
        end = timestamp_ms(":".join(match.groups()[4:7]) + "," + match.group(8))
        if end <= start:
            errors.append(f"SRT blok {index}: bitiş zamanı başlangıçtan sonra olmalı.")
        if start < previous_end:
            errors.append(f"SRT blok {index}: altyazı zamanları önceki blokla çakışıyor veya geriye gidiyor.")
        if not any(line.strip() for line in lines[2:]):
            errors.append(f"SRT blok {index}: altyazı metni boş.")
        previous_end = max(previous_end, end)
    if not blocks:
        errors.append("SRT dosyası boş.")
    return errors


def validate_assets(folder: Path, minimum_scenes: int = 6) -> dict:
    errors = []
    warnings = []
    metadata_path = folder / "metadata.json"
    if not metadata_path.is_file():
        errors.append("metadata.json eksik.")
        metadata = {}
    else:
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"metadata.json okunamadı: {exc}")
            metadata = {}

    audio_name = str(metadata.get("audio_file", "song.mp3"))
    if not (folder / audio_name).is_file():
        errors.append(f"Ses dosyası eksik: {audio_name}")

    images = list_images(folder)
    if len(images) < minimum_scenes:
        errors.append(f"En az {minimum_scenes} sahne görseli gerekli; bulunan: {len(images)}.")
    numbers = []
    for image in images:
        match = re.search(r"(\d+)", image.stem)
        if not match:
            errors.append(f"Sahne dosya adında sıra numarası bulunmalı: {image.name}")
        else:
            numbers.append(int(match.group(1)))
    if len(numbers) != len(set(numbers)):
        errors.append("Sahne görsellerinde yinelenen sıra numarası var.")
    if numbers:
        expected = list(range(1, len(numbers) + 1))
        if sorted(numbers) != expected:
            errors.append(f"Sahne numaraları 1'den başlayıp kesintisiz ilerlemeli; bulunan: {sorted(numbers)}.")

    storyboard_path = folder / "storyboard.json"
    if storyboard_path.is_file():
        try:
            storyboard = json.loads(storyboard_path.read_text(encoding="utf-8"))
            expected_count = len(storyboard.get("scenes", []))
            if expected_count and len(images) != expected_count:
                errors.append(f"Storyboard {expected_count} sahne içeriyor, görsel sayısı {len(images)}.")
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"storyboard.json okunamadı: {exc}")
    else:
        warnings.append("Şarkı klasöründe storyboard.json yok; sahne sayısı storyboard ile karşılaştırılmadı.")

    captions = folder / "captions.srt"
    if captions.exists():
        errors.extend(validate_srt(captions))
    else:
        warnings.append("captions.srt yok; video altyazısız render edilecek.")

    return {
        "passed": not errors,
        "song_folder": str(folder),
        "audio_file": audio_name,
        "scene_count": len(images),
        "scene_files": [image.name for image in images],
        "captions_present": captions.is_file(),
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Render öncesi sahne ve altyazı dosyalarını doğrula")
    parser.add_argument("--song-folder", required=True)
    parser.add_argument("--report", default="output/asset-preflight-report.json")
    args = parser.parse_args()
    report = validate_assets(Path(args.song_folder))
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
