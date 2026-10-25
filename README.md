# Çocuk Şarkıları YouTube Otomasyonu

GitHub Actions üzerinde çalışacak, Türkçe çocuk şarkıları için özgün beste/söz, görsel-animasyon, video montajı ve YouTube yayınlama hattı.

## Kararlar
- İlk dil: Türkçe
- Hedef sıklık: 4 günde bir (ayda yaklaşık 7–8 video)
- Hedef görsel tarzı: stilize çocuk animasyonu; Azure iptali sonrası aktif üretim yolu prosedürel Pillow + FFmpeg animasyonudur (2D prototip, yüksek kaliteli 3D değildir).
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
6. Blender tabanlı tema-özel 3D sahne prototipi — TR001–TR008 için ayrı karakter/ortam taslakları ve kısa MP4 ön izleme iş akışı eklendi; tam şarkı üretimine henüz bağlanmadı
7. Tema ön izlemesini GitHub Actions üzerinde doğrulama; ardından tam şarkı sahne akışı ve kalite kontrolüne bağlama
8. YouTube API bağlantısı ve manuel onaylı test yüklemesi
9. Her dört günde bir yayın takvimi; otomatik yayın ancak testler tamamlandıktan sonra

## Görsel üretim kararı
- Ücretli görsel/video API'si zorunlu olmayacak. Seçilen başlangıç yaklaşımı Blender + lisansı doğrulanmış ücretsiz 3D varlıklar + FFmpeg; kullanıcı bilgisayarı üretimde kullanılmayacak.
- Kaynak/lisans araştırması: `docs/visual-production-strategy.md`; makinece okunabilir kayıt: `config/visual_asset_sources.json`.
- **Actions → Blender CPU render smoke test → Run workflow:** GitHub Actions üzerinde küçük bir prosedürel 3D test sahnesi üretir ve `blender-cpu-smoke-test` artifact'i verir. Bu, yalnızca Blender/CPU render hattını sınar; nihai çocuk animasyonu değildir.
- **Actions → Blender CPU animation smoke test → Run workflow:** 2 saniyelik, 24 FPS, 320×568 hareketli MP4 test sahnesi üretir; karaktere hafif zıplama ve kol sallama animasyonu ekler. `blender-cpu-animation-smoke-test` artifact'i MP4 ve FFprobe kalite kontrol raporunu içerir. Bu da teknik prototiptir; nihai video kalitesi veya tam şarkı üretimi anlamına gelmez.
- **Actions → Blender CPU 30-second benchmark → Run workflow:** 30 saniyelik, döngüsel karakter hareketi içeren 320×568 MP4 render eder. Artifact; MP4, `.blend` proje dosyası, FFprobe kalite raporu ve gerçek render süresini içerir. Bu ölçüm, tam çözünürlükteki 2–3 dakikalık videoların süresini tahmin etmeden önce kullanılacak düşük çözünürlüklü CPU benchmark'ıdır.
- **Actions → Theme-specific 3D character preview → Run workflow:** TR001–TR008 arasından tema seçerek 3, 5 veya 8 saniyelik, 320×568 prosedürel Blender 3D ön izlemesi üretir. Her tema için farklı karakter/aksesuar ve ortam yaklaşımı kullanılır; MP4, ilk kare PNG, süre/çözünürlük QC raporu ve render süresi artifact olarak verilir. Animasyon anahtar kareleri seçilen sürenin tamamına yayılır. Bu hâlâ görsel prototiptir; yüksek kaliteli nihai animasyon değildir ve ana şarkı render hattına bağlı değildir.
- **Actions → Theme gallery preview (all 8 songs) → Run workflow:** tek çalıştırmada TR001–TR008 temalarının her biri için 3 saniyelik MP4 üretir, çözünürlük/kodlayıcı/süre kontrolü yapar ve sekiz ilk kareyi tek bir karşılaştırma görselinde toplar. Artifact adı `all-eight-theme-gallery`. Bu, karakter tasarımlarını tek tek sekiz iş başlatmadan değerlendirmek içindir; üretim kalitesi onayı yerine geçmez.
- Tema ön izleme iş akışları pahalı render başlamadan önce `app/validate_theme_preview_source.py` ile sekiz tema dalını, dikey çıktı ayarlarını, karakter/çevre animasyonlarını, hafif kamera kayması ve yaklaşmasını, ayrıca YouTube yüklemesinin kapalı kalmasını statik olarak kontrol eder. 3D prototipte karakter zıplaması/kol sallamasına ek olarak balon, yıldız, baloncuk, çiçek ve benzeri seçili çevre öğeleri de yumuşak hareket eder; kamera da çok hafif yana kayıp yaklaşır. Statik kontrol gerçek render veya görsel insan incelemesinin yerine geçmez.
- **Actions → Prepare Blender project for SheepIt → Run workflow:** Blender sahnesini GitHub Actions üzerinde `.blend` dosyası olarak hazırlar; render etmez. `sheepit-blender-project-test` artifact'ini SheepIt'e manuel yükleyerek harici render kuyruğunu test edebilirsin. Bu yalnızca kısa prototiptir ve SheepIt'in puan/kuyruk kurallarına tabidir.
- Kenney Mini Characters, resmî sayfasında CC0 ve animasyon özelliği gösterdiği için yalnızca ilk teknik prototip adayıdır. Nihai çocuk videosu kalitesi henüz kanıtlanmış değildir.
- Bir sonraki teknik doğrulama, GitHub Actions CPU üzerinde kısa Blender sahnesi render edip çalışma süresi ve görsel sonucu değerlendirmektir. Bu prototip başarılı olmadan tüm şarkılara yayılmayacak.

