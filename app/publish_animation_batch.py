#!/usr/bin/env python3
"""Publish an approved batch of MP4 clips to a GitHub Release and update the catalog.

Each MP4 must have a same-name JSON sidecar (clip-name.json) containing tags,
keywords, duration_seconds, loopable, category, etc. The publisher fills in
clip_id, file_name and asset_url when absent.
"""
from __future__ import annotations
import argparse, json, re, subprocess, sys
from pathlib import Path
from animation_catalog import DEFAULT_CATALOG, load_catalog, save_catalog, validate_clip

def run(command: list[str], dry_run: bool = False) -> str:
    print("+ " + " ".join(command))
    if dry_run:
        return ""
    result = subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stdout.strip()

def main() -> int:
    p = argparse.ArgumentParser(description="Publish an approved animation batch as GitHub Release assets")
    p.add_argument("--batch-dir", type=Path, required=True)
    p.add_argument("--repo", required=True, help="owner/repository")
    p.add_argument("--tag", required=True, help="unique release tag, e.g. animation-batch-2026-10-13-01")
    p.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9._-]{3,100}", a.tag):
        raise ValueError("Release tag may contain only letters, numbers, dot, underscore and hyphen")
    if not a.batch_dir.is_dir():
        raise ValueError(f"Batch directory does not exist: {a.batch_dir}")
    videos = sorted(a.batch_dir.glob("*.mp4"))
    if not videos:
        raise ValueError(f"No MP4 files found in {a.batch_dir}")
    catalog = load_catalog(a.catalog)
    known = {clip["clip_id"] for clip in catalog["clips"] if "clip_id" in clip}
    records = []
    release_base = f"https://github.com/{a.repo}/releases/download/{a.tag}"
    for video in videos:
        sidecar = video.with_suffix(".json")
        if not sidecar.exists():
            raise ValueError(f"Missing sidecar metadata for {video.name}: expected {sidecar.name}")
        meta = json.loads(sidecar.read_text(encoding="utf-8"))
        if not isinstance(meta, dict):
            raise ValueError(f"Sidecar must be a JSON object: {sidecar}")
        clip_id = meta.get("clip_id") or "ANIM_" + re.sub(r"[^A-Z0-9]+", "_", video.stem.upper()).strip("_")
        if clip_id in known:
            raise ValueError(f"Duplicate clip_id {clip_id}; use a new stable ID")
        known.add(clip_id)
        meta["clip_id"] = clip_id
        meta["file_name"] = video.name
        meta["asset_url"] = f"{release_base}/{video.name}"
        meta.setdefault("approved", True)
        meta.setdefault("source_model", "unknown")
        meta.setdefault("prompt_id", "")
        errors = validate_clip(meta)
        if errors:
            raise ValueError(f"{sidecar.name}: " + "; ".join(errors))
        records.append(meta)
    # Verify files are non-empty before uploading. Detailed MP4 probing belongs in batch QC.
    for video in videos:
        if video.stat().st_size == 0:
            raise ValueError(f"Empty MP4: {video.name}")
    run(["gh", "release", "create", a.tag, "--repo", a.repo, "--title", f"Animation batch {a.tag}", "--notes", f"Approved reusable 3D animation clips. Clip count: {len(videos)}"], a.dry_run)
    run(["gh", "release", "upload", a.tag, *[str(v) for v in videos], "--repo", a.repo], a.dry_run)
    by_id = {clip.get("clip_id"): clip for clip in catalog["clips"]}
    for record in records:
        by_id[record["clip_id"]] = record
    catalog["clips"] = sorted(by_id.values(), key=lambda item: item.get("clip_id", ""))
    if not a.dry_run:
        save_catalog(catalog, a.catalog)
    print(f"Validated {len(records)} clips; catalog will contain {len(catalog['clips'])} records.")
    if a.dry_run:
        print("DRY RUN: no Release or catalog files were changed.")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
