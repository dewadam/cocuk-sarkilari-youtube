#!/usr/bin/env python3
"""Render a song by matching lyric lines to approved 30-second animation-library clips."""
from __future__ import annotations
import argparse, hashlib, json, re, shutil, subprocess, sys, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"app"))
from animation_catalog import DEFAULT_CATALOG, load_catalog, score_clip

def run(cmd,capture=False):
    p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=capture)
    if p.returncode: raise RuntimeError(f"Command failed: {' '.join(cmd[:7])}\n{(p.stderr or p.stdout or '')[-3000:]}")
    return p.stdout.strip() if capture else ""
def duration(p):
    return float(run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(p)],True))
def song_folder(sid):
    m=sorted(p for p in (ROOT/"songs").glob(sid.upper()+"_*") if p.is_dir())
    if len(m)!=1: raise RuntimeError(f"Expected one songs/{sid}_* folder; found {len(m)}")
    return m[0]
def choose_playlist(lyrics,catalog,target):
    clips=[c for c in catalog["clips"] if c.get("approved",False) and str(c.get("asset_url","")).startswith("https://") and 20<=float(c.get("duration_seconds",0))<=40]
    if not clips: raise RuntimeError("No approved 20-40s HTTPS clips in animation_library/catalog.json")
    lines=[x.strip() for x in lyrics.splitlines() if x.strip() and not x.strip().startswith(("[", "#", "("))]
    lines=[x for x in lines if len(x.split())>=2]
    matched=[]
    for line in lines:
        ranked=[(score_clip(c,line)[0],c) for c in clips]
        ranked=[x for x in ranked if x[0]>0]
        ranked.sort(key=lambda x:(-x[0],x[1].get("clip_id","")))
        if ranked and (not matched or matched[-1]["clip_id"]!=ranked[0][1]["clip_id"]): matched.append(ranked[0][1])
    if not matched:
        ranked=[(score_clip(c,lyrics)[0],c) for c in clips]
        ranked=[x for x in ranked if x[0]>0]
        ranked.sort(key=lambda x:(-x[0],x[1].get("clip_id","")))
        matched=[c for _,c in ranked[:10]]
    if not matched: raise RuntimeError("No keyword match found. Add Turkish tags/keywords; random fallback is disabled.")
    playlist=[]; total=0
    while total<target and len(playlist)<200:
        c=matched[len(playlist)%len(matched)]; playlist.append(c); total+=30
    return playlist
def main():
    p=argparse.ArgumentParser(); p.add_argument("--song-id",required=True); p.add_argument("--output"); p.add_argument("--catalog",type=Path,default=DEFAULT_CATALOG); p.add_argument("--preview-only",action="store_true",help="Allow visual-only preview before lyrics/audio verification; never authorizes YouTube publishing."); a=p.parse_args()
    sid=a.song_id.upper(); folder=song_folder(sid); meta_path=folder/"metadata.json"; meta=json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("status")!="ready":
        if not (a.preview_only and meta.get("status")=="audio_uploaded_lyrics_check"):
            raise RuntimeError("YouTube publishing requires metadata status=ready. Use --preview-only only for a non-publishing visual preview while lyrics/audio are being checked.")
        print("PREVIEW_ONLY: lyrics/audio verification is pending; this render must not be published.")
    if meta.get("usage_status","available")!="available" or meta.get("used_in_video_id"): raise RuntimeError("Song already used/unavailable.")
    audio=folder/str(meta.get("audio_file","song.mp3")); lyrics=folder/str(meta.get("lyrics_file","lyrics.txt"))
    if not audio.is_file() or not lyrics.is_file(): raise RuntimeError("Song MP3 or lyrics.txt missing.")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"): raise RuntimeError("FFmpeg/ffprobe missing.")
    target=duration(audio); playlist=choose_playlist(lyrics.read_text(encoding="utf-8"),load_catalog(a.catalog),target)
    work=ROOT/"output"/(sid+"_animation_work"); work.mkdir(parents=True,exist_ok=True); sources={}
    for c in playlist:
        cid=c["clip_id"]
        if cid in sources: continue
        dest=work/(cid+".mp4")
        req=urllib.request.Request(c["asset_url"],headers={"User-Agent":"PufiKids/1.0"})
        with urllib.request.urlopen(req,timeout=180) as r, dest.open("wb") as f: f.write(r.read())
        if dest.stat().st_size<100_000: raise RuntimeError("Downloaded clip is too small: "+cid)
        sources[cid]=dest
    segments=[]
    for i,c in enumerate(playlist):
        src=sources[c["clip_id"]]; out=work/f"segment_{i:03d}.mp4"
        loop=["-stream_loop","-1"] if duration(src)<30 else []
        run(["ffmpeg","-y","-hide_banner","-loglevel","error",*loop,"-i",str(src),"-t","30","-vf","scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,format=yuv420p","-an","-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p",str(out)])
        segments.append(out)
    listing=work/"concat.txt"; listing.write_text("".join(f"file '{x.as_posix()}'\n" for x in segments),encoding="utf-8")
    joined=work/"joined.mp4"; run(["ffmpeg","-y","-hide_banner","-loglevel","error","-f","concat","-safe","0","-i",str(listing),"-c","copy",str(joined)])
    output=Path(a.output) if a.output else ROOT/"output"/(sid+"_final.mp4"); output.parent.mkdir(parents=True,exist_ok=True)
    run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(joined),"-i",str(audio),"-map","0:v:0","-map","1:a:0","-t",f"{target:.3f}","-vf","scale=1080:1920,fps=30,format=yuv420p","-c:v","libx264","-preset","veryfast","-crf","20","-c:a","aac","-b:a","192k","-shortest","-movflags","+faststart",str(output)])
    report={"song_id":sid,"title":meta.get("title"),"audio_duration_seconds":round(target,3),"clip_uses":[{"clip_id":c["clip_id"],"keywords":c.get("keywords",[]),"asset_url":c["asset_url"]} for c in playlist],"unique_clips":len(sources),"video":str(output.relative_to(ROOT)),"video_sha256":hashlib.sha256(output.read_bytes()).hexdigest(),"matching":"lyric-line keyword matching; no random fallback"}
    (ROOT/"output"/(sid+"_animation-match-report.json")).write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__":
    try: main()
    except Exception as e: print("ANIMATION_LIBRARY_RENDER_FAILED:",e,file=sys.stderr); raise SystemExit(1)
