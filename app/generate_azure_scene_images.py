#!/usr/bin/env python3
"""Generate a bounded batch of AI scene images through Azure AI Foundry's FLUX Image API.

The script is intentionally manual-run and caps a batch at 8 images to control spend.
Required environment:
  AZURE_ENDPOINT=https://<resource-name>.services.ai.azure.com
  AZURE_API_KEY=<secret>
  AZURE_IMAGE_MODEL=<deployment name, e.g. your FLUX-1.1-pro deployment>
Optional:
  AZURE_IMAGE_SIZE=1024x1024
  AZURE_IMAGE_COUNT=6
"""
from __future__ import annotations

import base64
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "azure-scene-test"
BASE_PROMPT = (
    "Premium high-end stylized 3D preschool animated feature film still, vertical-friendly "
    "composition, warm cinematic global illumination, soft detailed materials, expressive friendly "
    "characters, beautifully art-directed pastel colors, clear readable silhouette, professional "
    "family animation quality. No text, no letters, no subtitles, no logo, no watermark."
)
SCENES = [
    "A cute baby lamb with ivory wool curls, cream face, floppy ears, large kind glossy eyes and four short legs stands in a sunlit spring meadow, tiny flowers and rolling green hills, full body, natural quadruped anatomy, no arms or wings.",
    "The same cute baby lamb with ivory wool curls and cream face gently hops beside colorful spring flowers in a sunny meadow, joyful expression, dynamic but anatomically natural four-legged lamb pose.",
    "The same cute baby lamb discovers a small blue butterfly resting on a flower, close medium shot, soft morning sunlight, lush meadow, gentle curiosity.",
    "The same cute baby lamb walks along a winding path between rounded pastel hills, a few friendly birds in the distant sky, wide establishing shot, bright cheerful atmosphere.",
    "The same cute baby lamb plays beside a tiny sparkling stream with smooth stones and flowers, reflections, calm joyful preschool storybook mood.",
    "The same cute baby lamb smiles toward camera in a flower-filled meadow at golden hour, cinematic hero shot, beautiful soft bokeh, clean uncluttered background.",
    "The same cute baby lamb dances naturally on all four legs in a sunny clearing, flowers swaying in a light breeze, lively celebratory composition.",
    "The same cute baby lamb rests peacefully under a soft pastel rainbow after a happy day, gentle warm light, comforting final scene."
]


def fail(message: str) -> None:
    raise RuntimeError(message)


def main() -> int:
    endpoint = os.environ.get("AZURE_ENDPOINT", "").strip().rstrip("/")
    key = os.environ.get("AZURE_API_KEY", "").strip()
    model = os.environ.get("AZURE_IMAGE_MODEL", "").strip()
    size = os.environ.get("AZURE_IMAGE_SIZE", "1024x1024").strip()
    try:
        count = int(os.environ.get("AZURE_IMAGE_COUNT", "6"))
    except ValueError:
        fail("AZURE_IMAGE_COUNT must be an integer.")
    if not endpoint or not key or not model:
        print("SETUP_REQUIRED: Configure AZURE_ENDPOINT, AZURE_API_KEY and AZURE_IMAGE_MODEL as GitHub Actions secrets/variables.")
        OUTPUT.mkdir(parents=True, exist_ok=True)
        (OUTPUT / "SETUP_REQUIRED.txt").write_text(
            "No Azure request was made. Configure the Azure endpoint, API key, and deployed image model name in GitHub Actions.\n",
            encoding="utf-8",
        )
        return 0
    if count < 1 or count > 8:
        fail("AZURE_IMAGE_COUNT must be between 1 and 8 to keep the test spend bounded.")
    if not re.fullmatch(r"\\d{3,4}x\\d{3,4}", size):
        fail("AZURE_IMAGE_SIZE must look like 1024x1024.")

    # Current Microsoft Foundry Image API for FLUX models.
    url = endpoint + "/openai/v1/images/generations?api-version=preview"
    OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest = {
        "provider": "Azure AI Foundry",
        "model_deployment": model,
        "size": size,
        "requested_images": count,
        "prompt_prefix": BASE_PROMPT,
        "images": [],
    }

    for index, scene in enumerate(SCENES[:count], start=1):
        prompt = BASE_PROMPT + " " + scene
        body = json.dumps({
            "model": model,
            "prompt": prompt,
            "n": 1,
            "size": size,
        }).encode("utf-8")
        request = urllib.request.Request(
            url, data=body, method="POST",
            headers={"api-key": key, "Content-Type": "application/json", "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=240) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")[-3000:]
            fail(f"Azure image request {index}/{count} failed with HTTP {exc.code}: {details}")
        except urllib.error.URLError as exc:
            fail(f"Could not reach Azure AI Foundry: {exc}")

        items = payload.get("data")
        if not isinstance(items, list) or not items:
            fail("Unexpected Azure response: " + json.dumps(payload)[:2000])
        item = items[0]
        if item.get("b64_json"):
            image_bytes = base64.b64decode(item["b64_json"], validate=True)
        elif item.get("url"):
            image_request = urllib.request.Request(item["url"], headers={"User-Agent": "kids-song-pipeline/1.0"})
            with urllib.request.urlopen(image_request, timeout=120) as response:
                image_bytes = response.read()
        else:
            fail("Azure response had neither data[0].b64_json nor data[0].url.")
        if not (image_bytes.startswith(b"\\x89PNG\\r\\n\\x1a\\n") or image_bytes.startswith(b"\\xff\\xd8\\xff")):
            fail(f"Scene {index} response was not a recognized PNG/JPEG.")
        ext = ".png" if image_bytes.startswith(b"\\x89PNG\\r\\n\\x1a\\n") else ".jpg"
        filename = f"scene_{index:02d}{ext}"
        (OUTPUT / filename).write_bytes(image_bytes)
        manifest["images"].append({
            "file": filename,
            "bytes": len(image_bytes),
            "prompt": prompt,
        })
        print(f"Generated {index}/{count}: {filename} ({len(image_bytes)} bytes)")

    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
    print(f"Done: {len(manifest['images'])} images saved under {OUTPUT}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"AZURE_IMAGE_GENERATION_FAILED: {error}", file=sys.stderr)
        raise
