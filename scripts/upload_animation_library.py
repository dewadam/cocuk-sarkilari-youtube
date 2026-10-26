#!/usr/bin/env python3
"""Upload a prepared Pufi Kids animation batch to GitHub Releases and refresh catalog.json.

Windows usage:
  py scripts/upload_animation_library.py --batch-dir "C:\\path\\to\\upload_batch_generated"

Requirements:
  - GitHub CLI (gh) installed and authenticated: gh auth login
  - Git installed
  - Repository write access, including Releases and Contents
  - Each MP4 has a same-name JSON sidecar

This command does not upload anything to YouTube.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

REPO_DEFAULT = "dewadam/cocuk-sarkilari-youtube"
CATALOG_RELATIVE = Path("animation_library") / "catalog.json"


def run(args: list[str], *, cwd: Path | None = None, capture: bool = False) -> str:
    result = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        check=False,
    )
    if result.returncode:
        details = ""
        if capture:
            details = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(args[:5])}\n{details}")
    return (result.stdout or "").strip() if capture else ""


def load_batch(batch_dir: Path, repo: str, tag: str) -> list[dict]:
    if not batch_dir.is_dir():
        raise ValueError(f"Batch folder not found: {batch_dir}")
    videos = sorted(batch_dir.glob("*.mp4"), key=lambda p: p.name.casefold())
    if not videos:
        raise ValueError(f"No MP4 files found in: {batch_dir}")

    base_url = f"https://github.com/{repo}/releases/download/{tag}"
    records: list[dict] = []
    seen: set[str] = set()
    for video in videos:
        if video.stat().st_size <= 0:
            raise ValueError(f"Empty MP4: {video.name}")
        sidecar = video.with_suffix(".json")
        if not sidecar.is_file():
            raise ValueError(f"Missing JSON sidecar: {sidecar.name}")
        try:
            meta = json.loads(sidecar.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {sidecar.name}: {exc}") from exc
        if not isinstance(meta, dict):
            raise ValueError(f"JSON sidecar must contain an object: {sidecar.name}")

        clip_id = str(meta.get("clip_id") or video.stem).strip().upper()
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9_-]{2,63}", clip_id):
            raise ValueError(f"Invalid clip_id in {sidecar.name}: {clip_id!r}")
        if clip_id in seen:
            raise ValueError(f"Duplicate clip_id in batch: {clip_id}")
        seen.add(clip_id)

        # The user explicitly requested a ready-to-run library. The catalog entries
        # are activated for matching once uploaded; no YouTube upload is performed here.
        meta["clip_id"] = clip_id
        meta["file_name"] = video.name
        meta["asset_url"] = f"{base_url}/{quote(video.name)}"
        meta["approved"] = True
        meta.setdefault("category", "")
        meta.setdefault("tags", [])
        meta.setdefault("keywords", [])
        meta.setdefault("duration_seconds", 30)
        meta.setdefault("loopable", True)
        meta.setdefault("source_model", "user-generated-from-provided-prompt")
        errors = []
        for field in ("clip_id", "file_name", "category", "tags", "keywords", "duration_seconds", "loopable", "asset_url"):
            if field not in meta:
                errors.append(f"missing {field}")
        if not isinstance(meta.get("tags"), list) or not isinstance(meta.get("keywords"), list):
            errors.append("tags and keywords must be arrays")
        try:
            if float(meta.get("duration_seconds", 0)) <= 0:
                errors.append("duration_seconds must be positive")
        except (TypeError, ValueError):
            errors.append("duration_seconds must be numeric")
        if errors:
            raise ValueError(f"{sidecar.name}: " + "; ".join(errors))
        records.append(meta)

    print(f"Batch: {len(videos)} MP4 files with matching JSON sidecars.")
    print("Catalog entries will be marked approved=true so the animation renderer can use them.")
    return records


def release_exists(repo: str, tag: str) -> bool:
    result = subprocess.run(
        ["gh", "release", "view", tag, "--repo", repo],
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def upload_release_assets(repo: str, tag: str, batch_dir: Path, videos: list[Path]) -> None:
    if not release_exists(repo, tag):
        run([
            "gh", "release", "create", tag,
            "--repo", repo,
            "--title", f"Pufi Kids animation library {tag}",
            "--notes", f"Reusable animation clip batch. Clip count: {len(videos)}. Metadata is indexed in animation_library/catalog.json.",
        ])
    # Resume safely: skip assets already uploaded with the same byte size.
    listing = run([
        "gh", "release", "view", tag, "--repo", repo,
        "--json", "assets", "--jq", '.assets[] | [.name, (.size|tostring)] | @tsv',
    ], capture=True)
    existing_sizes = {}
    for line in listing.splitlines():
        parts = line.split("\\t")
        if len(parts) == 2:
            try:
                existing_sizes[parts[0]] = int(parts[1])
            except ValueError:
                continue
    pending = []
    for video in videos:
        current_size = video.stat().st_size
        if existing_sizes.get(video.name) == current_size:
            print(f"Already uploaded; skipping: {video.name}")
        else:
            pending.append(video)
    # Chunk uploads to keep Windows command-line lengths comfortably below limits.
    chunk_size = 20
    for offset in range(0, len(pending), chunk_size):
        chunk = pending[offset:offset + chunk_size]
        print(f"Uploading clips {offset + 1}-{offset + len(chunk)} of {len(pending)} pending files...")
        run(["gh", "release", "upload", tag, *[str(p) for p in chunk], "--repo", repo, "--clobber"])


def update_remote_catalog(repo: str, records: list[dict]) -> None:
    with tempfile.TemporaryDirectory(prefix="pufi-kids-catalog-") as tmp:
        clone = Path(tmp) / "repo"
        run(["gh", "repo", "clone", repo, str(clone)])
        catalog_path = clone / CATALOG_RELATIVE
        if catalog_path.is_file():
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        else:
            catalog = {
                "schema_version": 1,
                "description": "Persistent metadata catalog for reusable 3D children's-song animation clips. Video binaries are stored as GitHub Release assets, not in Git history.",
                "updated_at": None,
                "clips": [],
            }
        if catalog.get("schema_version") != 1 or not isinstance(catalog.get("clips"), list):
            raise ValueError("Remote animation_library/catalog.json has an unsupported schema.")

        by_id = {str(item.get("clip_id")): item for item in catalog["clips"] if isinstance(item, dict) and item.get("clip_id")}
        for record in records:
            by_id[record["clip_id"]] = record
        catalog["clips"] = sorted(by_id.values(), key=lambda item: str(item.get("clip_id", "")))
        catalog["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        catalog_path.parent.mkdir(parents=True, exist_ok=True)
        catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        run(["git", "config", "user.name", "Pufi Kids Animation Uploader"], cwd=clone)
        run(["git", "config", "user.email", "pufi-kids-animation-uploader@users.noreply.github.com"], cwd=clone)
        run(["git", "add", str(CATALOG_RELATIVE)], cwd=clone)
        changed = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=str(clone), check=False)
        if changed.returncode == 0:
            print(f"Catalog already up to date ({len(catalog['clips'])} clips).")
            return
        run(["git", "commit", "-m", f"Update animation catalog with {len(records)} uploaded clips"], cwd=clone)
        run(["git", "push"], cwd=clone)
        print(f"Updated remote catalog: {len(catalog['clips'])} total clips.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload Pufi Kids MP4 + JSON batches to GitHub Releases and update catalog.json.")
    parser.add_argument("--batch-dir", required=True, type=Path, help="Folder containing CLIP###.mp4 and matching CLIP###.json files.")
    parser.add_argument("--repo", default=REPO_DEFAULT, help="GitHub repository in owner/name form.")
    parser.add_argument("--tag", default=None, help="Release tag. If omitted, a unique tag is generated.")
    args = parser.parse_args()

    if not shutil.which("gh"):
        raise RuntimeError("GitHub CLI 'gh' is required. Install it, then run: gh auth login")
    if not shutil.which("git"):
        raise RuntimeError("Git is required. Install Git for Windows and reopen Command Prompt.")
    run(["gh", "auth", "status"])

    tag = args.tag or "animation-library-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    if not re.fullmatch(r"[A-Za-z0-9._-]{3,100}", tag):
        raise ValueError("Invalid release tag; use letters, digits, dot, underscore or hyphen.")

    batch_dir = args.batch_dir.expanduser().resolve()
    print(f"Release tag: {tag}")
    print("If the upload is interrupted, rerun with this same tag using --tag " + tag)
    records = load_batch(batch_dir, args.repo, tag)
    videos = sorted(batch_dir.glob("*.mp4"), key=lambda p: p.name.casefold())
    upload_release_assets(args.repo, tag, batch_dir, videos)
    update_remote_catalog(args.repo, records)

    print("\nSUCCESS")
    print(f"Repository: https://github.com/{args.repo}")
    print(f"Release: https://github.com/{args.repo}/releases/tag/{tag}")
    print(f"Uploaded clips: {len(records)}")
    print("catalog.json updated. This process does not publish to YouTube.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
