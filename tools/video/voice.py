#!/usr/bin/env python3
"""Voice-over for the v3 demo video, made offline with Kokoro-82M (Apache-2.0).

    pip install kokoro-onnx soundfile
    # model.onnx and voices/<voice>.bin from huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX,
    # packed into voices.npz (see pack_voices below), in the folder named by KOKORO_DIR
    KOKORO_DIR=/path/to/kokoro python3 voice.py [voice]     # default af_heart
    python3 render2.py data.json --durations build3/durations.json --audio build3/narration.wav

Writes one clip per scene, the scene durations needed so each line fits its
scene, and one narration track that starts each line just after its scene
fades in.
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
OUT = HERE / "build3"
LEAD, TAIL = 0.45, 0.6  # seconds of silence before and after each line within its scene

# Base durations from render2.py; a scene grows if its line needs more time.
BASE = [("title", 4.0), ("problem", 4.5), ("report", 5.0), ("validators", 6.0), ("gauge", 4.5), ("cure", 6.0),
        ("outcomes", 7.0), ("networks", 6.0), ("site", 6.0), ("end", 3.5)]
LINES = {
    "title": "Private credit is an estimated three trillion dollar market.",
    "problem": "Yet covenant checks still mean someone retyping a borrower's figures by hand, every quarter.",
    "report": "With Private Credit Gate, the borrower publishes its compliance figures on a web page.",
    "validators": "Gen Layer validators each read that page and copy four figures. A reading is stored only when a majority agree, exactly.",
    "gauge": "Then plain code tests the covenant. Leverage of three point seven five times breaks the limit.",
    "cure": "The borrower sends the equity cure quoted on chain. Principal is prepaid, and the breach is cured.",
    "outcomes": "Margins, defaults, acceleration and waivers all follow written rules, on fixed dates.",
    "networks": "Five fictional borrowers ran end to end, on Gen Layer Studio and the Bradbury testnet. One hundred and twenty nine live transactions, with identical readings.",
    "site": "Every reading and transaction is on the site, and anyone can run their own facility on Studio.",
    "end": "Private Credit Gate. Covenant gated credit, on Gen Layer.",
}


def pack_voices(folder, names):
    """Pack raw voices/<name>.bin files (float32, 510x1x256) into voices.npz for kokoro-onnx."""
    np.savez(Path(folder) / "voices.npz", **{n: np.fromfile(Path(folder) / f"{n}.bin", dtype=np.float32).reshape(-1, 1, 256) for n in names})


def main():
    from kokoro_onnx import Kokoro
    kdir = Path(os.environ["KOKORO_DIR"])
    voice = sys.argv[1] if len(sys.argv) > 1 else "af_heart"
    lang = "en-gb" if voice.startswith("b") else "en-us"
    k = Kokoro(str(kdir / "model.onnx"), str(kdir / "voices.npz"))
    (OUT / "voice").mkdir(parents=True, exist_ok=True)
    clips, durs, sr = {}, {}, 24000
    for name, base in BASE:
        samples, sr = k.create(LINES[name], voice=voice, speed=1.0, lang=lang)
        samples = np.asarray(samples, dtype=np.float32)
        sf.write(OUT / "voice" / f"{name}.wav", samples, sr)
        clips[name] = samples
        durs[name] = round(max(base, LEAD + len(samples) / sr + TAIL), 2)
        print(f"{name:11s} line {len(samples) / sr:5.2f} s  scene {durs[name]:5.2f} s")
    total = sum(durs.values())
    track = np.zeros(int(total * sr) + sr, dtype=np.float32)
    t = 0.0
    for name, _ in BASE:
        i = int((t + LEAD) * sr)
        track[i:i + len(clips[name])] += clips[name]
        t += durs[name]
    peak = float(np.max(np.abs(track))) or 1.0
    track = track * (0.89 / peak)
    sf.write(OUT / "narration.wav", track[: int(total * sr)], sr)
    (OUT / "durations.json").write_text(json.dumps(durs, indent=1))
    print(f"total {total:.2f} s, voice {voice}")


if __name__ == "__main__":
    main()
