# Azure GPU ile AI 3D video üretimi

## Seçilen yaklaşım

Azure OpenAI Sora 2 dağıtımı mevcut abonelik/bölgede kota hatası verdi. Bu nedenle workflow Sora kotasını aşmaya çalışmaz; FLUX ve Python ile çizilmiş karakterler de nihai üretim yöntemi değildir. Plan, açık ağırlıklı Wan 2.2 TI2V-5B modelini Azure GPU VM üzerinde çalıştırmak, GitHub Actions ile üretimi başlatıp videoyu almak ve QC yapmaktır.

Wan-Video'nun resmî deposu TI2V-5B için 720p üretim ve en az 24 GB GPU belleği belirtiyor; model offload, dtype dönüşümü ve T5 CPU seçenekleri bellek kullanımını azaltmaya yardımcı olur. Azure GPU VM kapasitesi ve kota aboneliğe/bölgeye bağlıdır. Azure Machine Learning dokümanları GPU ailelerinde varsayılan kotanın sıfır olabileceğini belirtiyor. Önce Azure Portal > Subscriptions > Usage + quotas ekranında bölge ve GPU ailesi kontrol edilmelidir.

## Kurulum mimarisi

1. Azure Portal'da GPU VM için uygun kota ve kapasite doğrulanır. 24 GB GPU sınıfı ilk test için hedeflenir; uygun değilse VM oluşturulmaz ve kota/uygun SKU çözülür.
2. Linux GPU VM'ye NVIDIA sürücüsü, Docker/NVIDIA Container Toolkit ve Wan 2.2 TI2V-5B ağırlıkları kurulur.
3. VM üzerinde HTTPS ve bearer-token korumasıyla bir worker API çalışır. API sözleşmesi:
   - POST /v1/jobs: model, prompt, duration_seconds, width, height, fps, loop, audio, song_id ve output_format alır.
   - GET /v1/jobs/{job_id}: queued/running/succeeded/failed durumunu ve isteğe bağlı result_url alanını döndürür.
   - GET /v1/jobs/{job_id}/result: MP4 dosyasını döndürür.
4. GitHub repository Settings > Secrets and variables > Actions bölümüne şu değerler eklenir:
   - Secret AZURE_VIDEO_WORKER_URL: worker HTTPS base URL
   - Secret AZURE_VIDEO_WORKER_TOKEN: uzun, rastgele bearer token
   - Variable AZURE_VIDEO_MODEL: Wan2.2-TI2V-5B
5. Azure AI 3D animation loop workflow'u önce TR002 için 5–10 saniyelik test üretir. Görsel kalite ve gerçek render süresi onaylanmadan 30 saniyelik klip ve toplu üretime geçilmez.

## Güvenlik ve maliyet

- GPU VM yalnızca üretim sırasında açık tutulmalı; testten sonra durdurulup deallocate edilmelidir. Disk ve ağ gibi ilişkili kaynaklar ücretlendirmeye devam edebilir.
- Worker internete açılacaksa HTTPS ve güçlü bearer token zorunludur; mümkünse IP allowlist veya private networking kullanılır.
- Model ağırlıkları ilk kurulumda büyük indirme ve disk alanı gerektirir. Model lisansı ve üretilen kliplerin kullanım koşulları arşiv kayıtlarına eklenmelidir.
- Azure kredisi GPU kullanımını karşılayabilir, ancak GPU kapasitesi veya sıfır maliyet garantisi değildir. Azure Pricing Calculator ve kota ekranı önceden kontrol edilmelidir.
- Bu belge ve GitHub istemcisi worker'ın kurulduğu anlamına gelmez. Worker kurulumu, endpoint URL ve token hazır olunca test workflow'u çalıştırılabilir.

## Kaynaklar

- Wan-Video resmî depo: https://github.com/Wan-Video/Wan2.2
- Azure ML GPU quota açıklaması: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-manage-quotas?view=azureml-api-2
