# Ücretsiz AI kuzu görseli denemesi

Bu test, Cloudflare Workers AI üzerindeki `@cf/black-forest-labs/flux-1-schnell` modelini kullanarak **tek bir** profesyonel görünümlü kuzu konsept görseli üretir. Henüz video üretmez ve YouTube'a yükleme yapmaz.

## Bir defalık hesap kurulumu

1. Cloudflare hesabı oluştur/aç: https://dash.cloudflare.com/
2. Hesap ana sayfasından **Account ID** değerini kopyala.
3. API token oluştur: https://dash.cloudflare.com/profile/api-tokens . Workers AI'ı çalıştırmaya izin veren en az yetkili token'ı seç.
4. GitHub deposunda **Settings → Secrets and variables → Actions → New repository secret** bölümüne iki gizli değer ekle:
   - `CLOUDFLARE_ACCOUNT_ID` = Cloudflare Account ID
   - `CLOUDFLARE_API_TOKEN` = API token
5. **Actions → Generate free AI lamb concept → Run workflow** seçeneğiyle çalıştır.
6. Çalışma tamamlanınca **AI-lamb-concept** artifact'ini indir. İçindeki PNG/JPG görseli karakter kalitesi değerlendirmesi içindir.

**Güvenlik:** API token'ını sohbet mesajına, kaynak koda veya normal GitHub dosyasına yazma. Yalnızca Actions secret olarak ekle.

## Ücretsiz kota ve güvenli sınır

Cloudflare Workers AI resmî fiyatlandırması ücretsiz planda günde 10.000 Neuron tahsisi belirtir; bu modelin görsel başına tüketimi boyut ve adımlara göre değişir. Bu deneme tek görselle sınırlıdır. Ücretsiz kota aşılırsa ücretsiz plandaki isteklerin hata vermesi beklenir; bu iş akışında ücretli plana yükseltme ya da otomatik ödeme ayarı yapılmaz.

Kaynaklar:
- https://developers.cloudflare.com/workers-ai/platform/pricing/
- https://developers.cloudflare.com/workers-ai/models/flux-1-schnell/

Bu, tek kare görsel üretimidir. Aynı karakterin sahneler boyunca tutarlılığı ve 90–150 saniyelik animasyon ayrı aşamalardır.
