import json
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
marker = "const AUDIO_CUES = "
start = html.find(marker)
if start < 0:
    raise RuntimeError("AUDIO_CUES not found in index.html")

obj_start = html.find("{", start)
if obj_start < 0:
    raise RuntimeError("AUDIO_CUES object start not found")

depth = 0
in_string = False
escape = False
obj_end = None

for pos in range(obj_start, len(html)):
    ch = html[pos]
    if in_string:
        if escape:
            escape = False
        elif ch == "\\":
            escape = True
        elif ch == '"':
            in_string = False
        continue

    if ch == '"':
        in_string = True
    elif ch == "{":
        depth += 1
    elif ch == "}":
        depth -= 1
        if depth == 0:
            obj_end = pos + 1
            break

if obj_end is None:
    raise RuntimeError("AUDIO_CUES object end not found")

cues = json.loads(html[obj_start:obj_end])
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
