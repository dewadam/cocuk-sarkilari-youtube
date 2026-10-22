"""Sequentially render up to N prepared Pufi Kids song packages without Azure.

For each eligible song, this script generates a free procedural loop with Pillow +
FFmpeg when no loop exists, renders the loop to the song's audio duration, and
runs MP4 QC. It never publishes to YouTube and never marks a song as consumed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SONGS = ROOT / "songs"


def run(command: list[str], env: dict[str, str] | None = None) -> None:
    result = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True)
    if result.returncode:
        detail = (result.stderr or result.stdout)[-4000:]
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(command)}\n{detail}")


def candidates() -> list[tuple[str, Path, dict]]:
    found = []
    for metadata_path in sorted(SONGS.glob("TR*/metadata.json")):
        folder = metadata_path.parent
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            found.append((folder.name.split("_", 1)[0], folder, {"_metadata_error": str(exc)}))
            continue
        song_id = str(metadata.get("id") or folder.name.split("_", 1)[0]).upper()
        found.append((song_id, folder, metadata))
    return found


def process(song_id: str, folder: Path, metadata: dict, output_dir: Path) -> dict:
    started = time.monotonic()
    result = {"song_id": song_id, "title": metadata.get("title", song_id), "status": "failed"}
    if metadata.get("_metadata_error"):
        raise RuntimeError(f"metadata.json unreadable: {metadata['_metadata_error']}")
    if metadata.get("status") not in {"ready", "audio_uploaded_lyrics_check"}:
        raise RuntimeError(f"Blocked: status={metadata.get('status')!r}")
    if metadata.get("usage_status", "available") != "available" or metadata.get("used_in_video_id"):
        raise RuntimeError("Blocked: song is already used or unavailable")

    audio = folder / str(metadata.get("audio_file", "song.mp3"))
    if not audio.is_file():
        raise RuntimeError(f"Audio missing: {audio}")

    visuals = folder / "visuals"
    loop = visuals / "dance_loop.mp4"
    if not loop.is_file():
        env = os.environ.copy()
        env["SONG_ID"] = song_id
        run([sys.executable, "app/generate_procedural_dance_loop.py"], env=env)
    if not loop.is_file() or loop.stat().st_size == 0:
        raise RuntimeError("Procedural loop was not created")

    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{song_id}_preview.mp4"
    report = output_dir / f"{song_id}_qc-report.json"
    run([sys.executable, "app/render_video.py", "--song-id", song_id, "--output", str(output)])
    run([sys.executable, "app/validate_render.py", "--input", str(output), "--report", str(report)])
    result.update({
        "status": "success",
        "output": str(output.relative_to(ROOT)),
        "qc_report": str(report.relative_to(ROOT)),
        "bytes": output.stat().st_size,
        "elapsed_seconds": round(time.monotonic() - started, 1),
        "engine": "procedural_pillow_ffmpeg_no_azure",
        "youtube_uploaded": False,
    })
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch-render up to 500 Pufi Kids videos without Azure.")
    parser.add_argument("--limit", type=int, default=500, help="Maximum number of song packages to attempt (1-500).")
    parser.add_argument("--output-dir", default="output/batch", help="Directory for rendered videos and QC reports.")
    parser.add_argument("--fail-fast", action="store_true", help="Stop on first song failure instead of continuing.")
    args = parser.parse_args()
    if not 1 <= args.limit <= 500:
        parser.error("--limit must be between 1 and 500")

    output_dir = (ROOT / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    all_candidates = candidates()
    selected = []
    skipped = []
    seen_audio_hashes = {}
    allowed_statuses = {"ready", "audio_uploaded_lyrics_check"}
    for song_id, folder, metadata in all_candidates:
        reason = None
        if metadata.get("_metadata_error"):
            reason = f"metadata.json unreadable: {metadata['_metadata_error']}"
        elif metadata.get("status") not in allowed_statuses:
            reason = f"not ready: status={metadata.get('status')!r}"
        elif metadata.get("usage_status", "available") != "available" or metadata.get("used_in_video_id"):
            reason = "already used or unavailable"
        else:
            audio = folder / str(metadata.get("audio_file", "song.mp3"))
            if not audio.is_file():
                reason = f"audio missing: {audio.name}"
            else:
                digest = hashlib.sha256(audio.read_bytes()).hexdigest()
                if digest in seen_audio_hashes:
                    reason = f"duplicate audio content matches {seen_audio_hashes[digest]}"
                else:
                    seen_audio_hashes[digest] = song_id
        if reason:
            skipped.append({"song_id": song_id, "title": metadata.get("title", folder.name), "status": "skipped", "reason": reason})
        elif len(selected) < args.limit:
            selected.append((song_id, folder, metadata))

    results = []
    print(f"Packages found: {len(all_candidates)}; eligible unique-audio packages: {len(selected)}; limit: {args.limit}; Azure: disabled")
    for index, (song_id, folder, metadata) in enumerate(selected, start=1):
        print(f"\\n[{index}/{len(selected)}] {song_id}: {metadata.get('title', folder.name)}")
        try:
            item = process(song_id, folder, metadata, output_dir)
            print(f"SUCCESS: {item['output']} ({item['elapsed_seconds']} sec)")
        except Exception as exc:
            item = {
                "song_id": song_id,
                "title": metadata.get("title", folder.name),
                "status": "failed",
                "error": str(exc),
            }
            print(f"FAILED: {song_id}: {exc}")
            if args.fail_fast:
                results.append(item)
                break
        results.append(item)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "sequential_batch_render",
        "azure_enabled": False,
        "youtube_publishing": False,
        "limit": args.limit,
        "packages_found": len(all_candidates),
        "eligible_unique_audio_packages": len(selected),
        "attempted": len(results),
        "succeeded": sum(x["status"] == "success" for x in results),
        "failed": sum(x["status"] == "failed" for x in results),
        "skipped": len(skipped),
        "skip_reasons": skipped,
        "results": results,
        "note": "Only song packages already present in songs/ are processed. This workflow does not invent 500 songs or upload videos.",
    }
    report_path = output_dir / "batch-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("packages_found", "eligible_unique_audio_packages", "attempted", "succeeded", "failed", "skipped")}, ensure_ascii=False))
    return 0 if report["succeeded"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
