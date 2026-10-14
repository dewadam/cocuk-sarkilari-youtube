# Windows yerel video üretim sunucusu — ilk kurulum

Bu aşama yalnızca mevcut bilgisayarı ve ComfyUI'yi kontrol eder. Video üretmez, YouTube'a yükleme yapmaz, GitHub'a video göndermez ve API anahtarı istemez.

## Hedef mimari

- Windows bilgisayar: ComfyUI/Wan klip üretimi ve FFmpeg ile montaj.
- GitHub: kod, iş kuyruğu tanımları, durum raporları ve iş akışları.
- Yerel servis: sonraki aşamada GitHub'dan kontrollü işleri alacak; bilgisayar kapalıysa iş bekleyecek.
- YouTube: ayrı bir aşama; ilk testlerde otomatik yayın kapalı kalacak.

## Gereksinimler

- Windows 10/11
- NVIDIA sürücüsü ve RTX GPU
- Python 3.10+ (mevcut ComfyUI sanal ortamı ayrıca korunmalı)
- Git
- FFmpeg ve FFprobe
- ComfyUI çalışır durumda, varsayılan API adresi `http://127.0.0.1:8188`

## İlk test

1. Depoyu bilgisayarınızda güncelleyin: `git pull`
2. PowerShell'i depo klasöründe açın.
3. Çalıştırın: `powershell -ExecutionPolicy Bypass -File .\scripts\local_server_preflight.ps1`
4. Çıktının tamamını inceleme için paylaşın. Anahtar, token veya kişisel bilgi eklemeyin.

ComfyUI başka bir portta çalışıyorsa:
`$env:COMFYUI_URL = "http://127.0.0.1:8188"`

## Güvenlik ve sınırlar

- ComfyUI API'sini doğrudan internete açmayın.
- GitHub token'ını kaynak dosyalara yazmayın veya sohbete göndermeyin.
- Büyük MP4 dosyalarını normal Git commit'lerine eklemeyin; gerektiğinde GitHub Releases/Actions artifacts veya ayrı depolama kullanılır.
- Bu ilk kontrol başarılı olmadan sürekli çalışan ajan, otomatik video üretimi veya otomatik YouTube yayınlama etkinleştirilmez.
- Wan 2.1 için 4 GB VRAM sınırlıdır. Uzun videoları tek seferde üretmek yerine kısa klipler ve kontrollü montaj değerlendirilecektir.
