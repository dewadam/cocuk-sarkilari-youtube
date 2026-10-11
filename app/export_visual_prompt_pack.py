"""Export storyboard JSON into a copy-ready visual prompt pack."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_") or "song"

def build_pack(storyboard: dict, output_dir: Path) -> list[Path]:
    song_id = str(storyboard.get("id") or "UNKNOWN")
    title = str(storyboard.get("title") or song_id)
    scenes = storyboard.get("scenes") or []
    if not scenes:
        raise ValueError(f"{song_id}: storyboard içinde sahne bulunamadı.")
    folder = output_dir / safe_name(song_id)
    folder.mkdir(parents=True, exist_ok=True)
    created = []
    bible = (
        f"# Karakter ve Görsel Tutarlılık Rehberi — {title}\n\n"
        "İlk görseli üretmeden önce bu rehberi doldurun. Henüz karakter tasarımı tanımlı değildir.\n\n"
        "- Ana karakter: tür/insan görünümü, yüz özellikleri\n"
        "- Saç/baş: şekil, renk, ayırt edici özellikler\n"
        "- Kıyafet: parçalar, renkler, aksesuarlar\n"
        "- Oranlar ve malzemeler: kafa-gövde oranı, doku, 3D stil\n"
        "- Yardımcı karakterler: görünüm ve ilişki\n"
        "- Sabit kurallar: ışık, kamera dili, render kalitesi\n\n"
        "Onaylanan karakter tarifini her sahne istemine ekleyin. Mümkünse aynı referans görseli her sahnede kullanın. "
        "Yalnızca metin kullanmak karakter tutarlılığını garanti etmez.\n"
    )
    path = folder / "character_bible.md"
    path.write_text(bible, encoding="utf-8")
    created.append(path)
    index = [
        f"# Görsel Üretim Paketi — {title}", "",
        f"- Şarkı: {song_id}", f"- Kadraj: {storyboard.get('aspect_ratio', '9:16')}",
        f"- Hedef kitle: {storyboard.get('target_audience', 'preschool')}",
        f"- Sahne sayısı: {len(scenes)}", "",
        "## Kullanım",
        "1. character_bible.md dosyasındaki karakter tarifini belirleyin.",
        "2. Her scene_XX_prompt.txt dosyasını karakter tarifiyle birleştirip görsel aracına verin.",
        "3. Her sahne için tek bir dikey kare üretin; metin, logo ve filigran ekletmeyin.",
        "4. Onaylanan görselleri visuals/scene_XX.png adıyla kaydedin.",
        "5. Görsel aracının lisans ve kullanım koşullarını kontrol edin.",
        "",
        "Bu paket görsel üretmez; kopyalanabilir istemleri düzenler. Referans görsel karakter sürekliliğini artırır.",
        "", "## Sahneler", ""
    ]
    for idx, scene in enumerate(scenes, start=1):
        number = int(scene.get("scene", idx))
        filename = f"scene_{number:02d}_prompt.txt"
        prompt = str(scene.get("image_generation_prompt") or "").strip()
        if not prompt:
            raise ValueError(f"{song_id}: {number}. sahne için görsel istemi boş.")
        path = folder / filename
        path.write_text(prompt + "\n", encoding="utf-8")
        created.append(path)
        index.extend([f"### Sahne {number:02d}",
                      f"- Zaman: {scene.get('start_seconds', '?')}–{scene.get('end_seconds', '?')} sn",
                      f"- Odak: {scene.get('visual_focus', 'belirtilmedi')}",
                      f"- Dosya: {filename}", ""])
    path = folder / "README.md"
    path.write_text("\n".join(index) + "\n", encoding="utf-8")
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
