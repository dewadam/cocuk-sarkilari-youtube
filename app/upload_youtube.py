#!/usr/bin/env python3
"""Upload a QC-passed rendered video to YouTube using OAuth credentials from a GitHub secret.

Required environment:
  YOUTUBE_OAUTH_TOKEN_JSON: JSON containing client_id, client_secret, refresh_token,
                           token_uri (usually https://oauth2.googleapis.com/token)
  YOUTUBE_VIDEO_PATH: path to MP4
  YOUTUBE_METADATA_PATH: path to the song metadata.json
Optional:
  YOUTUBE_TAGS: comma-separated tags
  YOUTUBE_PRIVACY_STATUS: public|unlisted|private (default public)
  YOUTUBE_MADE_FOR_KIDS: true (always forced true for this project)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

def main() -> int:
    raw = os.environ.get("YOUTUBE_OAUTH_TOKEN_JSON", "").strip()
    if not raw:
        raise RuntimeError("Missing GitHub Actions secret YOUTUBE_OAUTH_TOKEN_JSON.")
    try:
        token_data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("YOUTUBE_OAUTH_TOKEN_JSON must be valid JSON.") from exc

    required = ("client_id", "client_secret", "refresh_token")
    missing = [key for key in required if not token_data.get(key)]
    if missing:
        raise RuntimeError("OAuth JSON missing required fields: " + ", ".join(missing))

    video_path = Path(os.environ.get("YOUTUBE_VIDEO_PATH", "output/TR001_preview.mp4"))
    if not video_path.is_file() or video_path.stat().st_size < 100_000:
        raise RuntimeError(f"Rendered MP4 missing or unexpectedly small: {video_path}")
    metadata_path = Path(os.environ.get("YOUTUBE_METADATA_PATH", ""))
    if not metadata_path.is_file():
        raise RuntimeError(f"Song metadata file missing: {metadata_path}")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("status") != "ready":
        raise RuntimeError("Public upload is blocked unless metadata.json has status=ready after content review.")
    title = str(metadata.get("youtube_title") or metadata.get("title") or "").strip()
    description = str(metadata.get("youtube_description") or metadata.get("description") or "").strip()
    if not title:
        raise RuntimeError("Approved song metadata must include a title.")
    if not description:
        description = (
            "Türkçe çocuk şarkısı. Özgün müzik ve görsel anlatım. "
            "Çocuklara yönelik içerik olarak işaretlenmiştir. "
            "Ebeveyn gözetiminde dinlenmesi önerilir."
        )
    privacy = os.environ.get("YOUTUBE_PRIVACY_STATUS", "public").strip().lower()
    if privacy not in {"public", "unlisted", "private"}:
        raise RuntimeError("YOUTUBE_PRIVACY_STATUS must be public, unlisted, or private.")

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError as exc:
        raise RuntimeError("Install google-api-python-client and google-auth before upload.") from exc

    credentials = Credentials(
        token=None,
        refresh_token=token_data["refresh_token"],
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )
    youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)
    tags = [item.strip() for item in os.environ.get("YOUTUBE_TAGS", "").split(",") if item.strip()]
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:30],
            "categoryId": "10",
            "defaultLanguage": "tr",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": True,
        },
    }
    media = MediaFileUpload(str(video_path), mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"YouTube upload progress: {int(status.progress() * 100)}%")
    video_id = response.get("id")
    if not video_id:
        raise RuntimeError("YouTube API returned no video ID: " + json.dumps(response)[:2000])
    result = {
        "video_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "privacy_status_requested": privacy,
        "self_declared_made_for_kids": True,
        "file": str(video_path),
    }
    Path("output").mkdir(exist_ok=True)
    Path("output/youtube-upload-result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"YOUTUBE_UPLOAD_FAILED: {error}", file=sys.stderr)
        raise
