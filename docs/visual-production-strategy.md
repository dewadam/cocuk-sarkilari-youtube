# Görsel üretim stratejisi: ücretsiz ve tutarlı 3D

## Karar

Üretim hattı ücretli görsel/video API'sine bağımlı olmayacak. İlk araştırma ve prototip için Blender + FFmpeg + lisansı tek tek doğrulanmış ücretsiz 3D varlıklar kullanılacak. Blender sahneleri düzenlemek/render etmek için; FFmpeg son videoyu birleştirmek için kullanılacak. GitHub Actions bulut çalışma ortamıdır; kullanıcının bilgisayarı üretim için kullanılmaz.

## Kaynak seçimi

- **Kenney Mini Characters** — https://kenney.nl/assets/mini-characters
  - Resmî sayfada 3D/Mini, Animation özelliği ve CC0 lisansı belirtiliyor.
  - İlk teknik prototip için uygun adaydır; nihai çocuk içeriği kalitesini tek başına garanti etmez.
- **Kenney destek/lisans açıklaması** — https://kenney.nl/support
  - Kenney varlıklarının CC0 olduğu, ticari projelerde kullanılabildiği ve atfın zorunlu olmadığı belirtiliyor.
- **Blender lisansı** — https://www.blender.org/about/license/
  - Blender özgür/açık kaynaklıdır; Blender ile üretilen eserler kullanıcıya aittir.
- **FFmpeg** — https://ffmpeg.org/
  - Video birleştirme, ses ekleme, çözünürlük ve kare hızı standardizasyonu için kullanılacak. Dağıtım koşulları kullanılan derleme ve codec'lere göre kontrol edilmelidir.

## Kalite ilkeleri

1. Bir ana karakterin görünümü, renkleri ve oranları tüm sahnelerde korunmalı.
2. Her sahne hikâyeye hizmet etmeli; yalnızca rastgele görsel veya ritim vuruşuna tepki olmamalı.
3. Hareketler anlamlı olmalı: yürüme, işaret etme, nesneyle etkileşim, dans veya duygusal tepki.
4. Kamera hareketi ve geçişler yumuşak olmalı; her birkaç saniyede bir sebepsiz kesme yapılmamalı.
5. Ekran yazısı, altyazı ve şarkı sözü kullanılmamalı.
6. Görsel kaynağın lisansı ve gerekiyorsa atıf bilgisi asset manifestinde saklanmalı.
7. İlk prototip yalnızca teknik olarak render oldu diye başarılı sayılmamalı; karakter tutarlılığı, kompozisyon, hareket ve hikâyeyle uyum ayrı değerlendirilmelidir.

## Gerçekçi sınırlar

- GitHub Actions standart sunucuları GPU'lu değildir. Blender render'ı CPU'da yapılabilir, ancak karmaşık sahnelerde yavaşlayabilir ve ücretsiz dakika kotasına takılabilir.
- Kenney gibi oyun varlıkları teknik başlangıç sağlar; premium çocuk animasyonu estetiği için malzeme, ışık, çevre ve hareket tasarımı gerekir.
- Bu aşamada otomatik YouTube yüklemesi yoktur.
- Varlık paketleri lisans ve kaynak bağlantısı kontrol edilmeden depoya topluca kopyalanmamalıdır.

## Uygulama sırası

1. Kaynak ve lisans manifestini koru.
2. Tek bir kısa örnek sahneyle Blender'ın GitHub Actions üzerinde CPU render süresini ölç.
3. Süre ve kalite uygunsa bir şarkı için tekrar kullanılabilir karakter/çevre sahne şablonları hazırla.
4. Sahne seçimini şarkı teması ve öğrenme hedefine bağla.
5. FFmpeg ile ses ve sahneleri birleştir; teknik QC çalıştır.
6. Bir örnek çıktıyı değerlendirmeden toplu üretime ve YouTube yüklemesine geçme.
