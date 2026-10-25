#!/usr/bin/env python3
"""Match generated Pufi Kids MP4 files to video_catalog_500.csv.

Expected source layout:
  animation_library/source/video_catalog_500.csv
  animation_library/inbox/<THEME_CODE>/CLIP###.mp4

Creates a flat upload batch with JSON sidecars for app/publish_animation_batch.py.
No clip is approved automatically.
"""
from __future__ import annotations
import argparse, csv, json, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def truthy(value):
    return str(value).strip().casefold() in {"yes", "true", "1", "evet"}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--csv", type=Path, default=ROOT/"animation_library/source/video_catalog_500.csv")
    p.add_argument("--inbox", type=Path, default=ROOT/"animation_library/inbox")
    p.add_argument("--out", type=Path, default=ROOT/"animation_library/upload_batch")
    a = p.parse_args()
    if not a.csv.is_file():
        raise SystemExit(f"CSV bulunamadı: {a.csv}")
    with a.csv.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "video_id" not in reader.fieldnames:
            raise SystemExit("CSV içinde video_id sütunu bulunmalı.")
        rows = list(reader)
    by_id = {}
    for row in rows:
        cid = str(row.get("video_id", "")).strip().upper()
        if not cid:
            raise SystemExit("CSV'de boş video_id bulundu.")
        if cid in by_id:
            raise SystemExit(f"CSV'de yinelenen video_id: {cid}")
        by_id[cid] = row
    if not a.inbox.is_dir():
        raise SystemExit(f"MP4 gelen kutusu bulunamadı: {a.inbox}")
    found = {}
    all_mp4 = sorted(a.inbox.rglob("*.mp4"))
    for video in all_mp4:
        cid = video.stem.upper()
        if cid not in by_id:
            print(f"CSV'de karşılığı yok, atlandı: {video.relative_to(a.inbox)}")
            continue
        if cid in found:
            raise SystemExit(f"Aynı klip kimliği birden fazla dosyada: {cid}")
        found[cid] = video
    a.out.mkdir(parents=True, exist_ok=True)
    missing = sorted(set(by_id) - set(found))
    for cid, video in sorted(found.items()):
        row = by_id[cid]
        tags = [x.strip() for x in str(row.get("tags", "")).split(";") if x.strip()]
        keywords = list(dict.fromkeys(x.strip() for x in [
            row.get("title_tr", ""), row.get("theme_tr", ""), row.get("character", ""),
            row.get("setting", ""), row.get("learning_goal_tr", "")
        ] if str(x).strip()))
        prompts = [str(row.get(f"prompt_seg{i}", "")).strip() for i in range(1, 6)]
        try:
            duration = float(row.get("duration_target_sec") or 30)
            scene_no = int(float(row.get("scene_no") or 0))
        except ValueError:
            raise SystemExit(f"{cid}: duration_target_sec/scene_no sayı değil.")
        metadata = {
            "clip_id": cid, "file_name": video.name,
            "category": str(row.get("theme_tr", "")).strip(),
            "tags": tags, "keywords": keywords, "duration_seconds": duration,
            "loopable": truthy(row.get("loopable", "yes")),
            "asset_url": "", "approved": False,
            "source_model": "user-generated-from-provided-prompt", "prompt_id": cid,
            "characters": [str(row.get("character", "")).strip()] if row.get("character") else [],
            "actions": [], "environments": [str(row.get("setting", "")).strip()] if row.get("setting") else [],
            "moods": ["çocuk dostu"], "theme_code": str(row.get("theme_code", "")).strip(),
            "scene_no": scene_no, "learning_goal_tr": str(row.get("learning_goal_tr", "")).strip(),
            "aspect_ratio": str(row.get("aspect_ratio", "9:16")).strip(),
            "prompt_segments": prompts, "negative_prompt": str(row.get("negative_prompt", "")).strip()
        }
        dest = a.out/video.name
        if video.resolve() != dest.resolve():
            shutil.copy2(video, dest)
        (a.out/(cid+".json")).write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    report = {
        "csv_records": len(by_id), "found_video_files": len(found),
        "missing_video_count": len(missing), "missing_video_ids": missing,
        "mp4_files_scanned": len(all_mp4), "prepared_batch": str(a.out),
        "approval_default": False
    }
    (a.out/"import-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k: (v[:30]+["..."] if k=="missing_video_ids" and len(v)>30 else v) for k,v in report.items()}, ensure_ascii=False, indent=2))
    print("Sonraki adım: MP4'leri görsel olarak kontrol edin; yalnızca onaylanan sidecar dosyalarında approved=true yapın.")

if __name__ == "__main__":
    try:
        main()
    except (OSError, csv.Error, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
