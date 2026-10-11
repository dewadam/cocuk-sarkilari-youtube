"""Dry-run orchestrator for the kids song production pipeline.

Runs preflight, storyboard generation, prompt-pack export and asset validation.
It never uploads to YouTube and never changes song usage metadata.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"


def run_step(label: str, command: list[str], cwd: Path = ROOT) -> dict:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    output = (result.stdout or "") + (("\n" + result.stderr) if result.stderr else "")
    return {
        "step": label,
        "command": command,
        "returncode": result.returncode,
        "passed": result.returncode == 0,
        "output_tail": output[-6000:],
    }


def song_folder(root: Path, song_id: str) -> Path | None:
    matches = sorted(path for path in (root / "songs").glob(f"{song_id}_*") if path.is_dir())
    return matches[0] if len(matches) == 1 else None


def run_pipeline(root: Path, song_id: str) -> dict:
    root = root.resolve()
    steps = []
    folder = song_folder(root, song_id)
    if folder is None:
        return {
            "song_id": song_id, "mode": "dry_run", "youtube_upload_enabled": False,
            "passed": False, "steps": [],
            "blockers": [f"{song_id} için tam bir şarkı klasörü bulunamadı."],
            "next_action": "Şarkı kimliğini ve songs/TRxxx_... klasörünü kontrol edin.",
        }

    preflight_path = root / "output" / f"{song_id}_pipeline-preflight.json"
    preflight = run_step("song_library_preflight", [
        sys.executable, str(APP / "prepare_video.py"), "--output", str(preflight_path)
    ], root)
    steps.append(preflight)
    if preflight["returncode"] != 0:
        return _report(song_id, steps, [f"Şarkı kütüphanesi ön kontrolü başarısız: {preflight['output_tail'][-1000:]}"],
                       "Ön kontrol hatasını düzeltip iş akışını yeniden çalıştırın.")

    try:
        library = json.loads(preflight_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _report(song_id, steps, [f"Ön kontrol raporu okunamadı: {exc}"], "Rapor üretimini kontrol edin.")

    chosen = next((p for p in library.get("packages", []) if p.get("id") == song_id), None)
    if chosen is None:
        return _report(song_id, steps, [f"{song_id} ön kontrol raporunda yok."], "metadata id ve klasör adını eşleştirin.")
    if not chosen.get("eligible"):
        blockers = chosen.get("blockers") or ["Şarkı paketinin eligible alanı false."]
        return _report(song_id, steps, blockers, "MP3 ve sözleri kontrol edin; yalnızca son vokal doğrulanınca metadata status=ready yapın.")

    storyboard_step = run_step("build_storyboard", [
        sys.executable, str(APP / "build_storyboards.py"),
        "--song-id", song_id, "--output-dir", str(root / "output" / "storyboards")
    ], root)
    steps.append(storyboard_step)
    if not storyboard_step["passed"]:
        return _report(song_id, steps, ["Storyboard oluşturulamadı."], "Storyboard adımındaki hatayı düzeltin.")

    export_step = run_step("export_visual_prompt_pack", [
        sys.executable, str(APP / "export_visual_prompt_pack.py"),
        "--song-id", song_id,
        "--input-dir", str(root / "output" / "storyboards"),
        "--output-dir", str(root / "output" / "visual-prompt-pack")
    ], root)
    steps.append(export_step)
    if not export_step["passed"]:
        return _report(song_id, steps, ["Görsel istem paketi oluşturulamadı."], "İstem paketi çıktısını kontrol edin.")

    storyboard_path = root / "output" / "storyboards" / f"{song_id}_storyboard.json"
    folder_storyboard_path = folder / "storyboard.json"
    if storyboard_path.is_file():
        folder_storyboard_path.write_text(storyboard_path.read_text(encoding="utf-8"), encoding="utf-8")

    asset_step = run_step("validate_scene_assets_and_captions", [
        sys.executable, str(APP / "validate_assets.py"),
        "--song-folder", str(folder),
        "--report", str(root / "output" / f"{song_id}_asset-preflight-report.json")
    ], root)
    steps.append(asset_step)

    if not asset_step["passed"]:
        return _report(song_id, steps, [
            "Şarkı paketi uygun, fakat sahne görselleri/altyazı render için hazır değil.",
            asset_step["output_tail"][-3500:]
        ], "Görsel istem paketini indirip sahne görsellerini visuals/scene_01.png biçiminde ekleyin; rapordaki dosya hatalarını düzeltin.")

    return {
        "song_id": song_id,
        "mode": "dry_run",
        "youtube_upload_enabled": False,
        "song_usage_metadata_changed": False,
        "passed": True,
        "steps": steps,
        "blockers": [],
        "next_action": "Sahneler doğrulandı. Ayrı render-video iş akışıyla MP4 ön izlemesi oluşturulabilir; yayın öncesi insan kontrolü gerekir."
    }


def _report(song_id: str, steps: list[dict], blockers: list[str], next_action: str) -> dict:
    return {
        "song_id": song_id,
        "mode": "dry_run",
        "youtube_upload_enabled": False,
        "song_usage_metadata_changed": False,
        "passed": False,
        "steps": steps,
        "blockers": blockers,
        "next_action": next_action,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Şarkı video üretim hattı dry-run kontrolü")
    parser.add_argument("--song-id", required=True)
    parser.add_argument("--report", default=None)
    args = parser.parse_args()
    report = run_pipeline(ROOT, args.song_id)
    out = Path(args.report) if args.report else ROOT / "output" / f"{args.song_id}_pipeline-dry-run.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
