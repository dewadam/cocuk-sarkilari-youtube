#!/usr/bin/env python3
"""Generate a single high-quality 3D preschool character concept image with Cloudflare Workers AI."""
from __future__ import annotations
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

MODEL = "@cf/black-forest-labs/flux-1-schnell"
PROMPT = (
    "Premium feature-animation still for a preschool nursery-rhyme film, portrait 3:4 composition. "
    "A single irresistibly cute baby lamb character, full body, centered and clearly readable: "
    "round fluffy ivory wool made of many soft individual curls, warm cream face, two long floppy "
    "ears hanging down with subtle pink inner ears, large kind glossy dark eyes with catchlights, "
    "tiny soft muzzle and little nostrils, four short sturdy legs with small dark brown hooves, "
    "small fluffy tail. The lamb stands naturally on all four legs, no arms, no wings, no human hands. "
    "Beautiful high-end stylized 3D animated feature film look, sophisticated soft wool shading, "
    "subtle subsurface scattering, detailed fur, physically based materials, cinematic global illumination, "
    "soft studio key light and rim light, gentle depth of field. Pastel spring meadow with tiny flowers "
    "and softly blurred rolling green hills, warm morning sunlight, appealing color design, polished "
    "professional art direction, clean silhouette, expressive face, exquisite detail. No text, no letters, "
    "no logo, no watermark, no border, no collage, no extra characters."
)

def main() -> int:
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    if not account or not token:
        print("SETUP_REQUIRED: Add GitHub Actions secrets CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN, then rerun this workflow.")
        Path("output").mkdir(exist_ok=True)
        Path("output/SETUP_REQUIRED.txt").write_text(
            "Cloudflare Workers AI image test has not run yet.\n\n"
            "In GitHub: Settings > Secrets and variables > Actions > New repository secret.\n"
            "Add CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN. The token needs permission to run Workers AI.\n"
            "Then open Actions > Generate free AI lamb concept > Run workflow.\n"
            "Do not put the token in source code or commit it.\n",
            encoding="utf-8",
        )
        return 0

    url = f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{MODEL}"
    body = json.dumps({"prompt": PROMPT, "steps": 4, "seed": 20261012}).encode("utf-8")
    request = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=240) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")[-4000:]
        raise RuntimeError(f"Cloudflare API HTTP {exc.code}: {details}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach Cloudflare Workers AI: {exc}") from exc

    if payload.get("success") is False or not isinstance(payload.get("result"), dict):
        raise RuntimeError("Unexpected Cloudflare response: " + json.dumps(payload)[:4000])
    encoded = payload["result"].get("image")
    if not isinstance(encoded, str) or not encoded:
        raise RuntimeError("Cloudflare response did not include result.image: " + json.dumps(payload)[:2000])
    image_bytes = base64.b64decode(encoded, validate=True)
    if not image_bytes.startswith(b"\x89PNG\r\n\x1a\n") and not image_bytes.startswith(b"\xff\xd8\xff"):
        raise RuntimeError("Image response is not a recognized PNG/JPEG file.")
    output = Path("output")
    output.mkdir(parents=True, exist_ok=True)
    extension = ".png" if image_bytes.startswith(b"\x89PNG\r\n\x1a\n") else ".jpg"
    image_path = output / ("AI_lamb_concept" + extension)
    image_path.write_bytes(image_bytes)
    (output / "AI_lamb_prompt.txt").write_text(PROMPT + "\n", encoding="utf-8")
    (output / "AI_lamb_metadata.json").write_text(json.dumps({
        "provider": "Cloudflare Workers AI",
        "model": MODEL,
        "steps": 4,
        "seed": 20261012,
        "bytes": len(image_bytes),
        "format": extension[1:],
        "purpose": "single-image visual quality test; not an animation or final video",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {image_path} ({len(image_bytes)} bytes) with {MODEL}")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"IMAGE_GENERATION_FAILED: {error}", file=sys.stderr)
        raise
