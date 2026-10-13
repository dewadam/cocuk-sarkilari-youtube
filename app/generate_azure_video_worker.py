#!/usr/bin/env python3
"""Submit a song-specific 3D animation request to an Azure GPU worker."""
from __future__ import annotations
import argparse, hashlib, json, os, time, urllib.error, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def api_request(url, token, method="GET", body=None, timeout=60):
    headers={"Authorization":f"Bearer {token}","Accept":"application/json"}; data=None
    if body is not None:
        headers["Content-Type"]="application/json"; data=json.dumps(body).encode("utf-8")
    req=urllib.request.Request(url,data=data,headers=headers,method=method)
    try:
        with urllib.request.urlopen(req,timeout=timeout) as response:
            raw=response.read(); ctype=response.headers.get("Content-Type","")
            return json.loads(raw.decode("utf-8")) if "json" in ctype else raw
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Azure GPU worker HTTP {exc.code}: {exc.read().decode(errors='replace')[-3000:]}") from exc

def song_folder(song_id):
    matches=sorted(p for p in (ROOT/"songs").glob(f"{song_id}_*") if p.is_dir())
    if len(matches)!=1: raise RuntimeError(f"Expected one song folder for {song_id}; found {len(matches)}")
    return matches[0]

def prompt_for(meta,lyrics):
    motifs=", ".join(str(x) for x in meta.get("visual_motifs",[]))
    lines=[line.strip() for line in lyrics.splitlines() if line.strip() and not line.strip().startswith(("#","["))]
    excerpt=" ".join(lines[:8])[:450]
    return ("High-quality stylized 3D animated preschool music-video, original polished feature-animation look. "
      f"Song theme: {meta.get('theme','preschool song')}. Story: {meta.get('core_idea','')}. Motifs: {motifs}. "
      f"Lyrics for visual inspiration only: {excerpt}. Portrait 9:16 composition, 704x1280 or closest supported. "
      "One continuous shot, no cuts, no text, subtitles, logos or watermark. Keep character identities, species, colors, "
      "proportions and environment stable across frames. Full-body characters fully visible, detailed 3D fur/feathers, "
      "soft cinematic lighting, colorful child-friendly palette. Cyclic group dance with rhythmic hops and side steps. "
      "Aim for a seamless loop: matching start/end pose, formation, positions and motion phase. No morphing, extra limbs, "
      "duplicates or sudden camera moves. Silent video; mix the original song audio separately.")

def main():
    p=argparse.ArgumentParser(description="Generate an AI 3D animation loop using Azure GPU worker")
    p.add_argument("--song-id",default=os.environ.get("SONG_ID","TR002")); p.add_argument("--seconds",type=int,default=5)
    p.add_argument("--poll-seconds",type=int,default=15); p.add_argument("--timeout-minutes",type=int,default=90)
    a=p.parse_args()
    base=os.environ.get("AZURE_VIDEO_WORKER_URL","").strip().rstrip("/")
    token=os.environ.get("AZURE_VIDEO_WORKER_TOKEN","").strip()
    model=os.environ.get("AZURE_VIDEO_MODEL","Wan2.2-TI2V-5B").strip()
    if not base or not token: raise RuntimeError("Set AZURE_VIDEO_WORKER_URL and AZURE_VIDEO_WORKER_TOKEN GitHub secrets.")
    folder=song_folder(a.song_id); meta=json.loads((folder/"metadata.json").read_text(encoding="utf-8"))
    lyrics_path=folder/str(meta.get("lyrics_file","lyrics.txt"))
    lyrics=lyrics_path.read_text(encoding="utf-8") if lyrics_path.is_file() else ""
    out_dir=folder/"visuals"; out_dir.mkdir(parents=True,exist_ok=True)
    output=out_dir/"dance_loop.mp4"; manifest_path=out_dir/"dance_loop_manifest.json"
    prompt=prompt_for(meta,lyrics)
    manifest={"song_id":a.song_id,"model":model,"status":"submitting","requested_seconds":a.seconds,
      "prompt":prompt,"lyrics_sha256":hashlib.sha256(lyrics.encode()).hexdigest()}
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    job=api_request(base+"/v1/jobs",token,"POST",{"model":model,"prompt":prompt,"duration_seconds":a.seconds,
      "width":704,"height":1280,"fps":16,"loop":True,"audio":False,"song_id":a.song_id,"output_format":"mp4"})
    job_id=job.get("job_id") or job.get("id")
    if not job_id: raise RuntimeError("Worker response missing job_id: "+str(job)[:1500])
    manifest.update({"job_id":job_id,"status":job.get("status","queued")})
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    deadline=time.time()+a.timeout_minutes*60; status=job.get("status","queued"); info=job
    while status not in ("succeeded","completed","failed","cancelled"):
        if time.time()>deadline:
            manifest.update({"status":"timeout","last_worker_status":status})
            manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            raise RuntimeError("Azure generation timed out; no duplicate job was submitted.")
        time.sleep(max(5,a.poll_seconds)); info=api_request(base+"/v1/jobs/"+str(job_id),token)
        status=info.get("status","unknown"); manifest["status"]=status
        manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(f"Azure video job {job_id}: {status}",flush=True)
    if status in ("failed","cancelled"): raise RuntimeError("Azure video generation failed: "+str(info.get("error") or status))
    url=info.get("result_url") or info.get("download_url") or base+"/v1/jobs/"+str(job_id)+"/result"
    if url.startswith("/"): url=base+url
    req=urllib.request.Request(url,headers={"Authorization":f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req,timeout=300) as response: data=response.read()
    except urllib.error.HTTPError as exc: raise RuntimeError(f"Video download HTTP {exc.code}: {exc.read().decode(errors='replace')[-2000:]}") from exc
    if len(data)<100_000: raise RuntimeError(f"Worker returned unexpectedly small video: {len(data)} bytes")
    output.write_bytes(data)
    manifest.update({"status":"downloaded","output":str(output.relative_to(ROOT)),"size_bytes":len(data),
      "result_sha256":hashlib.sha256(data).hexdigest()})
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(manifest,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
