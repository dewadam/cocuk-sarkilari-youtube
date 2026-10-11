# Çocuk Şarkıları YouTube Otomasyonu

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
5. Sahne görsellerinden hareketli dikey MP4 render ve müzik montajı — ilk sürüm eklendi
6. Ücretsiz 3D varlıklar ve Blender tabanlı sahne prototipi — araştırma kararı belgelendi; otomatik render henüz uygulanmadı
7. Tek videonun uçtan uca üretimi ve kalite kontrolü (önce dry-run)
8. YouTube API bağlantısı ve manuel onaylı test yüklemesi
9. Her dört günde bir yayın takvimi; otomatik yayın ancak testler tamamlandıktan sonra

## Görsel üretim kararı
- Ücretli görsel/video API'si zorunlu olmayacak. Seçilen başlangıç yaklaşımı Blender + lisansı doğrulanmış ücretsiz 3D varlıklar + FFmpeg; kullanıcı bilgisayarı üretimde kullanılmayacak.
- Kaynak/lisans araştırması: `docs/visual-production-strategy.md`; makinece okunabilir kayıt: `config/visual_asset_sources.json`.
- **Actions → Blender CPU render smoke test → Run workflow:** GitHub Actions üzerinde küçük bir prosedürel 3D test sahnesi üretir ve `blender-cpu-smoke-test` artifact'i verir. Bu, yalnızca Blender/CPU render hattını sınar; nihai çocuk animasyonu değildir.
- **Actions → Blender CPU animation smoke test → Run workflow:** 2 saniyelik, 24 FPS, 320×568 hareketli MP4 test sahnesi üretir; karaktere hafif zıplama ve kol sallama animasyonu ekler. `blender-cpu-animation-smoke-test` artifact'i MP4 ve FFprobe kalite kontrol raporunu içerir. Bu da teknik prototiptir; nihai video kalitesi veya tam şarkı üretimi anlamına gelmez.
- **Actions → Prepare Blender project for SheepIt → Run workflow:** Blender sahnesini GitHub Actions üzerinde `.blend` dosyası olarak hazırlar; render etmez. `sheepit-blender-project-test` artifact'ini SheepIt'e manuel yükleyerek harici render kuyruğunu test edebilirsin. Bu yalnızca kısa prototiptir ve SheepIt'in puan/kuyruk kurallarına tabidir.
- Kenney Mini Characters, resmî sayfasında CC0 ve animasyon özelliği gösterdiği için yalnızca ilk teknik prototip adayıdır. Nihai çocuk videosu kalitesi henüz kanıtlanmış değildir.
- Bir sonraki teknik doğrulama, GitHub Actions CPU üzerinde kısa Blender sahnesi render edip çalışma süresi ve görsel sonucu değerlendirmektir. Bu prototip başarılı olmadan tüm şarkılara yayılmayacak.

## Müzik prompt standardı
TR009 ve sonraki şarkılarda Gemini prompt'una `lyrics.txt` dosyasındaki sözlerin tamamı doğrudan eklenecek; yalnızca dosya yolu yazılmayacak. Her şarkının müzik tarzı besteye ve hikâyeye göre değiştirilecek; son dört şarkının tür/ritim/enstrüman kombinasyonu tekrar edilmeyecek. Şablon: `templates/music_prompt_template.txt`; ayrıntılar: `docs/music-prompt-rules.md`. Song library preflight yeni şarkılarda tam sözlerin prompt içinde olmasını kontrol eder.

## Testler
- Ekran altyazısı ve otomatik SRT üretimi ana üretim hattından çıkarıldı. Okul öncesi videolar müzik ve görsel hikâyeye odaklanır; storyboard sahneleri doğrulanmamış şarkı sözlerinden değil konu ve öğrenme hedefinden üretilir.
- **Actions → End-to-end song production dry run → Run workflow:** Bir `TRxxx` şarkısını kütüphane uygunluğu, storyboard, görsel istem paketi ve sahne görselleri ön kontrolünden geçirir. Rapor ve oluşturulan dosyalar artifact olarak sunulur. MP4 üretmez, YouTube'a yüklemez ve şarkıyı kullanılmış olarak işaretlemez.
- **Actions → Project validation → Run workflow:** proje ayarları ve birim testleri; video üretmez, YouTube'a yüklemez.
- **Actions → Song library preflight → Run workflow:** şarkı kütüphanesini kontrol eder ve `song-preflight-report` adlı rapor artifact'i üretir. Görsel ön izleme için `status: ready` veya `status: audio_uploaded_lyrics_check` kabul edilir; MP3 bulunmalı ve şarkı daha önce kullanılmamış olmalıdır. `ready` durumu yayın öncesi onay için korunur.
- **Actions → Build storyboard drafts → Run workflow:** tüm şarkılar veya seçilen bir `TRxxx` kimliği için storyboard ve görsel istem paketlerini `storyboard-and-visual-prompt-packs` artifact'inde sunar. Paket; her sahne için ayrı istem dosyaları, sahne dizini ve üretimden önce doldurulacak karakter tutarlılık rehberi içerir. Görsel üretimini otomatik yapmaz.
- Render öncesinde `app/validate_assets.py`, en az 6 sahne görseli, kesintisiz ve benzersiz sahne numaraları ve varsa `storyboard.json` sahne sayısını kontrol eder. Eksik sahneler varsa render başlamaz. Altyazı dosyaları kontrol veya render sürecini etkilemez.
- **Actions → Render vertical song video → Run workflow:** `TRxxx` kimliği ister. İlgili klasörde MP3, `metadata.json` içinde `status: ready` veya görsel ön izleme için `audio_uploaded_lyrics_check` ve `usage_status: available` olmalı. Görselleri `songs/TRxxx_.../visuals/scene_01.png`, `scene_02.png` vb. olarak ekleyin. Ekrana şarkı sözü veya altyazı gömülmez. İş akışı 1080×1920, 30 FPS MP4 ön izlemesi üretir; çıktıyı `TRxxx-video-preview` artifact'inden indirin. Bu aşama görsel üretmez ve YouTube'a yükleme yapmaz.
- Render sonrası `app/validate_render.py` MP4'ün okunabilirliğini, video/ses akışlarını, 1080×1920 çözünürlüğü ve ses-video süre farkını kontrol eder. Aynı artifact içinde `TRxxx_qc-report.json` raporu bulunur. Bu teknik kontrol görsel içeriğin doğruluğunu, söz senkronunu veya çocuklara uygunluğunu otomatik olarak onaylamaz.

Ön kontrol aşaması şarkıyı rezerve etmez veya `used` durumuna getirmez. Otomatik yayın kapalıdır; henüz video render'ı ya da YouTube yüklemesi yapılmaz.