## Müzik prompt standardı
TR009 ve sonraki şarkılarda Gemini prompt'una `lyrics.txt` dosyasındaki sözlerin tamamı doğrudan eklenecek; yalnızca dosya yolu yazılmayacak. Her şarkının müzik tarzı besteye ve hikâyeye göre değiştirilecek; son dört şarkının tür/ritim/enstrüman kombinasyonu tekrar edilmeyecek. Şablon: `templates/music_prompt_template.txt`; ayrıntılar: `docs/music-prompt-rules.md`. Song library preflight yeni şarkılarda tam sözlerin prompt içinde olmasını kontrol eder.

## Pufi Kids: 30 saniyelik animasyon kütüphanesiyle otomatik yayın

Aktif hedef akış, yeni şarkı üretmek için otomatik müzik servisi kullanmak değil; Gemini'de senin hazırladığın MP3'leri GitHub'a yüklediğinde bunları hazır animasyon kütüphanesiyle eşleştirmektir.

1. Sen Gemini'de şarkıyı üretir, şarkı klasörüne `song.mp3` ve eşleşecek `lyrics.txt` dosyasını yüklersin. Yayına hazır şarkının `metadata.json` dosyasında `status: "ready"` olmalı.
2. 500'e kadar yaklaşık 30 saniyelik MP4 klibini GitHub Release asset'leri olarak saklarsın. Büyük MP4'leri normal Git geçmişine ekleme.
3. Her klip için `animation_library/catalog.json` kaydı gerekir: `clip_id`, `asset_url`, `duration_seconds`, `approved`, Türkçe `keywords` ve `tags` ile karakter/eylem/ortam alanları. Video adının tek başına yeterli olduğu varsayılmaz.
4. `.github/workflows/pufi-kids-song-pipeline.yml`, yeni `songs/**/song.mp3` push edildiğinde çalışır. Şarkı sözlerini satır satır tarar, anahtar kelimelerle onaylı klipleri seçer, klipleri art arda birleştirir ve MP3'ü ekleyerek şarkı süresinde 1080×1920 MP4 oluşturur.
5. QC başarısızsa YouTube'a yükleme ve MP3 silme adımı çalışmaz. Push ile başlayan üretimde QC başarılıysa YouTube Data API üzerinden yükleme yapılır. Yükleme başarılı video ID'si döndürdükten sonra kaynak `song.mp3` silinir ve `metadata.json` içinde yayın bilgisi korunur.
6. YouTube kimlik bilgileri GitHub Actions secret `YOUTUBE_OAUTH_TOKEN_JSON` içinde bulunmalıdır. YouTube yüklemesi çocuklara yönelik (`Made for Kids`) olarak işaretlenir.

### İlk kullanım öncesi önemli

