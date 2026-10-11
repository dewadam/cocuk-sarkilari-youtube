# Türkçe Çocuk Şarkıları Otomasyonu

GitHub Actions üzerinde çalışacak, Türkçe çocuk şarkıları için özgün beste/söz, görsel-animasyon, video montajı ve YouTube yayınlama hattı.

## Kararlar
- İlk dil: Türkçe
- Hedef sıklık: 4 günde bir (ayda yaklaşık 7–8 video)
- Hedef görsel tarzı: yüksek kaliteli, stilize 3D
- Çalışma ortamı: bulut; kullanıcının bilgisayarı üretim sırasında gerekmez
- Öncelik: ücretsiz servisler ve açık kaynaklı araçlar
- Çocuklara yönelik içerik YouTube'da doğru biçimde "Made for Kids" olarak işaretlenecek
- İlk aşama: manuel doğrulama; otomatik yayın varsayılan olarak kapalı
- Diğer diller (İngilizce, Rusça, Almanca) ancak Türkçe hattı ve ücretsiz limitler doğrulandıktan sonra

## Güvenlik
- API anahtarları veya OAuth dosyaları depoya commit edilmez.
- YouTube'a yükleme, açıkça yapılandırılmadıkça ve test edilmedikçe çalıştırılmaz.
- Otomatik yayın öncesinde özgünlük, lisans, video kalitesi ve tekrar kontrolü yapılır.

## Aşamalar
1. Yapılandırma ve GitHub Actions doğrulama akışı — tamamlandı
2. Manuel Gemini müzik üretimi ve GitHub şarkı kütüphanesi — devam ediyor
3. Şarkı ön kontrolü: MP3 varlığı, söz kontrol durumu, SHA-256 ve tekrar kullanım engeli — ilk sürüm eklendi
4. Şarkı konularından dikey 9:16 storyboard taslakları üretme — ilk sürüm eklendi
5. Storyboard'dan stilize 3D sahne render'ı ve müzikle montaj
6. Tek videonun uçtan uca üretimi ve kalite kontrolü (önce dry-run)
7. YouTube API bağlantısı ve manuel onaylı test yüklemesi
8. Her dört günde bir yayın takvimi; otomatik yayın ancak testler tamamlandıktan sonra

## Müzik prompt standardı
TR009 ve sonraki şarkılarda Gemini prompt'una `lyrics.txt` dosyasındaki sözlerin tamamı doğrudan eklenecek; yalnızca dosya yolu yazılmayacak. Her şarkının müzik tarzı besteye ve hikâyeye göre değiştirilecek; son dört şarkının tür/ritim/enstrüman kombinasyonu tekrar edilmeyecek. Şablon: `templates/music_prompt_template.txt`; ayrıntılar: `docs/music-prompt-rules.md`. Song library preflight yeni şarkılarda tam sözlerin prompt içinde olmasını kontrol eder.

## Testler
- **Actions → Project validation → Run workflow:** proje ayarları ve birim testleri; video üretmez, YouTube'a yüklemez.
- **Actions → Song library preflight → Run workflow:** şarkı kütüphanesini kontrol eder ve `song-preflight-report` adlı rapor artifact'i üretir. Yalnızca `metadata.json` içinde `status: ready` olan, MP3 ve söz dosyası bulunan, daha önce kullanılmamış şarkılar video üretimine uygun sayılır.
- **Actions → Build storyboard drafts → Run workflow:** tüm şarkılar veya seçilen bir `TRxxx` kimliği için `storyboard-drafts` artifact'i üretir. Taslaklar 9:16 kadraj, sahne zaman aralıkları, sahneye özel görsel üretim prompt'ları ve taslak söz ipuçları içerir; gerçek 3D render ve vokalle kare-kare senkron henüz yapılmaz.

Ön kontrol aşaması şarkıyı rezerve etmez veya `used` durumuna getirmez. Otomatik yayın kapalıdır; henüz video render'ı ya da YouTube yüklemesi yapılmaz.
