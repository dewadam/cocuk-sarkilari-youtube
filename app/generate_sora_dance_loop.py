#!/usr/bin/env python3
"""Generate one song-specific, loop-oriented Sora 2 dance clip via Azure OpenAI."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def request_json(url: str, headers: dict[str, str], body: dict | None = None) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(
        url, data=data, method="POST" if body is not None else "GET",
        headers={**headers, **({"Content-Type": "application/json"} if body is not None else {})},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[-3000:]
        raise RuntimeError(f"Sora API HTTP {exc.code}: {detail}") from exc


def find_song_folder(song_id: str) -> Path:
    matches = sorted(p for p in (ROOT / "songs").glob(f"{song_id}_*") if p.is_dir())
    if len(matches) != 1:
        raise RuntimeError(f"{song_id}: exactly one song folder expected, found {len(matches)}")
    return matches[0]


def make_prompt(metadata: dict, lyrics: str) -> str:
    motifs = ", ".join(str(x) for x in metadata.get("visual_motifs", []))
    theme = metadata.get("theme", "preschool song")
    idea = metadata.get("core_idea", "")
    # Keep only a short lyric excerpt to ground the visuals without asking the model to render text.
    lyric_lines = [line.strip() for line in lyrics.splitlines()
                   if line.strip() and not line.strip().startswith("#")
                   and not line.strip().startswith("[")]
    lyric_hint = " ".join(lyric_lines[:8])[:500]
    return (
        "Create an original, polished 3D animated preschool music-video dance clip. "
        f"Song theme: {theme}. Story idea: {idea}. Visual motifs: {motifs}. "
        f"Lyric meaning for visual inspiration only: {lyric_hint}. "
        "Show a small, consistent cast of adorable farm animal friends: a friendly cow and calf, "
        "a fluffy lamb, a yellow duck, and a cheerful rooster, in a colorful sunny farmyard with a pond. "
        "All characters remain the same species, colors, proportions, and outfits throughout. "
        "They perform a continuous lively group dance with clear full-body movements, gentle hops, "
        "side-to-side steps, wing/hoof movements appropriate to each animal, and rhythmic head bobs. "
        "Single continuous take, fixed camera, no cuts, no scene changes, no zooms, no morphing, "
        "no extra limbs, no duplicated characters. Vertical 9:16 composition, characters fully visible, "
        "bright soft cinematic lighting, premium family-friendly 3D animation, smooth natural motion. "
        "DESIGNED FOR A SEAMLESS LOOP: begin and end in the exact same group formation and dance phase; "
        "the final movement must flow naturally into the opening movement, matching pose, position, "
        "direction, and motion speed. Keep a repeating cyclic dance pattern throughout. "
        "No text, no letters, no captions, no logos, no watermark. Do not add audio; the song will be mixed separately."
    )


def main() -> int:
    song_id = os.environ.get("SONG_ID", "TR002").strip()
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip().rstrip("/")
    api_key = os.environ.get("AZURE_OPENAI_API_KEY", "").strip()
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "sora-2").strip()
    if not endpoint or not api_key or not deployment:
        raise RuntimeError(
            "Missing Sora settings. Configure GitHub secrets AZURE_OPENAI_ENDPOINT and "
            "AZURE_OPENAI_API_KEY, and repository variable AZURE_OPENAI_DEPLOYMENT_NAME "
            "(the deployed Sora 2 model name)."
        )

    folder = find_song_folder(song_id)
    metadata = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
    audio = folder / str(metadata.get("audio_file", "song.mp3"))
    lyrics_path = folder / str(metadata.get("lyrics_file", "lyrics.txt"))
    if not audio.is_file():
        raise RuntimeError(f"Audio file missing: {audio}")
    lyrics = lyrics_path.read_text(encoding="utf-8") if lyrics_path.is_file() else ""
    prompt = make_prompt(metadata, lyrics)
    out_dir = folder / "visuals"
    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / "dance_loop.mp4"
    manifest_path = out_dir / "dance_loop_manifest.json"
    manifest = {
        "song_id": song_id, "model_deployment": deployment,
        "duration_seconds_requested": 15, "width": 720, "height": 1280,
        "loop_requested": True, "prompt": prompt, "status": "submitting",
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    headers = {"api-key": api_key}
    base = endpoint + "/openai/v1"
    job = request_json(
        base + "/video/generations/jobs?api-version=preview",
        headers,
        {"prompt": prompt, "width": 720, "height": 1280,
         "n_seconds": 15, "n_variants": 1, "model": deployment},
    )
    job_id = job.get("id")
    if not job_id:
        raise RuntimeError("Sora API response did not include a job id: " + json.dumps(job)[:2000])
    manifest.update({"job_id": job_id, "status": job.get("status", "queued")})
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    status = job.get("status")
    deadline = time.time() + 900
    status_response = job
    while status not in ("succeeded", "failed", "cancelled"):
        if time.time() >= deadline:
            manifest.update({"status": "timeout", "last_status": status})
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            raise RuntimeError("Sora job exceeded 15 minutes; no automatic duplicate generation was submitted.")
        time.sleep(8)
        status_response = request_json(
            f"{base}/video/generations/jobs/{job_id}?api-version=preview", headers
        )
        status = status_response.get("status")
        print(f"Sora job status: {status}", flush=True)

    if status != "succeeded":
        manifest.update({"status": status, "failure_reason": status_response.get("failure_reason")})
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise RuntimeError("Sora generation failed: " + str(status_response.get("failure_reason", status)))

    generations = status_response.get("generations", [])
    if not generations or not generations[0].get("id"):
        raise RuntimeError("Sora job succeeded but returned no generation id.")
    generation_id = generations[0]["id"]
    video_url = f"{base}/video/generations/{generation_id}/content/video?api-version=preview"
    request = urllib.request.Request(video_url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            video_bytes = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[-2000:]
        raise RuntimeError(f"Could not download generated video (HTTP {exc.code}): {detail}") from exc
    if len(video_bytes) < 100_000:
        raise RuntimeError(f"Downloaded video is unexpectedly small: {len(video_bytes)} bytes")
    output.write_bytes(video_bytes)
    manifest.update({
        "status": "downloaded", "generation_id": generation_id,
        "output": str(output.relative_to(ROOT)), "size_bytes": len(video_bytes),
    })
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