- `animation_library/catalog.json` şu anda boş; 500 klibin kendisi ve eşleştirme metadata kayıtları henüz eklenmiş değil. Bu nedenle kütüphane dolmadan üretim iş akışı bilinçli olarak hata verir; rastgele klip seçmez.
- Mevcut şarkı klasörlerinin hepsi otomatik yayına hazır kabul edilmez. Yalnızca `metadata.json` içinde `status: "ready"` olan şarkılar yayınlanabilir.
- Otomatik tetiklenen iş akışı MP3 yüklemesi sonrası yayın yapar. Önce yalnızca önizleme denemek için workflow'u elle başlatıp `publish=false` bırak; yayın için `publish=true` seç.
- GitHub Actions'ın `contents: write` izni, yükleme doğrulandıktan sonra kaynak MP3'ü kaldırıp metadata güncellemesini depoya commit etmek için kullanılır.
- Eski `Pufi Kids - Sequential batch render (up to 500)` iş akışı önceki prosedürel render prototipidir; 500 hazır klip kütüphanesiyle yayın akışının yerine geçmez.

## Testler
- Ekran altyazısı ve otomatik SRT üretimi ana üretim hattından çıkarıldı. Okul öncesi videolar müzik ve görsel hikâyeye odaklanır; storyboard sahneleri doğrulanmamış şarkı sözlerinden değil konu ve öğrenme hedefinden üretilir.
- **Actions → End-to-end song production dry run → Run workflow:** Bir `TRxxx` şarkısını kütüphane uygunluğu, storyboard, görsel istem paketi ve sahne görselleri ön kontrolünden geçirir. Rapor ve oluşturulan dosyalar artifact olarak sunulur. MP4 üretmez, YouTube'a yüklemez ve şarkıyı kullanılmış olarak işaretlemez.
- **Actions → Project validation → Run workflow:** proje ayarları ve birim testleri; video üretmez, YouTube'a yüklemez.
- **Actions → Song library preflight → Run workflow:** şarkı kütüphanesini kontrol eder ve `song-preflight-report` adlı rapor artifact'i üretir. Görsel ön izleme için `status: ready` veya `status: audio_uploaded_lyrics_check` kabul edilir; MP3 bulunmalı ve şarkı daha önce kullanılmamış olmalıdır. `ready` durumu yayın öncesi onay için korunur.
- **Actions → Build storyboard drafts → Run workflow:** tüm şarkılar veya seçilen bir `TRxxx` kimliği için storyboard ve görsel istem paketlerini `storyboard-and-visual-prompt-packs` artifact'inde sunar. Paket; her sahne için ayrı istem dosyaları, şarkıya özel karakter tasarım rehberi ve her isteme eklenen sabit karakter tarifi içerir. TR001–TR008 için karakterler, yardımcı nesneler, renk paleti ve ortamlar ayrı ayrı tanımlanmıştır. Görsel üretimini otomatik yapmaz.
- Storyboard artifact'i yüklenmeden önce `app/validate_visual_prompt_pack.py` çalışır: en az altı sahne istemi, karakter rehberi, her istemdeki karakter kilidi, dikey kadraj ve yazısız görsel kuralları doğrulanır. Bu metin tabanlı kontrol, gerçek görsel üretimi veya görsel kalite incelemesi değildir.
- Render öncesinde `app/validate_assets.py`, en az 6 sahne görseli, kesintisiz ve benzersiz sahne numaraları ve varsa `storyboard.json` sahne sayısını kontrol eder. Eksik sahneler varsa render başlamaz. Altyazı dosyaları kontrol veya render sürecini etkilemez.
- **Actions → Render vertical song video → Run workflow:** `TRxxx` kimliği ister. İlgili klasörde MP3, `metadata.json` içinde `status: ready` veya görsel ön izleme için `audio_uploaded_lyrics_check` ve `usage_status: available` olmalı. Görselleri `songs/TRxxx_.../visuals/scene_01.png`, `scene_02.png` vb. olarak ekleyin. Ekrana şarkı sözü veya altyazı gömülmez. İş akışı 1080×1920, 30 FPS MP4 ön izlemesi üretir; çıktıyı `TRxxx-video-preview` artifact'inden indirin. Bu aşama görsel üretmez ve YouTube'a yükleme yapmaz.
- Render sonrası `app/validate_render.py` MP4'ün okunabilirliğini, video/ses akışlarını, 1080×1920 çözünürlüğü ve ses-video süre farkını kontrol eder. Aynı artifact içinde `TRxxx_qc-report.json` raporu bulunur. Bu teknik kontrol görsel içeriğin doğruluğunu, söz senkronunu veya çocuklara uygunluğunu otomatik olarak onaylamaz.

