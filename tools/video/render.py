#!/usr/bin/env python3
"""Render the PrivateCreditGate demo video from stage.html.

Each scene is drawn frame by frame in headless Chromium; screenshots go
straight into ffmpeg as JPEG, one encoded file per scene, then the scenes are
joined with the concat demuxer and -c copy.

  python3 shot.py                       # site and report screenshots
  python3 render.py data.json           # privatecredit-demo.mp4 (1920x1080, 45 s)
  python3 render.py data.json --preview hook@3 cure@2.5   # stills to look at
"""
import json
import os
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
FPS = 30
SIZE = (1920, 1080)
OUT = "privatecredit-demo.mp4"
SCENES = [("hook", 4.5), ("report", 5.0), ("validators", 6.5), ("cure", 6.0), ("outcomes", 7.0),
          ("networks", 6.0), ("site", 6.5), ("end", 3.5)]


def encode_scene(page, name, dur, idx, total, outdir):
    n = round(dur * FPS)
    tmp = outdir / f"{idx:02d}_{name}.part.mp4"
    final = outdir / f"{idx:02d}_{name}.mp4"
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
         "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", str(FPS),
         "-movflags", "+faststart", str(tmp)],
        stdin=subprocess.PIPE)
    for f in range(n):
        page.evaluate("([n, t, d, a, b]) => draw(n, t, d, a, b)", [name, f / FPS, dur, idx > 0, idx < total - 1])
        ff.stdin.write(page.locator("#s").screenshot(type="jpeg", quality=92))
    ff.stdin.close()
    if ff.wait() != 0:
        raise SystemExit(f"ffmpeg failed on {name}")
    os.replace(tmp, final)
    return final


def main():
    data = json.loads(Path(sys.argv[1]).read_text())
    w, h = SIZE
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
        page.goto((HERE / "stage.html").as_uri())
        page.evaluate("document.fonts.ready")
        page.evaluate("([w, h, d]) => setup(w, h, d)", [w, h, data])
        if "--preview" in sys.argv:
            for spec in sys.argv[sys.argv.index("--preview") + 1:]:
                name, t = spec.split("@")
                dur = dict(SCENES)[name]
                page.evaluate("([n, t, d]) => draw(n, t, d, false, false)", [name, float(t), dur])
                page.wait_for_timeout(100)
                page.locator("#s").screenshot(path=str(HERE / f"pv_{name}_{t}.jpg"), type="jpeg", quality=85)
            b.close()
            return
        outdir = HERE / "build"
        outdir.mkdir(exist_ok=True)
        files = [encode_scene(page, name, dur, i, len(SCENES), outdir) for i, (name, dur) in enumerate(SCENES)]
        b.close()
    lst = outdir / "list.txt"
    lst.write_text("".join(f"file '{f.name}'\n" for f in files))
    tmp = HERE / (OUT[:-4] + ".part.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
                    "-movflags", "+faststart", str(tmp)], check=True)
    os.replace(tmp, HERE / OUT)
    print(OUT)


if __name__ == "__main__":
    main()
