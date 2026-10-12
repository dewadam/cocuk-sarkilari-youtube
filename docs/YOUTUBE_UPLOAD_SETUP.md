# YouTube yayın bağlantısı

`.github/workflows/render-video.yml` artık video render ve teknik QC sonrasında isteğe bağlı YouTube yükleme adımını destekler. Workflow ekranında `publish_to_youtube=true` varsayılandır. Yükleme yalnızca şarkı `metadata.json` dosyasında `status: ready` ise çalışır; `audio_uploaded_lyrics_check` durumunda herkese açık yükleme durdurulur.

## Google OAuth secret

YouTube Data API, kanal sahibi adına yükleme yapmak için OAuth 2.0 ister. API anahtarı tek başına yeterli değildir.

1. Google Cloud Console'da bir proje oluştur veya mevcut projeyi seç.
2. **YouTube Data API v3** hizmetini etkinleştir.
3. OAuth consent screen / Google Auth Platform ayarlarını tamamla.
4. OAuth client ID oluştur. Masaüstü uygulaması veya güvenilir bir OAuth akışıyla `https://www.googleapis.com/auth/youtube.upload` kapsamı için izin ver.
5. Uzun süreli kullanım için yenileme belirteci (`refresh_token`) edin. Uygulama test modundaysa Google yenileme belirtecini yaklaşık 7 gün sonra geçersiz kılabilir; kalıcı kullanım için uygun yayın durumu/izinler gerekir.
6. GitHub → **Settings → Secrets and variables → Actions → New repository secret** bölümüne `YOUTUBE_OAUTH_TOKEN_JSON` adında secret ekle. Değer tek bir JSON nesnesi olmalı ve en az şu alanları içermeli:

```json
{
  "client_id": "YOUR_CLIENT_ID",
  "client_secret": "YOUR_CLIENT_SECRET",
  "refresh_token": "YOUR_REFRESH_TOKEN",
  "token_uri": "https://oauth2.googleapis.com/token"
}
```

Gerçek değerleri sohbete veya repoya yazma. Yalnızca GitHub Actions secret olarak kaydet.

## İlk yayın için zorunlu kontroller

- Şarkı MP3 dosyası mevcut olmalı.
- En az 6 sahne görseli, `songs/<ID>_<name>/visuals/scene_01.png` vb. olarak bulunmalı.
- `metadata.json` içindeki `status` yalnızca sözlerin MP3 ile eşleştirilmesi ve içerik incelemesi tamamlandığında `ready` yapılmalı.
- Render ve teknik QC başarıyla bitmeli.
- Workflow YouTube yüklemesinde `selfDeclaredMadeForKids=true` ayarını gönderir. İlk yükleme varsayılan olarak herkese açık olur; `publish_to_youtube=false` seçilirse yalnızca video artifact'i üretilir.

YouTube API kaynakları:
- https://developers.google.com/youtube/v3/guides/uploading_a_video
- https://developers.google.com/youtube/v3/docs/videos/insert
