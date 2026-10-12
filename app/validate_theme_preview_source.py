"""Fast static checks for the procedural theme preview before expensive Blender renders.

This does not replace a real render or visual review; it catches missing theme
branches and unsafe output assumptions without requiring Blender to be installed.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "app" / "blender_theme_preview.py"
EXPECTED = {f"TR{i:03d}" for i in range(1, 9)}


def validate(source: str) -> list[str]:
    errors: list[str] = []
    theme_block = source.split("    themed = {", 1)
    if len(theme_block) != 2:
        return ["Theme mapping dictionary is missing."]
    theme_block = theme_block[1].split("    }", 1)[0]
    found = set(re.findall(r'"(TR\d{3})"\s*:', theme_block))
    if found != EXPECTED:
        errors.append(f"Theme mapping mismatch: missing={sorted(EXPECTED-found)}, extra={sorted(found-EXPECTED)}")
    for song_id in sorted(EXPECTED):
        if not re.search(rf'song_id\s*==\s*"{song_id}"', source):
            if song_id != "TR001":  # TR001 is the default branch.
                errors.append(f"{song_id}: dedicated character branch is missing.")
    required = [
        "scene.render.resolution_x=320",
        "scene.render.resolution_y=568",
        "scene.render.fps=24",
        "scene.render.ffmpeg.codec=\"H264\"",
        "scene.frame_end=seconds*24",
        "youtube_uploaded\":False",
    ]
    for snippet in required:
        if snippet not in source:
            errors.append(f"Required render/safety setting missing: {snippet}")
    if "last_frame = scene.frame_end" not in source:
        errors.append("Animation keyframes are not derived from the requested duration.")
    if "keyframe_insert(data_path=\"location\"" not in source:
        errors.append("Hero movement keyframes are missing.")
    if "Gentle camera drift" not in source or "Gentle camera push-in" not in source:
        errors.append("Gentle camera movement keyframes are missing.")
    if "camera.data.keyframe_insert(data_path=\"ortho_scale\"" not in source:
        errors.append("Camera push-in animation is missing.")
    lamb_checks = [
        'Lamb fleece body',
        'Lamb face',
        'Long floppy lamb ear',
        'Pink inner ear',
        'Lamb short leg',
        'Lamb dark hoof',
        'Individual fluffy wool curl',
        'Tiny nostril',
    ]
    for snippet in lamb_checks:
        if snippet not in source:
            errors.append(f"TR002 recognizable lamb feature missing: {snippet}")
    tr002 = source.split('if song_id == "TR002":', 1)
    if len(tr002) != 2 or 'elif song_id == "TR003":' not in tr002[1]:
        errors.append("TR002 lamb character branch is malformed.")
    else:
        tr002_block = tr002[1].split('elif song_id == "TR003":', 1)[0]
        for count_check, label in [
            (r'for side_x in \(-\\.38,\\.38\\):', "leg row loop"),
            (r'for depth_y in \(-\\.24,\\.24\\):', "front/back leg loop"),
        ]:
            if not re.search(count_check, tr002_block):
                errors.append(f"TR002 four-leg construction missing: {label}.")
    return errors


def main() -> int:
    source = SCRIPT.read_text(encoding="utf-8")
    errors = validate(source)
    if errors:
        print("Theme preview source validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Theme preview source validation passed: 8 themes, distinct branches, vertical output, no upload.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
