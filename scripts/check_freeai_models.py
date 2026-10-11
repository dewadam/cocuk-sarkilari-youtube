"""Check Free.ai API access and discover music-capable models.

This probe never generates content and never prints the API key.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

BASE_URL = "https://api.free.ai"
KEY_ENV = "FREEAI_API_KEY"


def walk(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in {"id", "name", "model", "model_id", "slug"} and isinstance(child, str):
                yield child
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def main() -> int:
    api_key = os.environ.get(KEY_ENV, "").strip()
    if not api_key:
        print(f"EKSİK: GitHub Actions secret '{KEY_ENV}' tanımlanmamış.")
        return 2

    request = urllib.request.Request(
        f"{BASE_URL}/v1/models",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "User-Agent": "turkce-cocuk-sarkilari-provider-check/0.1",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            status = response.status
    except urllib.error.HTTPError as exc:
        # Avoid printing request headers or secrets. Limit response body in logs.
        detail = exc.read().decode("utf-8", errors="replace")[:600]
        print(f"API HATASI: HTTP {exc.code}. Yanıt: {detail}")
        return 1
    except Exception as exc:
        print(f"BAĞLANTI HATASI: {type(exc).__name__}: {exc}")
        return 1

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        print(f"API JSON döndürmedi (HTTP {status}). İlk 600 karakter: {body[:600]}")
        return 1

    names = sorted(set(walk(payload)))
    candidates = [
        name for name in names
        if any(term in name.lower() for term in ("music", "audio", "ace", "step", "diff", "song", "lyrics"))
    ]

    print(f"API bağlantısı başarılı (HTTP {status}).")
    print("Yanıtta bulunan model/kimlik sayısı:", len(names))
    print("Müzik/ses ile ilişkili olabilecek kayıtlar:")
    if candidates:
        for name in candidates[:100]:
            print("-", name)
    else:
        print("Model adlarında müzik/ses anahtar kelimesi bulunamadı; yanıt biçimi elle incelenmeli.")

    print("\nBu kontrol yalnızca model listesini okur; kredi harcamaz ve şarkı üretmez.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
