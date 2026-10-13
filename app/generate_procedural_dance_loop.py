#!/usr/bin/env python3
"""Create a song-specific, seamless, procedurally animated farm-dance loop.

No paid video API, model quota, or local GPU is required. Pillow draws each frame;
FFmpeg encodes a 10-second cyclic animation that the renderer repeats to song length.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
W, H, FPS, LOOP_SECONDS = 720, 1280, 30, 10


def song_folder(song_id: str) -> Path:
    matches = sorted(p for p in (ROOT / "songs").glob(f"{song_id}_*") if p.is_dir())
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one folder for {song_id}; found {len(matches)}")
    return matches[0]


def draw_animal(draw: ImageDraw.ImageDraw, x: float, y: float, scale: float,
                kind: str, phase: float, palette: tuple[str, str]) -> None:
    # All animation offsets are periodic so frame 0 and frame N are identical.
    bob = 12 * math.sin(phase)
    leg = 14 * math.sin(phase + math.pi / 2)
    x, y = int(x), int(y + bob)
    s = scale
    outline = "#4b4b55"
    body, accent = palette
    # feet / legs
    for lx in (-22, 22):
        xx = int(x + lx*s)
        draw.line((xx, y+62*s, xx+int(leg*s), y+91*s), fill=outline, width=max(3,int(5*s)))
        draw.ellipse((xx+int(leg*s)-7*s, y+85*s, xx+int(leg*s)+9*s, y+94*s), fill=accent)
    # body
    draw.ellipse((x-52*s, y+16*s, x+52*s, y+76*s), fill=body, outline=outline, width=max(2,int(3*s)))
    # ears
    if kind in ("cow", "lamb"):
        draw.ellipse((x-47*s,y-16*s,x-20*s,y+18*s), fill=accent, outline=outline, width=max(2,int(2*s)))
        draw.ellipse((x+20*s,y-16*s,x+47*s,y+18*s), fill=accent, outline=outline, width=max(2,int(2*s)))
    elif kind == "duck":
        draw.polygon([(x-25*s,y+2*s),(x-47*s,y-12*s),(x-36*s,y+18*s)], fill=accent, outline=outline)
    else:
        draw.polygon([(x-24*s,y-20*s),(x-12*s,y-38*s),(x-4*s,y-18*s),
                      (x+7*s,y-40*s),(x+15*s,y-16*s),(x+27*s,y-26*s),(x+27*s,y+1*s)], fill="#e85d4a", outline=outline)
    # head and muzzle
    draw.ellipse((x-37*s,y-36*s,x+37*s,y+30*s), fill=body, outline=outline, width=max(2,int(3*s)))
    if kind == "cow":
        draw.ellipse((x-27*s,y-13*s,x-12*s,y+3*s), fill="#4b4b55")
        draw.ellipse((x+12*s,y-20*s,x+27*s,y-6*s), fill="#4b4b55")
    if kind == "lamb":
        for ox,oy in [(-22,-28),(0,-34),(22,-28),(-31,-8),(31,-8)]:
            draw.ellipse((x+(ox-9)*s,y+(oy-9)*s,x+(ox+9)*s,y+(oy+9)*s), fill="#fff4dc", outline=outline, width=max(1,int(s)))
    if kind == "duck":
        draw.ellipse((x-27*s,y-5*s,x+27*s,y+20*s), fill="#ffcf66", outline=outline, width=max(1,int(2*s)))
        draw.polygon([(x+21*s,y-1*s),(x+48*s,y+7*s),(x+22*s,y+13*s)], fill="#ef9145", outline=outline)
    else:
        draw.ellipse((x-24*s,y+2*s,x+24*s,y+22*s), fill=accent, outline=outline, width=max(1,int(2*s)))
    # eyes
    for ex in (-13, 13):
        draw.ellipse((x+(ex-4)*s,y-14*s,x+(ex+4)*s,y-3*s), fill="#292a35")
        draw.ellipse((x+(ex-2)*s,y-13*s,x+(ex+1)*s,y-10*s), fill="white")
    draw.arc((x-10*s,y+1*s,x+10*s,y+14*s), 5, 175, fill=outline, width=max(1,int(2*s)))


def make_frame(song_id: str, frame_index: int, total: int) -> Image.Image:
    im = Image.new("RGB", (W, H), "#9bdcf7")
    d = ImageDraw.Draw(im)
    phase = 2 * math.pi * frame_index / total
    # sunny sky, clouds, distant hills and farm grass
    d.ellipse((530,70,630,170), fill="#ffe27a")
    for cx, cy in [(100,150),(330,100),(560,240)]:
        d.ellipse((cx,cy,cx+95,cy+35), fill="#f8ffff")
        d.ellipse((cx+20,cy-20,cx+65,cy+30), fill="#f8ffff")
    d.ellipse((-120,430,390,760), fill="#77c987")
    d.ellipse((300,400,850,770), fill="#55b878")
    d.rectangle((0,610,W,H), fill="#7ed16f")
    # pond
    d.ellipse((440,690,680,790), fill="#58c9e8", outline="#ffffff", width=5)
    # barn
    d.rectangle((45,435,215,600), fill="#e96c65", outline="#ffffff", width=5)
    d.polygon([(25,440),(130,350),(235,440)], fill="#b94b4c", outline="#ffffff")
    d.rectangle((98,500,163,600), fill="#f4d6a1", outline="#ffffff", width=4)
    # song-specific seed affects the accent flowers while keeping the loop repeatable
    seed = int(hashlib.sha256(song_id.encode()).hexdigest()[:8], 16)
    for i in range(18):
        fx = 20 + ((i*97 + seed % 83) % 680)
        fy = 815 + ((i*31 + seed % 29) % 350)
        d.line((fx,fy,fx-4,fy+18), fill="#399b58", width=3)
        d.ellipse((fx-7,fy-5,fx+7,fy+9), fill=["#fff0a6","#ff9dc3","#ffffff"][i%3])
    # Four dancing friends: evenly spaced, their movement is exactly periodic.
    animals = [
        (150, 700 + 8*math.sin(phase), 1.05, "cow", phase, ("#fff8ee","#d9a5a1")),
        (305, 750 + 8*math.sin(phase+1.2), .88, "lamb", phase+1.2, ("#f4e6c9","#fff4dc")),
        (460, 715 + 8*math.sin(phase+2.4), .86, "duck", phase+2.4, ("#ffd84f","#ef9145")),
        (595, 750 + 8*math.sin(phase+3.2), .76, "rooster", phase+3.2, ("#e5a34e","#d94b43")),
    ]
    for x,y,s,k,p,pal in animals:
        draw_animal(d,x,y,s,k,p,pal)
    # Decorative music notes bob on the same cycle; no text is rendered.
    for j, (nx,ny) in enumerate([(270,560),(390,520),(530,580)]):
        yy = ny + 10*math.sin(phase+j)
        d.ellipse((nx,yy,nx+15,yy+11), fill="#8d64d9")
        d.line((nx+13,yy+5,nx+13,yy-27), fill="#8d64d9", width=5)
        d.line((nx+13,yy-27,nx+28,yy-20), fill="#8d64d9", width=5)
    return im


def main() -> int:
    song_id = os.environ.get("SONG_ID", "TR002").strip()
    folder = song_folder(song_id)
    metadata = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
    audio = folder / str(metadata.get("audio_file", "song.mp3"))
    if not audio.is_file():
        raise RuntimeError(f"Missing audio: {audio}")
    out_dir = folder / "visuals"
    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / "dance_loop.mp4"
    manifest_path = out_dir / "dance_loop_manifest.json"
    manifest = {
        "song_id": song_id, "engine": "procedural_pillow_ffmpeg",
        "duration_seconds": LOOP_SECONDS, "width": W, "height": H,
        "fps": FPS, "seamless_cycle": True,
        "status": "rendering",
        "note": "Original song-seeded farm animation; no Sora or FLUX API required."
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    total = FPS * LOOP_SECONDS
    with __import__("tempfile").TemporaryDirectory(prefix="kids-dance-") as td:
        frames = Path(td)
        for i in range(total):
            make_frame(song_id, i, total).save(frames / f"frame_{i:04d}.png", optimize=True)
        cmd = [
            "ffmpeg","-y","-hide_banner","-loglevel","error",
            "-framerate",str(FPS),"-i",str(frames/"frame_%04d.png"),
            "-vf","scale=720:1280,fps=30,format=yuv420p",
            "-c:v","libx264","-preset","veryfast","-crf","21",
            "-pix_fmt","yuv420p","-an","-t",str(LOOP_SECONDS),
            "-movflags","+faststart",str(output)
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode:
            raise RuntimeError("FFmpeg failed: "+(proc.stderr or "")[-3000:])
    manifest.update({"status":"generated","output":str(output.relative_to(ROOT)),
                     "size_bytes":output.stat().st_size,"frame_count":total})
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
