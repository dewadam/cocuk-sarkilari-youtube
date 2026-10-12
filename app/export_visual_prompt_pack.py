"""Export storyboard JSON into a copy-ready visual prompt pack."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_") or "song"

CHARACTER_BIBLES = {
    "TR001": {
        "hero": "Pofuduk adlı minik turkuaz bahçe arkadaşı; büyük oval kafa, küçük yuvarlak gövde, mercan pembe yanaklar, iri koyu gözler ve kısa kollar. Başında küçük pembe balon düğümü biçimli çıkıntı.",
        "companions": "kırmızı ve sarı gülen balonlar; basit, sevimli yüz ifadeleri",
        "palette": "turkuaz, yaprak yeşili, güneş sarısı ve mercan pembe",
        "setting": "çiçekli, bakımlı okul öncesi bahçesi"
    },
    "TR002": {
        "hero": "Ponçik adlı minik krem renkli kuzu; yumuşak kıvırcık yün tutamı, kısa pembe kulak içleri, küçük kahverengi toynaklar, yuvarlak yanaklar ve büyük koyu gözler.",
        "companions": "aynı yumuşak 3D stilde dost canlısı benekli inek, sarı gagalı beyaz ördek ve kırmızı ibikli horoz",
        "palette": "krem, saman sarısı, çimen yeşili, gök mavisi ve yumuşak kahve",
        "setting": "temiz, güneşli ve çocuk dostu çiftlik avlusu"
    },
    "TR003": {
        "hero": "Pırıl adlı sevimli inci beyazı diş karakteri; geniş yuvarlak taç, iki kısa diş kökü, minik pembe yanaklar ve iri koyu gözler.",
        "companions": "pembe saplı çocuk diş fırçası ve şeffaf sabun köpüğü baloncukları",
        "palette": "inci beyazı, pastel mavi, mint ve pembe",
        "setting": "yuvarlak kenarlı lavabolu, temiz ve aydınlık çocuk banyosu"
    },
    "TR004": {
        "hero": "Çufçuf adlı parlak kırmızı oyuncak tren; mavi kabin, sarı kısa baca, büyük siyah tekerlekler ve ön yüzünde neşeli bir ifade.",
        "companions": "yuvarlak peluş ayı, renkli bloklar ve resimli kitaplar",
        "palette": "kırmızı, mavi, sarı, ahşap kahvesi",
        "setting": "sıcak ışıklı, düzenli çocuk oyun odası ve alçak oyuncak rafları"
    },
    "TR005": {
        "hero": "Mino adlı küçük gümüş uzay robotu; yuvarlak kask başı, turkuaz gövde, iki sarı LED göz ve uçlarında pembe ışık bulunan kısa antenler.",
        "companions": "mor halkalı gezegen, dost canlısı küçük roket ve yuvarlak yıldızlar",
        "palette": "lacivert, mor, gümüş, turkuaz ve sarı",
        "setting": "yumuşak ışıklı, renkli ve korkutucu olmayan masalsı uzay"
    },
    "TR006": {
        "hero": "Üç değişmeyen geometrik arkadaş: mercan pembe daire, güneş sarısı yuvarlatılmış kare ve turkuaz üçgen; her birinde küçük koyu gözler ve sade gülümseme.",
        "companions": "aynı üç şeklin küçük tekrarları, basit renkli dans pisti işaretleri",
        "palette": "pembe, sarı, turkuaz ve mor",
        "setting": "temiz, geometrik desenli, çocuklara uygun dans sahnesi"
    },
    "TR007": {
        "hero": "Ada adlı minik bahçıvan; krem ten, kahverengi kısa saç, turuncu tulum, yuvarlak yüz ve büyük koyu gözler.",
        "companions": "kırmızı saksıdaki tek filiz; yaprak sayısı hikâyede büyüme aşamasına göre değişebilir",
        "palette": "yaprak yeşili, toprak kahvesi, turuncu ve güneş sarısı",
        "setting": "güneşli küçük bahçe, nemli toprak ve ahşap çocuk bahçe araçları"
    },
    "TR008": {
        "hero": "İki sabit arkadaş: Ece turkuaz üstlü ve kahverengi saçlı; Can mor üstlü ve turuncu saçlı. İkisi de yuvarlak yüzlü, iri koyu gözlü ve okul öncesi 3D oranlarında.",
        "companions": "ortada paylaşılan renkli meyve sepeti, uçurtma ve yumuşak bir top",
        "palette": "turkuaz, mor, meyve kırmızısı, portakal ve park yeşili",
        "setting": "sıcak güneşli, düzenli piknik alanı ve açık park"
    }
}


def character_bible_text(song_id: str, title: str) -> str:
    spec = CHARACTER_BIBLES.get(song_id, {
        "hero": "Hikâyeye özgü, tamamen özgün ve sevimli okul öncesi ana karakter.",
        "companions": "hikâyenin öğrenme hedefine uygun özgün yardımcı karakterler",
        "palette": "birbiriyle uyumlu, kolay ayırt edilen üç ila beş renk",
        "setting": "sade, sıcak ışıklı, güvenli çocuk ortamı"
    })
    return (
        f"# Karakter ve Görsel Tutarlılık Rehberi — {title} ({song_id})\\n\\n"
        f"## Ana karakter\\n{spec['hero']}\\n\\n"
        f"## Yardımcı karakterler ve nesneler\\n{spec['companions']}\\n\\n"
        f"## Renk paleti\\n{spec['palette']}\\n\\n"
        f"## Ortam\\n{spec['setting']}\\n\\n"
        "## Her sahnede sabit tutulacak kurallar\\n"
        "- Aynı ana karakter(ler)in yüzü, kafa-gövde oranı, renkleri, kıyafeti ve malzemeleri değişmesin.\\n"
        "- Stil: yüksek kaliteli, stilize 3D okul öncesi animasyon filmi; yuvarlak formlar, yumuşak sinematik ışık, temiz kompozisyon.\\n"
        "- Dikey 9:16 kadraj; ana karakter kadrajda açıkça görünür ve önemli nesneler kesilmez.\\n"
        "- Görselde yazı, altyazı, logo, filigran veya tanınmış çizgi film karakteri bulunmasın.\\n"
        "- Bir sahnede yalnızca hikâye için gerekli nesneler bulunsun; arka plan gereksiz ayrıntıyla dolmasın.\\n\\n"
        "Her sahne istemine aşağıdaki karakter kilidini aynen ekle. Mümkünse ilk sahnenin onaylı görselini sonraki sahnelerde referans olarak kullan; yalnızca metin tam tutarlılığı garanti etmez.\\n"
    )


def build_pack(storyboard: dict, output_dir: Path) -> list[Path]:
    song_id = str(storyboard.get("id") or "UNKNOWN")
    title = str(storyboard.get("title") or song_id)
    scenes = storyboard.get("scenes") or []
    if not scenes:
        raise ValueError(f"{song_id}: storyboard içinde sahne bulunamadı.")
    folder = output_dir / safe_name(song_id)
    folder.mkdir(parents=True, exist_ok=True)
    created = []
    bible = character_bible_text(song_id, title)
    path = folder / "character_bible.md"
    path.write_text(bible, encoding="utf-8")
    created.append(path)
    index = [
        f"# Görsel Üretim Paketi — {title}", "",
        f"- Şarkı: {song_id}", f"- Kadraj: {storyboard.get('aspect_ratio', '9:16')}",
        f"- Hedef kitle: {storyboard.get('target_audience', 'preschool')}",
        f"- Sahne sayısı: {len(scenes)}", "",
        "## Kullanım",
        "1. Her sahne istemi, karakter rehberindeki sabit karakter tarifini içerir.",
        "2. Mümkünse ilk sahnenin onaylı görselini sonraki sahnelerde referans olarak kullanın.",
        "3. Her sahne için tek bir dikey kare üretin; metin, logo ve filigran ekletmeyin.",
        "4. Onaylanan görselleri visuals/scene_XX.png adıyla kaydedin.",
        "5. Görsel aracının lisans ve kullanım koşullarını kontrol edin.",
        "",
        "Bu paket görsel üretmez; tutarlı karakter tasarımı için hazır istemler üretir.",
        "", "## Sahneler", ""
    ]
    spec = CHARACTER_BIBLES.get(song_id, CHARACTER_BIBLES["TR001"])
    character_lock = f" CHARACTER DESIGN LOCK — {spec['hero']} Companions: {spec['companions']}. Keep the exact same design, proportions, colors, clothing, face and materials in every scene."
    for idx, scene in enumerate(scenes, start=1):
        number = int(scene.get("scene", idx))
        filename = f"scene_{number:02d}_prompt.txt"
        prompt = str(scene.get("image_generation_prompt") or "").strip()
        if not prompt:
            raise ValueError(f"{song_id}: {number}. sahne için görsel istemi boş.")
        prompt = prompt + character_lock + " Vertical 9:16, premium stylized 3D preschool animation, soft cinematic lighting, clear composition. No text, subtitles, logos, watermarks or copyrighted characters."
        path = folder / filename
        path.write_text(prompt + "\\n", encoding="utf-8")
        created.append(path)
        index.extend([f"### Sahne {number:02d}",
                      f"- Zaman: {scene.get('start_seconds', '?')}–{scene.get('end_seconds', '?')} sn",
                      f"- Odak: {scene.get('visual_focus', 'belirtilmedi')}",
                      f"- Dosya: {filename}", ""])
    path = folder / "README.md"
    path.write_text("\\n".join(index) + "\\n", encoding="utf-8")
    created.append(path)
    return created

def main() -> int:
    parser = argparse.ArgumentParser(description="Storyboard sahnelerini görsel istem paketine dönüştür")
    parser.add_argument("--input-dir", default=str(ROOT / "output" / "storyboards"))
    parser.add_argument("--output-dir", default=str(ROOT / "output" / "visual-prompt-pack"))
    parser.add_argument("--song-id")
    args = parser.parse_args()
    files = sorted(Path(args.input_dir).glob("*_storyboard.json"))
    if args.song_id:
        files = [p for p in files if p.name.startswith(args.song_id + "_")]
    if not files:
        print("Storyboard bulunamadı. Önce Build storyboard drafts iş akışını çalıştırın.")
        return 1
    for file in files:
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
            created = build_pack(data, Path(args.output_dir))
            print(f"{data.get('id')}: {len(created)} dosya hazır")
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"HATA {file.name}: {exc}")
            return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
