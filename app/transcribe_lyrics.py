"""Create an unverified SRT draft from song audio using faster-whisper.

Speech recognition on singing is error-prone. The generated subtitles must be
listened to and corrected before they are copied into a song package.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


def srt_timestamp(seconds: float) -> str:
    milliseconds = max(0, round(float(seconds) * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, millis = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{whole_seconds:02},{millis:03}"


def segments_to_srt(segments: Iterable[object]) -> str:
    blocks: list[str] = []
    previous_end = 0.0
    for segment in segments:
        text = str(getattr(segment, "text", "")).strip()
        if not text:
            continue
        start = max(0.0, float(getattr(segment, "start", 0.0)))
        end = max(start + 0.08, float(getattr(segment, "end", start + 0.08)))
        # Keep SRT cues sequential and non-overlapping for the project's validator.
        start = max(start, previous_end)
        if end <= start:
            end = start + 0.08
        blocks.append(
            f"{len(blocks) + 1}\n{srt_timestamp(start)} --> {srt_timestamp(end)}\n{text}"
        )
        previous_end = end
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def generate_draft(
    audio_path: Path,
    output_srt: Path,
    report_path: Path,
    model_name: str = "small",
) -> dict:
    if not audio_path.is_file():
        raise FileNotFoundError(f"Ses dosyası bulunamadı: {audio_path}")

    from faster_whisper import WhisperModel

    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, info = model.transcribe(
        str(audio_path),
        language="tr",
        task="transcribe",
        beam_size=5,
        vad_filter=False,
    )
    segment_list = list(segments)
    srt = segments_to_srt(segment_list)
    if not srt.strip():
        raise RuntimeError("Model altyazı üretemedi; ses dosyasını kontrol edin.")

    output_srt.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    output_srt.write_text(srt, encoding="utf-8")
    report = {
        "status": "draft_requires_human_review",
        "verified": False,
        "language_detected": getattr(info, "language", None),
        "language_probability": getattr(info, "language_probability", None),
        "model": model_name,
        "audio_file": audio_path.name,
        "output_srt": str(output_srt),
        "caption_count": len([block for block in srt.strip().split("\n\n") if block.strip()]),
        "warnings": [
            "Şarkı söyleme, müzik ve efektler konuşma tanımayı yanıltabilir.",
            "Her satırı MP3 dinleyerek düzeltin; sözleri doğrulamadan captions.srt olarak kullanmayın.",
            "Zamanlamaları ve Türkçe karakterleri kontrol edin.",
        ],
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="MP3 dosyasından insan kontrolü gereken SRT taslağı üret")
    parser.add_argument("--audio", required=True, help="Girdi MP3 dosyası")
    parser.add_argument("--output-srt", required=True, help="Oluşturulacak taslak SRT")
    parser.add_argument("--report", required=True, help="JSON kalite/inceleme raporu")
    parser.add_argument("--model", default="small", choices=("tiny", "base", "small", "medium"))
    args = parser.parse_args()
    report = generate_draft(Path(args.audio), Path(args.output_srt), Path(args.report), args.model)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
