#!/usr/bin/env python3
"""Manage the reusable animation clip catalog."""
from __future__ import annotations
import argparse, json, re, sys, unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "animation_library" / "catalog.json"

def normalize(value: str) -> str:
    value = value.casefold().translate(str.maketrans({"ı":"i","İ":"i","ğ":"g","ü":"u","ş":"s","ö":"o","ç":"c"}))
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", value).strip()

def load_catalog(path=DEFAULT_CATALOG):
    if not path.exists():
        return {"schema_version":1,"description":"Reusable animation clip catalog","updated_at":None,"clips":[]}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("clips"), list):
        raise ValueError(f"Unsupported or invalid catalog schema: {path}")
    return data

def save_catalog(data, path=DEFAULT_CATALOG):
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def validate_clip(clip):
    errors = []
    for field in ("clip_id","file_name","category","tags","keywords","duration_seconds","loopable","asset_url"):
        if field not in clip: errors.append(f"missing {field}")
    if "clip_id" in clip and not re.fullmatch(r"[A-Z0-9][A-Z0-9_-]{2,63}", str(clip["clip_id"])):
        errors.append("clip_id must contain 3-64 uppercase letters, digits, underscores or hyphens")
    if "file_name" in clip and not str(clip["file_name"]).lower().endswith(".mp4"):
        errors.append("file_name must end with .mp4")
    if "duration_seconds" in clip:
        try:
            if float(clip["duration_seconds"]) <= 0: errors.append("duration_seconds must be positive")
        except (TypeError, ValueError): errors.append("duration_seconds must be numeric")
    if not isinstance(clip.get("tags", []), list): errors.append("tags must be a list")
    if not isinstance(clip.get("keywords", []), list): errors.append("keywords must be a list")
    if clip.get("asset_url") and not str(clip["asset_url"]).startswith(("https://","http://")):
        errors.append("asset_url must be an HTTP(S) URL")
    return errors

def score_clip(clip, query):
    query_norm = normalize(query); query_terms = set(query_norm.split()); matched = []; score = 0
    fields = {"tags":clip.get("tags",[]),"keywords":clip.get("keywords",[]),"category":[clip.get("category","")],"character":clip.get("characters",[]),"action":clip.get("actions",[]),"environment":clip.get("environments",[]),"mood":clip.get("moods",[])}
    weights = {"keywords":5,"tags":4,"action":4,"character":3,"category":2,"environment":2,"mood":1}
    for field, values in fields.items():
        for value in values:
            norm = normalize(str(value))
            if not norm: continue
            words = set(norm.split()); overlap = query_terms & words
            if norm in query_norm or (words and words.issubset(query_terms)):
                score += weights.get(field,1) + len(overlap); matched.append(str(value))
            elif overlap:
                score += weights.get(field,1) * len(overlap); matched.extend(sorted(overlap))
    return score, sorted(set(matched))

def command_validate(args):
    data = load_catalog(args.catalog); seen = set(); problems = []
    for index, clip in enumerate(data["clips"]):
        for error in validate_clip(clip): problems.append(f"clips[{index}] {clip.get('clip_id','?')}: {error}")
        clip_id = clip.get("clip_id")
        if clip_id in seen: problems.append(f"duplicate clip_id: {clip_id}")
        seen.add(clip_id)
    if problems: print("\n".join(problems), file=sys.stderr); return 1
    print(f"Catalog OK: {len(data['clips'])} clips"); return 0

def command_search(args):
    data = load_catalog(args.catalog); results = []
    for clip in data["clips"]:
        if args.loopable_only and not clip.get("loopable",False): continue
        score, matches = score_clip(clip,args.query)
        if score > 0: results.append((score,clip,matches))
    results.sort(key=lambda row:(-row[0],row[1].get("clip_id",""))); results = results[:args.limit]
    if args.json: print(json.dumps([{"score":s,"matched":m,**c} for s,c,m in results],ensure_ascii=False,indent=2))
    elif not results: print("Eşleşen klip bulunamadı.")
    else:
        for score,clip,matches in results:
            print(f"{clip.get('clip_id')} | skor={score} | {clip.get('file_name')} | {', '.join(matches)}")
            print(f"  {clip.get('asset_url','')}")
    return 0

def command_add(args):
    data = load_catalog(args.catalog); clip = json.loads(Path(args.metadata).read_text(encoding="utf-8"))
    if not isinstance(clip,dict): raise ValueError("Metadata JSON must be an object")
    errors = validate_clip(clip)
    if errors: raise ValueError("Invalid clip metadata: " + "; ".join(errors))
    existing = {item.get("clip_id"):i for i,item in enumerate(data["clips"])}
    if clip["clip_id"] in existing:
        if not args.replace: raise ValueError(f"{clip['clip_id']} already exists; use --replace to update it")
        data["clips"][existing[clip["clip_id"]]] = clip
    else: data["clips"].append(clip)
    data["clips"].sort(key=lambda item:item["clip_id"]); save_catalog(data,args.catalog)
    print(f"Saved {clip['clip_id']}; total clips: {len(data['clips'])}"); return 0

def build_parser():
    parser = argparse.ArgumentParser(description="Search and validate the reusable animation catalog")
    parser.add_argument("--catalog",type=Path,default=DEFAULT_CATALOG)
    sub = parser.add_subparsers(dest="command",required=True)
    p = sub.add_parser("validate"); p.set_defaults(func=command_validate)
    p = sub.add_parser("search"); p.add_argument("query"); p.add_argument("--limit",type=int,default=10); p.add_argument("--loopable-only",action="store_true"); p.add_argument("--json",action="store_true"); p.set_defaults(func=command_search)
    p = sub.add_parser("add"); p.add_argument("metadata"); p.add_argument("--replace",action="store_true"); p.set_defaults(func=command_add)
    return parser

if __name__ == "__main__":
    args = build_parser().parse_args()
    try: raise SystemExit(args.func(args))
    except (OSError,ValueError,json.JSONDecodeError) as exc: print(f"ERROR: {exc}",file=sys.stderr); raise SystemExit(2)
