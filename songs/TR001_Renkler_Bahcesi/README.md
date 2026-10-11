# TR001 — Renkler Bahçesi

Bu klasör bir şarkının tüm üretim girdilerini ve ses dosyasını bir arada tutar.

## Dosyalar
- `song.mp3`: Gemini'dan indirilen gerçek şarkı dosyası.
- `lyrics.txt`: Şarkıda gerçekten söylenen son sözler. Altyazılar bu dosyadan hazırlanacak.
- `music_prompt.txt`: Gemini'da kullanacağın prompt.
- `metadata.json`: Otomasyonun okuyacağı kimlik, durum ve tekrar-kullanım bilgileri.

## MP3 yükleme
1. Gemini'dan indirdiğin **Renkler Bahçesi** MP3 dosyasını bu klasöre yükle.
2. Dosya adını tam olarak `song.mp3` yap.
3. `lyrics.txt` dosyasını MP3'te gerçekten söylenen tüm sözlerle eşleştir. Gemini ek sözler ürettiyse onları da ekle.
4. `metadata.json` içindeki `status` değerini `ready` yap.

## Tekrar kullanım kuralı
Bir şarkı bir video için rezerve edildiğinde `reserved`, video başarıyla üretildiğinde `used` olarak işaretlenecek. Kullanılan şarkılar sonraki video seçimlerinde atlanacak. Dosya SHA-256 özeti de tekrar kontrolü için saklanacak.

Şimdilik bu kayıtlar manuel hazırlanıyor; otomatik video üretim hattı tamamlanana kadar YouTube'a yükleme yapılmaz.
