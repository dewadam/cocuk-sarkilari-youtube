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
1. Yapılandırma ve GitHub Actions doğrulama akışı
2. Ücretsiz/erişilebilir müzik üretim API'sinin doğrulanması
3. Görsel varlıklar ve 3D/hibrit animasyon prototipi
4. Tek videonun uçtan uca üretimi (önce dry-run)
5. YouTube API bağlantısı ve test yüklemesi
6. Her dört günde bir yayın takvimi ve tekrar önleme

## İlk test
GitHub deposunda **Actions → Project validation → Run workflow** ile doğrulama çalıştırılabilir. Bu test video üretmez ve YouTube'a yükleme yapmaz.
