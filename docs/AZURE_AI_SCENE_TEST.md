# Azure AI görsel üretimi — başlangıç kurulumu

Bu iş akışı, Azure AI Foundry'de dağıtılmış bir FLUX görsel modelini çağırır ve 1, 3, 6 veya 8 sahne görseli üretir. Otomatik tetiklenmez; yalnızca Actions ekranından manuel başlatılır. Her çalıştırmada en fazla 8 görsel üretilebilir. Bu, harcamayı sınırlar; Azure kredisi veya kaynak oluşturma işlemi bu dosyalar tarafından otomatik olarak yapılamaz.

## 1. Azure kurulumu

1. Azure portalında başlangıç kredisi olan aboneliğine gir.
2. Microsoft Foundry'de bir Foundry kaynağı oluştur ve bölgen için kullanılabilir bir FLUX görsel modelini dağıt. Model/dağıtım erişimi ve ücretler bölgeye göre değişebilir.
3. Dağıtım ekranındaki endpoint ve API anahtarını al. FLUX Image API için endpoint şu biçimdedir: `https://<resource-name>.services.ai.azure.com`.
4. Önce Azure portalındaki fiyatlandırma ve kota bilgilerini kontrol et. İlk test 6 görselle sınırlıdır; bu workflow otomatik olarak bakiye sınırı veya Azure bütçesi oluşturmaz.

## 2. GitHub Secrets ve Variables

GitHub deposu → **Settings → Secrets and variables → Actions**:

**Repository secrets**
- `AZURE_ENDPOINT`: Kaynağın endpoint'i; `https://` ile başlayacak, sonuna `/openai` ekleme.
- `AZURE_API_KEY`: Azure AI Foundry API anahtarı.

**Repository variables**
- `AZURE_IMAGE_MODEL`: Foundry'de dağıttığın modelin deployment adı (katalogdaki model etiketi olmak zorunda değildir).

Anahtarları sohbet mesajına veya kaynak koda yazma.

## 3. Testi başlat

1. [GitHub Actions](https://github.com/dewadam/cocuk-sarkilari-youtube/actions) sayfasını aç.
2. **Azure AI scene image test** iş akışını seç.
3. **Run workflow** → başlangıç için **6** görsel seç.
4. Tamamlanınca `azure-ai-scene-test` artifact'ini indir. `scene_01.png` gibi dosyalar ile `manifest.json` içinde kullanılan prompt'lar bulunur.

## API

Kod, Microsoft Foundry FLUX Image API'sini kullanır: `/openai/v1/images/generations?api-version=preview`. Resmî dokümantasyon: https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-models/how-to/use-foundry-models-flux

## Bu aşamanın sınırları

- Bu, yalnızca sahne görseli üretim testidir; henüz tam video üretmez.
- Aynı karakterin görseller arasında birebir tutarlılığı garanti edilmez.
- YouTube'a yükleme bu iş akışında yapılmaz.
- Harcama yalnızca manuel çalıştırmada ve seçilen 1–8 görsel için tetiklenir; Azure tarafında bütçe/harcama uyarısı ayrıca ayarlanmalıdır.
