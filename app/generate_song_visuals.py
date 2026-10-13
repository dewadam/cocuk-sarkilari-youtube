#!/usr/bin/env python3
"""Generate storyboard-driven song visuals with Azure FLUX. No automatic retries."""
from __future__ import annotations
import base64, json, os, re, sys, urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SONG_ID = os.environ.get("SONG_ID", "TR001").strip().upper()
ENDPOINT = os.environ.get("AZURE_ENDPOINT", "").strip().rstrip("/")
KEY = os.environ.get("AZURE_API_KEY", "").strip()
MODEL = os.environ.get("AZURE_IMAGE_MODEL", "FLUX.2-pro").strip() or "FLUX.2-pro"
MAX_SCENES = int(os.environ.get("MAX_SCENES", "6"))
SIZE = os.environ.get("AZURE_IMAGE_SIZE", "1024x1536").strip()
BASE = ("Premium polished stylized 3D preschool animated feature-film frame, "
        "soft cinematic global illumination, appealing rounded shapes, detailed materials, "
        "clear focal point, uncluttered composition, portrait 2:3 composition intended for a 9:16 video. "
        "No text, letters, captions, logo or watermark. Original characters only.")

def find_image(value):
    if isinstance(value, dict):
        for k in ("b64_json", "image_base64", "base64", "image"):
            v=value.get(k)
            if isinstance(v,str) and v: return ("base64",v)
        for k in ("url","sample","image_url"):
            v=value.get(k)
            if isinstance(v,str) and v.startswith(("https://","http://")): return ("url",v)
        for v in value.values():
            found=find_image(v)
            if found: return found
    elif isinstance(value,list):
        for v in value:
            found=find_image(v)
            if found: return found
    return None