Ön kontrol aşaması şarkıyı rezerve etmez veya `used` durumuna getirmez. Otomatik yayın kapalıdır; henüz video render'ı ya da YouTube yüklemesi yapılmaz.


### TR002 kuzu karakteri — modelleme düzeltmesi

TR002 ön izlemesindeki genel balon benzeri görünüm yerine ayrı bir kuzu silüeti oluşturulur: sarkık kulaklar ve pembe iç kulaklar, yün bukleleri, ayrı yüz/muzıl ayrıntıları, dört kısa bacak ve koyu toynaklar. Kaynak doğrulayıcı bu temel anatomik bileşenlerin mevcut olduğunu kontrol eder. Bu kontrol görsel kaliteyi tek başına kanıtlamaz; gerçek Blender render çıktısı ayrıca incelenmelidir.


## Animasyon arşivi ve katalog

- Azure üretimi iptal edildiği için Azure tabanlı 3D klip üretimi aktif plandan çıkarıldı. `animation_library/catalog.json` katalog altyapısı korunuyor; ileride ücretsiz, Azure dışı bir kaynak doğrulanırsa kullanılabilir.
- Kalıcı katalog: `animation_library/catalog.json`. Her klip için benzersiz kimlik, dosya adı, kategori, Türkçe anahtar kelimeler/etiketler, karakter, eylem, ortam, ruh hâli, süre, döngü uygunluğu ve MP4 adresi tutulur.
- MP4 dosyaları normal Git geçmişine konmaz. `app/publish_animation_batch.py` onaylı MP4 + aynı adlı JSON yan dosyalarını bir GitHub Release'e yükleyip katalog kaydını hazırlar; bu yardımcı araç mevcut batch-render iş akışının parçası değildir.
- `app/animation_catalog.py` katalog doğrulama ve Türkçe arama yapar. `app/select_animation_clips.py` şarkı sözlerinden etiket eşleşmeleri bulup şarkı süresine göre tekrar edilebilir bir oynatma listesi üretir.
- Aylık şarkı temizliği geçici dosyaları temizlemeli; Release varlıkları ve katalog kayıtları kalıcı kalmalıdır.
- Depo henüz kalıcı MP4 animasyon arşiviyle doldurulmadı. Aktif toplu üretim, şarkı başına prosedürel animasyon döngüsü oluşturur ve YouTube'a otomatik yükleme yapmaz.


### CSV ile üretilen 500 klip kaydını içe aktarma

- CSV kataloğunu `animation_library/source/video_catalog_500.csv` konumuna koyun; MP4'leri `animation_library/inbox/<THEME_CODE>/CLIP###.mp4` altında tema koduna göre düzenleyin.
- `python app/import_video_catalog_csv.py` komutu, CSV ile aynı ID'ye sahip gerçek MP4 dosyalarını eşleştirir, `animation_library/upload_batch/` içine MP4 + JSON yan dosyaları hazırlar ve eksik ID'leri `import-report.json` dosyasına yazar.
- İçe aktarıcı hiçbir klibi otomatik onaylamaz: `approved: false` ve boş `asset_url` ile başlar. Görsel kontrol sonrası onaylanan klipler `app/publish_animation_batch.py` ile GitHub Release'e yüklenmelidir; ancak o zaman gerçek `asset_url` oluşur.
- Örnek `CLIP001.mp4` teknik olarak 30 saniye, 720×1280, H.264 ve 24 FPS'tir. Proje hattı son videoyu 1080×1920 / 30 FPS olarak yeniden kodlar.
- CSV'de 500 kayıt olması 500 MP4'ün mevcut olduğu anlamına gelmez. Bu konuşmada yalnızca CLIP001.mp4 örneği incelendi; bu dosya ve CSV henüz bu commit ile GitHub'a yüklenmedi. GitHub'daki kalıcı katalog/Release asset'leri ayrıca doldurulmalıdır; kalan 499 MP4 olmadan kütüphane tamamlanmış sayılmaz.
