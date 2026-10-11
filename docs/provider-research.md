# Ücretsiz servis araştırması — ilk değerlendirme

Araştırma tarihi: 2026-10-11

## 1. Beste ve vokal

Aday: Free.ai müzik API'si
- API: https://free.ai/api/
- Müzik aracı: https://free.ai/music/
- Sağlayıcının yayımladığı bilgi: ücretsiz hesap için günlük 30.000 token ve ayda 1.000 API isteği; müzik üretimi API uç noktası `POST /v1/music/generate/`.
- Müzik sayfası, ACE-Step ile sözlü/vokalli şarkı üretilebildiğini ve üretilen müziğin ticari projelerde kullanılabileceğini belirtiyor.
- API sayfasındaki model/tablo açıklaması ise AudioLDM 2'yi öne çıkarıyor ve örnek API çağrısı sadece prompt + duration içeriyor. Bu, web arayüzündeki ACE-Step/vokal açıklamasıyla tam olarak örtüşmüyor.

**Karar:** Henüz üretim sağlayıcısı olarak sabitleme. Önce API anahtarıyla düşük maliyetli bir test yapıp şu maddeleri doğrula:
1. API üzerinden Türkçe sözleri gerçekten söyleyen vokalli parça üretilebiliyor mu?
2. Üretilen parçanın süresi ve ses kalitesi çocuk şarkısına uygun mu?
3. Günlük token tüketimi gerçek yanıtta ne kadar?
4. Ticari kullanım koşulları ilgili model için de geçerli mi?

## 2. Görsel ve video

Free.ai API sayfasında görsel üretimi ve video üretimi uç noktaları bulunuyor. Ancak ücretsiz video kotası çok sınırlı ve video üretimi için yayımlanan API örnekleri premium modelleri gösteriyor. Bu yüzden 90–150 saniyelik bir çocuk şarkısının tamamını üretken video modeliyle üretmek başlangıç planı değil.

İlk yaklaşım: lisansı kontrol edilmiş ücretsiz 3D karakter/çevre varlıkları + Blender ile sınırlı/tekrar kullanılabilir animasyon döngüleri + FFmpeg ile montaj. GitHub Actions standart sunucularında GPU varsayılmayacak; ilk prototipin render süresi ölçülecek.

## 3. GitHub Actions

Resmî GitHub belgeleri standart runner'ların herkese açık depolarda ücretsiz olduğunu, özel depolarda ise plana bağlı ücretsiz dakika kotası bulunduğunu söylüyor. Bu proje deposu özeldir; bu nedenle ağır render işlemlerini doğrudan ve sınırsız biçimde ücretsiz varsayma. İlk test kısa tutulacak.

Kaynak: https://docs.github.com/en/billing/concepts/product-billing/github-actions

## 4. YouTube

YouTube Data API `videos.insert` ile video ve meta verileri yüklenebilir; `status.selfDeclaredMadeForKids` alanıyla çocuklara yönelik içerik belirtilebilir. Ancak API projesinin doğrulama/audit gereklilikleri nedeniyle herkese açık yayınlama durumu ayrıca kontrol edilmeli.

Kaynak: https://developers.google.com/youtube/v3/docs/videos/insert

## 5. Gizli bilgiler

API anahtarları GitHub Actions Secrets içine eklenecek. Anahtarları sohbet mesajına veya depodaki dosyalara koyma. Bu aşamada hiçbir YouTube yüklemesi otomatik çalışmaz.
