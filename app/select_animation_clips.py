#!/usr/bin/env python3
"""Select reusable animation clips from song lyrics using catalog metadata."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from animation_catalog import DEFAULT_CATALOG, load_catalog, score_clip

def main() -> int:
    p=argparse.ArgumentParser(description="Match lyrics to reusable animation clips")
    p.add_argument("--lyrics",type=Path,required=True); p.add_argument("--catalog",type=Path,default=DEFAULT_CATALOG); p.add_argument("--output",type=Path,required=True); p.add_argument("--limit",type=int,default=20); p.add_argument("--repeat-to-seconds",type=float,default=0); p.add_argument("--allow-non-loopable",action="store_true")
    a=p.parse_args(); lyrics=a.lyrics.read_text(encoding="utf-8"); catalog=load_catalog(a.catalog); ranked=[]
    for clip in catalog["clips"]:
        if not a.allow_non_loopable and not clip.get("loopable",False): continue
        if not clip.get("approved",True): continue
        score,matched=score_clip(clip,lyrics)
        if score>0: ranked.append((score,clip,matched))
    ranked.sort(key=lambda row:(-row[0],row[1].get("clip_id",""))); ranked=ranked[:max(1,a.limit)]
    if not ranked: ranked=[(0,c,[]) for c in catalog["clips"] if c.get("loopable",False) and c.get("approved",True)][:a.limit]
    if not ranked: print("No matching approved loopable clips found in catalog.",file=sys.stderr); return 2
    playlist=[]; total=0.0; i=0
    while i<1000 and (a.repeat_to_seconds<=0 or total<a.repeat_to_seconds):
        score,clip,matched=ranked[i%len(ranked)]; duration=float(clip.get("duration_seconds",30))
        playlist.append({"clip_id":clip["clip_id"],"asset_url":clip["asset_url"],"duration_seconds":duration,"score":score,"matched_terms":matched,"loopable":bool(clip.get("loopable",False))})
        total+=duration; i+=1
    if i>=1000: print("Reached playlist safety limit.",file=sys.stderr)
    result={"schema_version":1,"lyrics_file":str(a.lyrics),"target_duration_seconds":a.repeat_to_seconds or None,"planned_duration_seconds":round(total,3),"clips":playlist}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Playlist written: {a.output} ({len(playlist)} clip uses, {total:.1f}s)"); return 0
if __name__=="__main__": raise SystemExit(main())
