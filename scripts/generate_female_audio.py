import json
import re
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
OUT = ROOT / "audio" / "female"
VOICE = "bf_emma"
SPEED = 0.92
SAMPLE_RATE = 24000

html = INDEX.read_text(encoding="utf-8")
m = re.search(r"const AUDIO_CUES\s*=\s*(\{.*?\});\s*const", html, re.S)
if not m:
    raise RuntimeError("AUDIO_CUES not found in index.html")

cues = json.loads(m.group(1))
words = list(cues.keys())

OUT.mkdir(parents=True, exist_ok=True)
pipeline = KPipeline(lang_code="b")

manifest = {}

for i, text in enumerate(words):
    filename = f"{i:03d}.wav"
    path = OUT / filename

    chunks = []
    generator = pipeline(text, voice=VOICE, speed=SPEED)
    for _, _, audio in generator:
        chunks.append(np.asarray(audio, dtype=np.float32))

    if not chunks:
        raise RuntimeError(f"No audio generated for: {text!r}")

    combined = np.concatenate(chunks)
    sf.write(path, combined, SAMPLE_RATE, subtype="PCM_16")
    manifest[text] = f"audio/female/{filename}"
    print(f"{i+1}/{len(words)} {text} -> {filename}")

(OUT / "manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print(f"Generated {len(words)} files with voice {VOICE}")
