#!/usr/bin/env python3
"""Generate a bounded batch of FLUX.2-pro scene images through Azure AI Foundry.

Uses the BFL provider-specific API documented by Microsoft for FLUX.2-pro.
Required environment:
  AZURE_ENDPOINT=https://<resource-name>.services.ai.azure.com
  AZURE_API_KEY=<resource key>
Optional:
  AZURE_IMAGE_COUNT=1
  AZURE_IMAGE_SIZE=1024x1024
"""
from __future__ import annotations

import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

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
    "The same cute baby lamb rests peacefully under a soft pastel rainbow after a happy day, gentle warm light, comforting final scene.",
]


def fail(message: str) -> None:
    raise RuntimeError(message)


def find_image_value(value: Any) -> tuple[str | None, str | None]:
    """Find common image URL/base64 fields in provider responses."""
    if isinstance(value, dict):
        for key in ("b64_json", "image_base64", "base64", "image"):
            item = value.get(key)
            if isinstance(item, str) and item:
                return "base64", item
        for key in ("url", "sample", "image_url"):
            item = value.get(key)
            if isinstance(item, str) and item.startswith(("https://", "http://")):
                return "url", item
        for item in value.values():
            found = find_image_value(item)
            if found[0]:
                return found
    elif isinstance(value, list):
        for item in value:
            found = find_image_value(item)
            if found[0]:
                return found
    return None, None


def main() -> int:
    endpoint = os.environ.get("AZURE_ENDPOINT", "").strip().rstrip("/")
    key = os.environ.get("AZURE_API_KEY", "").strip()
    model = os.environ.get("AZURE_IMAGE_MODEL", "FLUX.2-pro").strip() or "FLUX.2-pro"
    size = os.environ.get("AZURE_IMAGE_SIZE", "1024x1024").strip()
    try:
        count = int(os.environ.get("AZURE_IMAGE_COUNT", "1"))
    except ValueError:
        fail("AZURE_IMAGE_COUNT must be an integer.")

    if not endpoint or not key:
        print("SETUP_REQUIRED: Configure AZURE_ENDPOINT and AZURE_API_KEY as GitHub Actions secrets.")
        OUTPUT.mkdir(parents=True, exist_ok=True)
        (OUTPUT / "SETUP_REQUIRED.txt").write_text(
            "No Azure request was made. Configure the BFL provider endpoint and resource API key in GitHub Actions.\n",
            encoding="utf-8",
        )
        return 0
    if count < 1 or count > 8:
        fail("AZURE_IMAGE_COUNT must be between 1 and 8 to keep the test spend bounded.")
    match = re.fullmatch(r"(\d{3,4})x(\d{3,4})", size)
    if not match:
        fail("AZURE_IMAGE_SIZE must look like 1024x1024.")
    width, height = int(match.group(1)), int(match.group(2))
    if width * height > 4_000_000:
        fail("FLUX.2-pro output is limited to 4 megapixels.")
    url = endpoint + "/providers/blackforestlabs/v1/flux-2-pro?api-version=preview"
    OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest = {
        "provider": "Azure AI Foundry / Black Forest Labs",
        "model": model,
        "endpoint_route": "/providers/blackforestlabs/v1/flux-2-pro?api-version=preview",
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
            "width": width,
            "height": height,
            "output_format": "jpeg",
            "num_images": 1,
        }).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")[-3000:]
            fail(f"Azure FLUX request {index}/{count} failed with HTTP {exc.code}: {details}")
        except urllib.error.URLError as exc:
            fail(f"Could not reach Azure AI Foundry: {exc}")

        kind, image_value = find_image_value(payload)
        if not kind or not image_value:
            fail("Unexpected Azure FLUX response; no image URL/base64 found: " + json.dumps(payload)[:3000])
        if kind == "base64":
            try:
                image_bytes = base64.b64decode(image_value, validate=True)
            except Exception as exc:
                fail(f"Could not decode returned image data: {exc}")
        else:
            image_request = urllib.request.Request(
                image_value, headers={"User-Agent": "kids-song-pipeline/1.0"}
            )
            try:
                with urllib.request.urlopen(image_request, timeout=120) as response:
                    image_bytes = response.read()
            except urllib.error.URLError as exc:
                fail(f"Could not download generated image: {exc}")

        if image_bytes.startswith(b"\xff\xd8\xff"):
            ext = ".jpg"
        elif image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            ext = ".png"
        else:
            fail(f"Scene {index} response was not a recognized PNG/JPEG image.")
        filename = f"scene_{index:02d}{ext}"
        (OUTPUT / filename).write_bytes(image_bytes)
        manifest["images"].append({
            "file": filename,
            "bytes": len(image_bytes),
            "prompt": prompt,
        })
        print(f"Generated {index}/{count}: {filename} ({len(image_bytes)} bytes)")

    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Done: {len(manifest['images'])} images saved under {OUTPUT}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"AZURE_IMAGE_GENERATION_FAILED: {error}", file=sys.stderr)
        raise
