"""Generate one short, private test track through Free.ai.

This is an explicit manual test only. It never publishes to YouTube.
The provider's public docs show the music endpoint and prompt/duration payload,
but do not fully specify the lyrics/model fields. The script records the
provider response shape so we can adjust safely if the API differs.
"""
from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE_URL = "https://api.free.ai"
KEY_ENV = "FREEAI_API_KEY"
OUTPUT_DIR = Path("output/TR001")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LYRICS = """[Verse]
Haydi çıkalım bahçeye,
Renkler saklanmış neşeyle.
Birlikte bulalım şimdi,
Her renk gülümsesin bize.

[Chorus]
Kırmızı balon göğe çıkar,
Sarı güneş bize bakar.
Mavi gökyüzü, yeşil çimen,
Renklerle şenlenir her yer hemen!"""

PROMPT = (
    "A cheerful original Turkish preschool nursery song with clear, warm, "
    "friendly lead vocals, simple memorable melody, gentle acoustic ukulele, "
    "marimba, hand claps and soft percussion, around 112 BPM, bright and "
    "playful, clear Turkish pronunciation, child-safe, no imitation of any "
    "existing song or artist. Sing the supplied Turkish lyrics exactly."
)


def api_request(path: str, api_key: str, payload: dict | None = None, timeout: int = 120):
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": "turkce-cocuk-sarkilari/0.1",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(BASE_URL + path, data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
            content_type = response.headers.get("Content-Type", "")
            if "json" in content_type or body.lstrip().startswith((b"{", b"[")):
                return response.status, json.loads(body.decode("utf-8")), content_type
            return response.status, body, content_type
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:1200]
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc


def find_string(obj, names):
    if isinstance(obj, dict):
        for name in names:
            value = obj.get(name)
            if isinstance(value, str) and value:
                return value
        for value in obj.values():
            found = find_string(value, names)
            if found:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = find_string(value, names)
            if found:
                return found
    return None


def main() -> int:
    api_key = os.environ.get(KEY_ENV, "").strip()
    if not api_key:
        print(f"EKSİK: GitHub Actions secret '{KEY_ENV}' tanımlanmamış.")
        return 2

    payload = {
        "prompt": PROMPT,
        "lyrics": LYRICS,
        "duration": 30,
        "model": "ace-step",
    }

    print("Free.ai üzerinden tek bir 30 saniyelik Türkçe vokal testi isteniyor.")
    print("Bu işlem token harcayabilir; YouTube'a yükleme yapmaz.")
    # Retry only explicit GPU-busy responses. Other errors are not retried,
    # so malformed requests or authentication failures do not loop.
    result_tuple = None
    for attempt in range(4):  # initial request + at most 3 retries
        try:
            result_tuple = api_request("/v1/music/generate/", api_key, payload)
            break
        except Exception as exc:
            error_text = str(exc)
            is_gpu_busy = "HTTP 503" in error_text and "gpu_busy" in error_text
            if not is_gpu_busy or attempt == 3:
                print(f"MÜZİK İSTEĞİ BAŞARISIZ: {exc}")
                (OUTPUT_DIR / "music_test_error.txt").write_text(
                    "Music generation failed.\n"
                    f"Attempts: {attempt + 1}\n"
                    f"Error: {error_text}\n"
                    "No YouTube upload was attempted.\n",
                    encoding="utf-8",
                )
                return 1
            wait_seconds = 30 * (attempt + 1)
            print(
                f"Free.ai GPU meşgul (503 gpu_busy). "
                f"{wait_seconds} saniye bekleyip tekrar denenecek "
                f"({attempt + 1}/3)."
            )
            time.sleep(wait_seconds)

    if result_tuple is None:
        print("Müzik isteği sonuç vermedi.")
        return 1
    status, result, content_type = result_tuple

    if not isinstance(result, (dict, list)):
        suffix = ".wav" if "wav" in content_type else ".mp3"
        path = OUTPUT_DIR / ("music_test" + suffix)
        path.write_bytes(result)
        print(f"Ses dosyası kaydedildi: {path}")
        return 0

    # Save a redacted summary for debugging; never persist credentials.
    (OUTPUT_DIR / "provider_response.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"API yanıtı alındı (HTTP {status}).")
    usage = result.get("free_ai_usage", {}) if isinstance(result, dict) else {}
    if usage:
        print("Kullanım özeti:", json.dumps(usage, ensure_ascii=False))

    encoded = find_string(result, ("audio_base64", "audio_data", "audioContent"))
    if encoded:
        try:
            raw = base64.b64decode(encoded)
            ext = ".wav" if raw[:4] == b"RIFF" else ".mp3"
            path = OUTPUT_DIR / ("music_test" + ext)
            path.write_bytes(raw)
            print(f"Ses dosyası kaydedildi: {path}")
            return 0
        except Exception as exc:
            print(f"Base64 ses çözülemedi: {type(exc).__name__}")

    audio_url = find_string(result, ("audio_url", "download_url", "file_url", "audioUrl"))
    if audio_url:
        if audio_url.startswith("/"):
            audio_url = BASE_URL + audio_url
        if audio_url.startswith("https://api.free.ai/") or audio_url.startswith("https://free.ai/"):
            request = urllib.request.Request(
                audio_url,
                headers={"Authorization": f"Bearer {api_key}", "User-Agent": "turkce-cocuk-sarkilari/0.1"},
            )
            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    raw = response.read()
                    content_type = response.headers.get("Content-Type", "")
                ext = ".wav" if "wav" in content_type or raw[:4] == b"RIFF" else ".mp3"
                path = OUTPUT_DIR / ("music_test" + ext)
                path.write_bytes(raw)
                print(f"Ses dosyası indirildi: {path}")
                return 0
            except Exception as exc:
                print(f"Ses bağlantısı bulundu ama indirilemedi: {type(exc).__name__}: {exc}")
        else:
            print("Yanıtta ses bağlantısı var ancak güvenlik için farklı alan adına otomatik istek gönderilmedi.")

    job_id = find_string(result, ("job_id", "task_id", "id"))
    if job_id:
        print(f"İş kimliği: {job_id}")
        for attempt in range(24):
            time.sleep(5)
            try:
                poll_status, polled, _ = api_request(
                    "/v1/status/" + urllib.parse.quote(job_id, safe="") + "/", api_key, timeout=30
                )
            except Exception as exc:
                print(f"Durum sorgusu {attempt + 1} başarısız: {exc}")
                continue
            (OUTPUT_DIR / "provider_status.json").write_text(
                json.dumps(polled, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            audio_url = find_string(polled, ("audio_url", "download_url", "file_url", "audioUrl"))
            if audio_url:
                print("İş tamamlandı ve ses bağlantısı alındı; sonraki çalıştırmada indirme işleyicisi genişletilebilir.")
                print("Sağlayıcı durum yanıtı output/TR001/provider_status.json içine kaydedildi.")
                return 0
            state = find_string(polled, ("status", "state"))
            print(f"Durum kontrolü {attempt + 1}/24: {state or 'beklemede'}")
            if isinstance(polled, dict) and polled.get("error"):
                print("Sağlayıcı iş hatası:", str(polled.get("error"))[:500])
                return 1

    print("Sağlayıcı yanıtı ses dosyasına dönüştürülemedi.")
    print("output/TR001/provider_response.json içindeki yanıt şemasını inceleyip API çağrısını uyarlamalıyız.")
    print("Yanıt özeti:", json.dumps(result, ensure_ascii=False)[:1500])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
