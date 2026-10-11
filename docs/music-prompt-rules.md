# Müzik prompt standardı (TR009 ve sonrası)

## Zorunlu kurallar
1. **Tam şarkı sözleri prompt'un içinde yer almalı.** Yalnızca `lyrics.txt` yolunu yazmak yeterli değildir. Gemini'ye gönderilecek metin, sözlerin tamamını [ŞARKI SÖZLERİ] bölümünde içermeli.
2. **Müzik tarzı her şarkının bestesine göre seçilmeli.** Her yeni şarkıya otomatik olarak aynı çocuk popu/ukulele/el çırpması düzenini vermeyin. Önce sözlerin duygusunu, hikâyesini, hareket ihtiyacını ve öğrenme hedefini değerlendirin; sonra ritim, BPM, vokal yaklaşımı, enstrümanlar ve düzenlemeyi buna göre seçin.
3. **Arka arkaya aynı müzikal kimliği kullanmayın.** Son dört şarkının tür/ritim/enstrüman kombinasyonunu kontrol edin. Aynı ana tür ve aynı ana enstrüman kombinasyonu tekrar etmesin; şarkı sözleri farklıysa bile müzik karakteri de duyulur biçimde farklı olsun.
4. Çocuklara uygunluk ve doğal Türkçe telaffuz korunmalı. Taklit edilen sanatçı, bilinen melodi veya telifli karakter yönlendirmesi yapılmamalı.
5. İlk vokal hedefi 5–7. saniye; ilk söz 5. saniyeden önce başlamamalı, enstrümantal giriş 8 saniyeyi geçmemeli. Bu bir üretim talimatıdır; oluşan ses ayrıca dinlenerek doğrulanmalıdır.
6. Gemini'nin sözlere ekleme yapması durumunda gerçek ses dosyasındaki son sözleri `lyrics.txt` dosyasına aktarın. Altyazı üretiminden önce bu kontrol zorunludur.

## Tarz seçme rehberi
Bunlar sabit reçeteler değil, seçim havuzudur. Her şarkının hikâyesine göre yeni bir karışım da üretilebilir:
- Hareket/oyun: hafif funk, Latin çocuk dansı, ska dokunuşu, groove-pop, ritmik beden perküsyonu.
- Doğa/bahçe: akustik folk, vals, pastoral oda-pop, hafif bluegrass, yumuşak bossa nova.
- Uzay/keşif: sinematik macera-pop, synth-pop, hafif electro-swing, parıltılı elektronik ses manzarası.
- Duygusal/sosyal öğrenme: sıcak piyano-pop, hafif soul, akustik balad-groove, call-and-response.
- Sayma/öğrenme: ritmik chant, marimba ağırlıklı perküsyon, hafif swing, minimal groove.
- Temizlik/rutin: stop-start pop, hafif ska, ritmik funk, oyuncak piyano ve kısa dur-kalk bölümleri.

Her prompt'ta şu özellikler açıkça yazılmalı:
- Ana tür ve enerji
- BPM veya uygun tempo aralığı
- En az 3 belirgin enstrüman/ses kaynağı
- Vokal karakteri ve çocukların eşlik edeceği bölüm
- Açılış ve ara süreleri
- Telif/taklit etmeme talimatı
- Şarkı sözlerinin tamamı

## Yayına hazır olma
Bir şarkının yalnızca MP3 yüklenmiş olması onu üretime hazır yapmaz. Gerçek vokal sözleri kontrol edilmeli, metadata `status: ready` yapılmalı ve ön kontrol raporunda engel kalmamalıdır.