def main():
    if not ENDPOINT or not KEY:
        raise RuntimeError("AZURE_ENDPOINT / AZURE_API_KEY missing; no request was sent.")
    if MAX_SCENES < 6 or MAX_SCENES > 8:
        raise RuntimeError("MAX_SCENES must be between 6 and 8.")
    match=re.fullmatch(r"(\\d{3,4})x(\\d{3,4})",SIZE)
    if not match or int(match.group(1))*int(match.group(2))>4_000_000:
        raise RuntimeError("AZURE_IMAGE_SIZE invalid or above 4 megapixels.")
    story_path=ROOT/"output"/"storyboards"/f"{SONG_ID}_storyboard.json"
    if not story_path.is_file(): raise RuntimeError(f"Storyboard missing: {story_path}")
    story=json.loads(story_path.read_text(encoding="utf-8"))
    scenes=story.get("scenes",[])[:MAX_SCENES]
    if len(scenes)<6: raise RuntimeError("Storyboard must contain at least 6 scenes.")
    folder_matches=sorted((ROOT/"songs").glob(f"{SONG_ID}_*"))
    if len(folder_matches)!=1: raise RuntimeError(f"Expected one song folder for {SONG_ID}; found {len(folder_matches)}.")
    visuals=folder_matches[0]/"visuals"
    visuals.mkdir(parents=True,exist_ok=True)
    # Never overwrite existing scene images: protects prior paid output from accidental replacement.
    for i in range(1,len(scenes)+1):
        if any((visuals/f"scene_{i:02d}{ext}").exists() for ext in (".jpg",".jpeg",".png",".webp")):
            raise RuntimeError(f"Existing scene_{i:02d} image found. Refusing to overwrite or charge again.")
    url=ENDPOINT+"/providers/blackforestlabs/v1/flux-2-pro?api-version=preview"
    bible={
      "TR001":"Main character Pofuduk: tiny turquoise garden friend, large oval head, small round body, coral-pink cheeks, large dark eyes, short arms, small pink balloon-knot tuft. Companions: friendly red and yellow balloons. Palette turquoise, leaf green, sunny yellow, coral pink. Flower-filled preschool garden.",
      "TR002":"Main character Ponçik: tiny cream lamb with curly wool tuft, short pink inner ears, small brown hooves, round cheeks, large dark eyes. Friendly cow, duck and rooster. Sunny clean farmyard.",
      "TR003":"Main character Pırıl: cute pearl-white tooth character, rounded crown, two short roots, pink cheeks, large dark eyes. Child toothbrush and bubbles. Bright clean pastel bathroom.",
      "TR004":"Main character Çufçuf: shiny red toy train, blue cabin, short yellow chimney, large black wheels, cheerful face. Tidy warm playroom, blocks, teddy bear and books.",
      "TR005":"Main character Mino: small silver space robot, rounded helmet head, turquoise body, two yellow LED eyes, short antennas. Friendly rocket, purple ringed planet, colorful gentle space.",
      "TR006":"Three consistent shape characters: coral-pink circle, sunny-yellow rounded square, turquoise triangle, each with small dark eyes and a simple smile. Clean geometric dance stage.",
      "TR007":"Main character Ada: little gardener child, short brown hair, orange overalls, round face, large dark eyes. One red pot, soil, seedling and watering can in sunny garden.",
      "TR008":"Two consistent friends: Ece wears turquoise and has brown hair; Can wears purple and has orange hair. Round faces, large dark eyes. Picnic fruit basket, kite and soft ball in a sunny park."
    }.get(SONG_ID,"Original cute preschool characters matched to the storyboard.")
    manifest={"song_id":SONG_ID,"model":MODEL,"size":SIZE,"requested_images":len(scenes),"completed_images":0,"images":[]}
    manifest_path=ROOT/"output"/f"{SONG_ID}_visual-generation-manifest.json"
    manifest_path.parent.mkdir(parents=True,exist_ok=True)
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\\n",encoding="utf-8")
    for index,scene in enumerate(scenes,start=1):
        prompt=BASE+" SONG: "+str(story.get("title",SONG_ID))+". CHARACTER AND STYLE LOCK: "+bible+" Scene action: "+str(scene.get("action",""))+" Visual focus: "+str(scene.get("visual_focus",""))+" Camera: "+str(scene.get("camera_direction",""))+" Learning goal: "+str(story.get("learning_goal",""))+". Keep character face, proportions, colors and materials consistent across scenes. No text or typography."
        body=json.dumps({"model":MODEL,"prompt":prompt,"width":int(match.group(1)),"height":int(match.group(2)),"output_format":"jpeg","num_images":1}).encode()
        req=urllib.request.Request(url,data=body,method="POST",headers={"Authorization":"Bearer "+KEY,"Content-Type":"application/json","Accept":"application/json"})
        try:
            with urllib.request.urlopen(req,timeout=300) as response: payload=json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            detail=exc.read().decode("utf-8",errors="replace")[-2000:]
            manifest["last_error"]=f"HTTP {exc.code} at scene {index}: {detail}"
            manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\\n",encoding="utf-8")
            raise RuntimeError(f"Azure request failed at scene {index}/{len(scenes)} with HTTP {exc.code}. No retry sent.")
        except (TimeoutError, urllib.error.URLError) as exc:
            manifest["last_error"]=f"{type(exc).__name__} at scene {index}: {exc}; no retry sent"
            manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\\n",encoding="utf-8")
            raise RuntimeError(f"Azure request did not complete at scene {index}/{len(scenes)}. No automatic retry sent.")
        found=find_image(payload)
        if not found: raise RuntimeError("Azure response contained no recognizable image data.")
        kind,value=found
        if kind=="base64": data=base64.b64decode(value)
        else:
            with urllib.request.urlopen(urllib.request.Request(value,headers={"User-Agent":"kids-song-pipeline/1.0"}),timeout=120) as response: data=response.read()
        if data.startswith(b"\\xff\\xd8\\xff"): ext=".jpg"
        elif data.startswith(b"\\x89PNG\\r\\n\\x1a\\n"): ext=".png"
        else: raise RuntimeError(f"Scene {index} returned unknown image format.")
        target=visuals/f"scene_{index:02d}{ext}"
        target.write_bytes(data)
        manifest["images"].append({"file":str(target.relative_to(ROOT)),"bytes":len(data),"visual_focus":scene.get("visual_focus","")})
        manifest["completed_images"]=len(manifest["images"])
        manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\\n",encoding="utf-8")
        print(f"Generated {index}/{len(scenes)}: {target.relative_to(ROOT)} ({len(data)} bytes)",flush=True)
    print(f"Visual generation complete for {SONG_ID}: {len(scenes)} images.")

if __name__=="__main__":
    try: main()
    except Exception as exc:
        print(f"VISUAL_GENERATION_FAILED: {exc}",file=sys.stderr)
        raise
