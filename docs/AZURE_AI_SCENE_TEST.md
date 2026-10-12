# Azure AI görsel üretimi — başlangıç kurulumu

Bu manuel GitHub Actions iş akışı Azure AI Foundry'deki FLUX.2-pro modelini çağırıp 1, 3, 6 veya 8 sahne görseli üretir. **İlk testte 1 görsel seçin.** Azure tarafında bütçe/harcama sınırı bu iş akışı tarafından otomatik oluşturulmaz.

## 1. Azure kurulumu

1. Microsoft Foundry'de FLUX.2-pro modelini **Genel Standart (Global Standard)** ile kullanın.
2. Azure portalında AI Services kaynağının **Anahtarlar ve Uç Nokta** bölümünü açın.
3. FLUX BFL API'si için endpoint şu biçimdedir: `https://<resource-name>.api.cognitive.microsoft.com`. Portalda görülen `https://<resource-name>.services.ai.azure.com` Image API endpoint'i FLUX.2-pro için doğru API rotası değildir.
4. Kaynak API anahtarını alın. Anahtarı sohbet mesajına veya kaynak koda yazmayın.

Microsoft'un FLUX.2-pro belgesi: https://learn.microsoft.com/en-us/azure/foundry/foundry-models/how-to/use-foundry-models-flux

## 2. GitHub Secrets ve Variables

GitHub deposu → **Settings → Secrets and variables → Actions**:

**Repository secrets**
- `AZURE_ENDPOINT`: `https://<resource-name>.api.cognitive.microsoft.com` biçimindeki BFL API endpoint'i.
- `AZURE_API_KEY`: Azure AI Services kaynak anahtarı.

**Repository variable (isteğe bağlı)**
- `AZURE_IMAGE_MODEL`: Varsayılan `FLUX.2-pro`; normalde bunu değiştirmeyin.

## 3. İlk testi çalıştır

1. https://github.com/dewadam/cocuk-sarkilari-youtube/actions sayfasını açın.
2. **Azure AI scene image test** iş akışını seçin.
3. **Run workflow** düğmesine basıp `1` görsel seçin.
4. İşlem bitince `azure-ai-scene-test` artifact'ini indirin. İçinde `scene_01.jpg` (veya PNG) ile `manifest.json` bulunur.

İlk test başarılı olmadan 3, 6 veya 8 görsele geçmeyin. Her görsel isteği ücret doğurabilir; gerçek maliyet seçilen çözünürlük ve Azure fiyatlandırmasına bağlıdır.

## Bu aşamanın sınırları

- Bu, yalnızca sahne görseli üretim testidir; henüz tam video üretmez.
- Aynı karakterin görseller arasında birebir tutarlılığı garanti edilmez.
- YouTube'a yükleme bu iş akışında yapılmaz.
- Harcama yalnızca manuel çalıştırmada ve seçilen 1–8 görsel için tetiklenir; Azure tarafında bütçe/harcama uyarısı ayrıca ayarlanmalıdır.
