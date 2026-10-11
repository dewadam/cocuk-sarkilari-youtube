"""Generate deterministic, editable vertical storyboard drafts from topic metadata.

This does not generate images, render video, or publish anything. Timings are
provisional scene windows; scenes follow topic motifs and music pacing, not lyric-level sync.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOPICS_FILE = ROOT / "config" / "topic_backlog.json"
PROJECT_FILE = ROOT / "config" / "project.json"


def probe_duration(audio: Path) -> float | None:
    if not audio.is_file():
        return None
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(audio)],
            check=True, capture_output=True, text=True, timeout=20,
        )
        duration = float(result.stdout.strip())
        return duration if duration > 0 else None
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def build_storyboard(topic: dict, package_dir: Path, project: dict) -> dict:
    metadata_path = package_dir / "metadata.json"
    metadata = {}
    if metadata_path.is_file():
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            metadata = {}

    audio_path = package_dir / str(metadata.get("audio_file", "song.mp3"))
    duration = probe_duration(audio_path)
    provisional = duration is None
    if duration is None:
        duration = float(project.get("target_duration_seconds", {}).get("min", 90) + project.get("target_duration_seconds", {}).get("max", 150)) / 2

    motifs = topic.get("visual_motifs") or [topic.get("theme", "Neşeli çocuk dünyası")]
    # Visual scenes are driven by the topic and learning goal, not exact lyric lines.
    # Aim for 6–8 scenes; use a stable visual sequence tied to the topic and learning goal.
    scene_count = min(8, max(6, len(motifs)))
    scenes = []
    palettes = {
        "renk": "temiz ve canlı bir renk paleti; her ana renk görsel olarak kolay ayırt edilsin",
        "hayvan": "sıcak çiftlik tonları, doğal yeşiller ve yumuşak saman sarıları",
        "diş": "temiz pastel mavi-beyaz tonlar, parlak ama yumuşak banyo ışığı",
        "oyuncak": "düzenli renk blokları, sıcak oda ışığı ve okunaklı oyuncak siluetleri",
        "uzay": "derin lacivert uzay, mor-mavi atmosfer ve kontrollü yıldız parıltıları",
        "şekil": "yüksek kontrastlı ama dengeli temel renkler ve net geometrik siluetler",
        "bahçıvan": "doğal yeşiller, toprak kahveleri, sabah güneşi ve yumuşak altın ışık",
        "paylaş": "sıcak park yeşilleri, güneşli sarılar ve davetkâr pastel tonlar",
    }
    theme_text = (str(topic.get("theme", "")) + " " + str(topic.get("learning_goal", ""))).casefold()
    palette_rules = [
        ("renk", ("renk", "color")),
        ("hayvan", ("hayvan", "çiftlik")),
        ("diş", ("diş", "fırçalama")),
        ("oyuncak", ("oyuncak", "düzen", "sınıflandırma")),
        ("uzay", ("uzay", "gezegen", "roket")),
        ("şekil", ("şekil", "daire", "üçgen", "kare")),
        ("bahçıvan", ("bahçıvan", "bitki", "tohum", "çiçek")),
        ("paylaş", ("paylaş", "empati", "sıra bekleme")),
    ]
    palette_key = next((key for key, words in palette_rules if any(word in theme_text for word in words)), None)
    palette = palettes.get(palette_key, "hikâyeye özgü, dengeli ve birbirinden ayırt edilebilir renk paleti")
    for index in range(scene_count):
        motif = motifs[index % len(motifs)]
        start = round(duration * index / scene_count, 2)
        end = round(duration * (index + 1) / scene_count, 2)
        action = [
            "Karakter kadraja neşeyle girer ve ana nesneyi keşfeder.",
            "Ana nesneyle basit, anlaşılır bir etkileşim gösterilir.",
            "Kamera yumuşak bir hareketle yakınlaşır; karakter tepki verir."
        ][index % 3]
        scenes.append({
            "scene": index + 1,
            "start_seconds": start,
            "end_seconds": end,
            "visual_focus": motif,
            "action": action,
            "visual_direction": (
                "Dikey 9:16 kadraj; yüksek kaliteli stilize 3D animasyon filmi estetiği; "
                "okul öncesi çocuklara uygun yuvarlak formlar, " + palette + "; "
                "temiz kompozisyon, okunaklı siluetler, yumuşak sinematik ışık. "
                "Aynı ana karakterin yüzünü, kıyafetini, oranlarını ve malzemelerini bütün sahnelerde koru."
            ),
            "image_generation_prompt": (
                "Create one polished vertical 9:16 frame for a Turkish preschool 3D animated music video. "
                "Song: " + str(metadata.get("title") or topic.get("theme", "")) + ". "
                "Scene focus: " + str(motif) + ". Action: " + action + " "
                "Learning goal: " + str(topic.get("learning_goal", "")) + ". "
                "Visual direction: " + palette + "; rounded appealing shapes, expressive friendly characters, "
                "cinematic soft lighting, clear focal point, uncluttered background, premium 3D animation render. "
                "Keep the same character design across all scenes. No text, no logos, no watermark, no copied copyrighted characters."
            ),
            "sync_note": "Geçici zaman aralığı; sahne geçişleri müziğin genel temposuna göre gözden geçirilecek, söz senkronu kullanılmayacak."
        })

    return {
        "id": topic.get("id"),
        "title": metadata.get("title") or topic.get("theme"),
        "language": project.get("language", "tr-TR"),
        "aspect_ratio": "9:16",
        "target_audience": "preschool",
        "visual_style": project.get("visual_style", "stylized_high_quality_3d"),
        "learning_goal": topic.get("learning_goal"),
        "duration_seconds": round(duration, 2),
        "duration_is_provisional": provisional,
        "audio_file_present": audio_path.is_file(),
        "scenes": scenes,
        "production_notes": [
            "Bu dosya taslak storyboard'dur; gerçek sahne render'ı değildir.",
            "Ekranda şarkı sözü/altyazı kullanılmaz; sahneler konu ve öğrenme hedefini görselleştirir.",
            "Sahneler arasında karakter, ışık ve malzeme tutarlılığını koru.",
            "Başka bir şarkıdan, çizgi filmden veya korunan karakterden görsel kopyalama."
        ]
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Şarkılar için storyboard taslakları üret")
    parser.add_argument("--output-dir", default=str(ROOT / "output" / "storyboards"))
    parser.add_argument("--song-id", help="Yalnızca bir şarkının storyboard'unu üret")
    args = parser.parse_args()

    project = json.loads(PROJECT_FILE.read_text(encoding="utf-8"))
    topics = json.loads(TOPICS_FILE.read_text(encoding="utf-8"))
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = 0

    for topic in topics:
        song_id = str(topic.get("id", ""))
        if args.song_id and song_id != args.song_id:
            continue
        matches = sorted((ROOT / "songs").glob(f"{song_id}_*"))
        if not matches:
            print(f"Atlandı: {song_id} için şarkı klasörü yok.")
            continue
        storyboard = build_storyboard(topic, matches[0], project)
        output = out_dir / f"{song_id}_storyboard.json"
        output.write_text(json.dumps(storyboard, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Oluşturuldu: {output} ({len(storyboard['scenes'])} sahne)")
        written += 1

    if args.song_id and written == 0:
        print(f"HATA: {args.song_id} bulunamadı.")
        return 1
    print(f"Toplam storyboard: {written}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
