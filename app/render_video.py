"""Render a vertical MP4 from approved song audio and scene stills using FFmpeg.

Expected images: songs/<ID>_*/visuals/scene_01.png, scene_02.png, ...
Optional captions: songs/<ID>_*/captions.srt.
No image generation or YouTube upload happens here.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def find_song_folder(root: Path, song_id: str) -> Path:
    matches = sorted((root / "songs").glob(f"{song_id}_*"))
    matches = [path for path in matches if path.is_dir()]
    if len(matches) != 1:
        raise ValueError(f"{song_id} için tam bir şarkı klasörü bekleniyordu; bulunan: {len(matches)}")
    return matches[0]


def list_scene_images(folder: Path) -> list[Path]:
    visuals = folder / "visuals"
    if not visuals.is_dir():
        return []
    images = [p for p in visuals.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
    def order(path: Path):
        match = re.search(r"(\d+)", path.stem)
        return (int(match.group(1)) if match else 10**9, path.name.casefold())
    return sorted(images, key=order)


def run_checked(command: list[str]) -> None:
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode != 0:
        tail = (result.stderr or result.stdout)[-5000:]
        raise RuntimeError(f"Komut başarısız (kod {result.returncode}): {' '.join(command[:5])}\n{tail}")


def get_duration(audio: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(audio)],
        check=True, capture_output=True, text=True, timeout=30,
    )
    duration = float(result.stdout.strip())
    if duration <= 0:
        raise ValueError("Ses dosyası süresi geçersiz.")
    return duration


def render_video(root: Path, song_id: str, output_path: Path) -> dict:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("FFmpeg ve ffprobe kurulu olmalı.")

    folder = find_song_folder(root, song_id)
    metadata_path = folder / "metadata.json"
    if not metadata_path.is_file():
        raise ValueError("metadata.json eksik.")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("status") != "ready":
        raise ValueError("Şarkı hazır değil: MP3'ü dinleyip lyrics.txt dosyasını doğrulayın ve metadata status=ready yapın.")
    if metadata.get("usage_status", "available") != "available" or metadata.get("used_in_video_id"):
        raise ValueError("Bu şarkı kullanılabilir durumda değil veya daha önce bir videoya bağlanmış.")

    audio = folder / str(metadata.get("audio_file", "song.mp3"))
    if not audio.is_file():
        raise ValueError(f"Ses dosyası eksik: {audio.name}")
    images = list_scene_images(folder)
    if not images:
        raise ValueError(f"Görsel bulunamadı. PNG/JPG/WEBP sahnelerini {folder.name}/visuals/scene_01.png konumuna ekleyin.")
    duration = get_duration(audio)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    captions = folder / "captions.srt"
    fps = 30
    segment_duration = duration / len(images)

    with tempfile.TemporaryDirectory(prefix="kids-song-render-") as tmp:
        temp = Path(tmp)
        clip_paths = []
        for index, image in enumerate(images):
            clip = temp / f"clip_{index:03d}.mp4"
            # The still fills the vertical frame, then a gentle zoom adds motion.
            frames = max(1, round(segment_duration * fps))
            zoom_filter = (
                "scale=1080:1920:force_original_aspect_ratio=increase,"
                "crop=1080:1920,"
                f"zoompan=z='min(zoom+0.0005,1.06)':d={frames}:"
                "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                "s=1080x1920:fps=30,format=yuv420p"
            )
            run_checked([
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-loop", "1", "-framerate", str(fps), "-i", str(image),
                "-vf", zoom_filter, "-t", f"{segment_duration:.6f}",
                "-an", "-r", str(fps), "-c:v", "libx264",
                "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                str(clip),
            ])
            clip_paths.append(clip)

        concat_list = temp / "clips.txt"
        concat_list.write_text(
            "".join("file '" + path.as_posix().replace("'", "'\\''") + "'\n" for path in clip_paths),
            encoding="utf-8",
        )
        joined = temp / "joined.mp4"
        run_checked([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", str(concat_list),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-r", str(fps), str(joined),
        ])

        command = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(joined), "-i", str(audio)]
        if captions.is_file():
            # Use a relative path escaped for FFmpeg's subtitles filter.
            subtitle_path = str(captions.resolve()).replace("\\", "/").replace(":", "\\:")
            command += ["-vf", f"subtitles='{subtitle_path}'"]
        command += [
            "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264",
            "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
            str(output_path),
        ]
        run_checked(command)

    return {
        "song_id": song_id,
        "title": metadata.get("title", song_id),
        "output": str(output_path),
        "audio_duration_seconds": round(duration, 3),
        "scene_image_count": len(images),
        "captions_embedded": captions.is_file(),
        "resolution": "1080x1920",
        "fps": fps,
        "youtube_uploaded": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="MP3 + sahne görsellerinden dikey video oluştur")
    parser.add_argument("--song-id", required=True, help="Ör. TR001")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    output = Path(args.output) if args.output else ROOT / "output" / f"{args.song_id}_preview.mp4"
    report = render_video(ROOT, args.song_id, output)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(f"VIDEO ÜRETİMİ DURDURULDU: {exc}")
        raise SystemExit(1)
