"""Preflight the song library and prepare a non-consuming video manifest.

This stage never reserves/consumes a song and never uploads to YouTube.
A song is eligible only after its final lyrics have been checked and metadata
status is explicitly set to "ready".
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SONGS_DIR = ROOT / "songs"
OUTPUT_DIR = ROOT / "output"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audio_duration(path: Path) -> float | None:
    """Read duration with ffprobe when available; otherwise return None."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", str(path),
            ],
            check=True, capture_output=True, text=True, timeout=20,
        )
        return round(float(result.stdout.strip()), 3)
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def inspect_library(root: Path = ROOT) -> dict:
    songs_dir = root / "songs"
    packages: list[dict] = []
    errors: list[str] = []
    seen_hashes: dict[str, str] = {}

    for metadata_path in sorted(songs_dir.glob("TR*/metadata.json")):
        folder = metadata_path.parent
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{folder.name}: metadata.json okunamadı ({exc})")
            continue

        song_id = str(metadata.get("id", folder.name.split("_", 1)[0]))
        audio_path = folder / str(metadata.get("audio_file", "song.mp3"))
        lyrics_path = folder / str(metadata.get("lyrics_file", "lyrics.txt"))
        entry = {
            "id": song_id,
            "title": metadata.get("title", folder.name),
            "folder": folder.relative_to(root).as_posix(),
            "metadata_status": metadata.get("status", "missing"),
            "usage_status": metadata.get("usage_status", "available"),
            "audio_exists": audio_path.is_file(),
            "lyrics_exists": lyrics_path.is_file(),
            "audio_sha256": None,
            "duration_seconds": None,
            "eligible": False,
            "blockers": [],
        }

        if not audio_path.is_file():
            entry["blockers"].append("song.mp3 eksik")
        else:
            digest = sha256_file(audio_path)
            entry["audio_sha256"] = digest
            entry["duration_seconds"] = audio_duration(audio_path)
            prior = seen_hashes.get(digest)
            if prior:
                entry["blockers"].append(f"aynı MP3 içeriği {prior} paketinde de var")
            else:
                seen_hashes[digest] = song_id

        if not lyrics_path.is_file():
            entry["blockers"].append("lyrics.txt eksik")
        if metadata.get("lyrics_must_match_final_audio") and metadata.get("status") != "ready":
            entry["blockers"].append("son vokal sözleri kontrol edilip status=ready yapılmalı")
        if metadata.get("status") != "ready":
            entry["blockers"].append("metadata status değeri ready değil")
        if entry["usage_status"] != "available":
            entry["blockers"].append("şarkı available değil; tekrar kullanım engeli")
        if metadata.get("used_in_video_id"):
            entry["blockers"].append("önceden bir videoya bağlanmış")

        entry["eligible"] = not entry["blockers"]
        packages.append(entry)

    eligible = next((item for item in packages if item["eligible"]), None)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "preflight_only",
        "publishing_enabled": False,
        "song_count": len(packages),
        "eligible_count": sum(1 for item in packages if item["eligible"]),
        "selected_song": eligible,
        "packages": packages,
        "errors": errors,
        "next_step": (
            "Seçilen şarkı için storyboard ve video üretimine geçilebilir."
            if eligible else
            "Video üretimine hazır şarkı yok. MP3 yükleyin, lyrics.txt dosyasını "
            "gerçek vokalle eşleştirin ve yalnızca kontrol bitince metadata status=ready yapın."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Şarkı kütüphanesi video ön kontrolü")
    parser.add_argument("--output", default=str(OUTPUT_DIR / "preflight-report.json"))
    args = parser.parse_args()

    report = inspect_library()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Şarkı paketi: {report['song_count']}")
    print(f"Video üretimine hazır: {report['eligible_count']}")
    print(f"Rapor: {output_path}")
    print(report["next_step"])
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
