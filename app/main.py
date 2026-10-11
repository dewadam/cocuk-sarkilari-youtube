"""Safe entry point for the Turkish children's song automation.

The first version only validates configuration. It does not call providers,
render a video, or upload anything to YouTube.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT_CONFIG = ROOT / "config" / "project.json"
TOPIC_BACKLOG = ROOT / "config" / "topic_backlog.json"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_text(value: str) -> str:
    """Normalize titles for exact duplicate checks (not semantic similarity)."""
    value = value.casefold().replace("ı", "i")
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def validate() -> list[str]:
    errors: list[str] = []
    config = load_json(PROJECT_CONFIG)
    topics = load_json(TOPIC_BACKLOG)

    if config.get("language") != "tr-TR":
        errors.append("İlk sürümün dili tr-TR olmalı.")
    if config.get("publishing_interval_days") != 4:
        errors.append("Yayın aralığı 4 gün olarak ayarlanmalı.")
    if config.get("auto_publish_enabled") is not False:
        errors.append("İlk sürümde otomatik yayın kapalı kalmalı.")
    if config.get("target_audience") != "made_for_kids":
        errors.append("Çocuklara yönelik içerik ayarı belirtilmeli.")

    duration = config.get("target_duration_seconds", {})
    if not (0 < duration.get("min", 0) <= duration.get("max", 0)):
        errors.append("Video süresi aralığı geçersiz.")

    ids = [item.get("id") for item in topics]
    if len(ids) != len(set(ids)):
        errors.append("Konu listesinde yinelenen kimlik var.")
    if not topics:
        errors.append("Konu listesi boş.")

    normalized_themes = [normalize_text(str(item.get("theme", ""))) for item in topics]
    if len(normalized_themes) != len(set(normalized_themes)):
        errors.append("Konu listesinde aynı/tekrarlanan tema başlığı var.")

    normalized_goals = [normalize_text(str(item.get("learning_goal", ""))) for item in topics]
    if len(normalized_goals) != len(set(normalized_goals)):
        errors.append("Konu listesinde aynı/tekrarlanan öğrenme hedefi var.")

    for item in topics:
        for required in ("id", "theme", "core_idea", "learning_goal", "status"):
            if not item.get(required):
                errors.append(f"Konu kaydında '{required}' alanı eksik: {item!r}")
        if item.get("id"):
            package_dirs = list((ROOT / "songs").glob(f"{item['id']}_*"))
            if not package_dirs:
                errors.append(f"{item['id']} için songs/ altında şarkı klasörü bulunamadı.")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Çocuk şarkıları projesi doğrulayıcısı")
    parser.add_argument(
        "--mode",
        choices=("validate", "dry-run"),
        default="validate",
        help="validate yapılandırmayı kontrol eder; dry-run yalnızca örnek planı gösterir.",
    )
    args = parser.parse_args()

    errors = validate()
    if errors:
        print("DOĞRULAMA BAŞARISIZ:")
        for error in errors:
            print(f"- {error}")
        return 1

    config = load_json(PROJECT_CONFIG)
    topics = load_json(TOPIC_BACKLOG)
    print("DOĞRULAMA BAŞARILI")
    print(f"Proje: {config['project_name']}")
    print(f"Dil: {config['language']}")
    print(f"Hedef yayın aralığı: {config['publishing_interval_days']} günde bir")
    print(f"Konu havuzu: {len(topics)} özgün fikir")
    print(f"Otomatik yayın: {'AÇIK' if config['auto_publish_enabled'] else 'KAPALI'}")

    if args.mode == "dry-run":
        topic = next((item for item in topics if item["status"] == "backlog"), topics[0])
        print("\nÖRNEK ÜRETİM PLANI (gerçek üretim yapılmadı):")
        print(f"Kimlik: {topic['id']}")
        print(f"Konu: {topic['theme']}")
        print(f"Öğrenme hedefi: {topic['learning_goal']}")
        print("Beste, görsel üretimi, render ve YouTube yüklemesi bu aşamada çalıştırılmaz.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
