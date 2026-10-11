"""Technical QC for an MP4 preview. No publishing."""
import argparse
import json
import subprocess
from pathlib import Path


def probe_video(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        check=True, capture_output=True, text=True, timeout=30,
    )
    return json.loads(result.stdout)


def validate_render(path: Path, expected_width: int = 1080, expected_height: int = 1920,
                    duration_tolerance: float = 1.5) -> dict:
    errors = []
    if not path.is_file():
        return {"passed": False, "file": str(path), "errors": ["MP4 dosyası bulunamadı."]}
    size = path.stat().st_size
    if size <= 0:
        errors.append("MP4 dosyası boş.")
    try:
        probe = probe_video(path)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        return {"passed": False, "file": str(path), "size_bytes": size,
                "errors": [f"ffprobe dosyayı okuyamadı: {exc}"]}

    streams = probe.get("streams", [])
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    if video is None:
        errors.append("Video akışı bulunamadı.")
    if audio is None:
        errors.append("Ses akışı bulunamadı.")

    width = video.get("width") if video else None
    height = video.get("height") if video else None
    if video and (width != expected_width or height != expected_height):
        errors.append(f"Çözünürlük {width}x{height}; beklenen {expected_width}x{expected_height}.")

    try:
        duration = float(probe.get("format", {}).get("duration", 0))
    except (TypeError, ValueError):
        duration = 0.0
    if duration <= 0:
        errors.append("Video süresi geçersiz.")

    audio_duration = None
    if audio:
        try:
            audio_duration = float(audio.get("duration") or 0)
        except (TypeError, ValueError):
            audio_duration = None
    delta = None
    if audio_duration and audio_duration > 0 and duration > 0:
        delta = round(duration - audio_duration, 3)
        if abs(delta) > duration_tolerance:
            errors.append(f"Video ve ses süreleri arasındaki fark {delta:.3f} sn; sınır ±{duration_tolerance:.1f} sn.")

    return {
        "passed": not errors, "file": str(path), "size_bytes": size,
        "duration_seconds": round(duration, 3),
        "audio_duration_seconds": round(audio_duration, 3) if audio_duration else None,
        "duration_delta_seconds": delta, "width": width, "height": height,
        "video_codec": video.get("codec_name") if video else None,
        "audio_codec": audio.get("codec_name") if audio else None, "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="MP4 teknik kalite kontrolü")
    parser.add_argument("--input", required=True)
    parser.add_argument("--report", default="output/render-qc-report.json")
    args = parser.parse_args()
    report = validate_render(Path(args.input))
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
