import asyncio
import json
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
SOURCE_MANIFEST = ROOT / "audio" / "female" / "manifest.json"
OUT = ROOT / "audio" / "sonia"

VOICE = "en-GB-SoniaNeural"
RATE = "-22%"
VOLUME = "+0%"
PITCH = "+0Hz"

# Explicit pronunciation fixes for isolated dictionary words.
# The output file still belongs to the original visible word.
PRONUNCIATION_OVERRIDES = {
    "close": "cloze",      # verb: /kləʊz/, not adjective /kləʊs/
    "present": "prezzent", # noun: birthday present, /ˈprezənt/
}

async def synthesize(text: str, path: Path):
    communicate = edge_tts.Communicate(
        text,
        VOICE,
        rate=RATE,
        volume=VOLUME,
        pitch=PITCH,
    )
    await communicate.save(str(path))

async def main():
    source = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    words = list(source.keys())

    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {}

    for i, word in enumerate(words):
        filename = f"{i:03d}.mp3"
        path = OUT / filename
        spoken = PRONUNCIATION_OVERRIDES.get(word, word)

        await synthesize(spoken, path)
        manifest[word] = f"audio/sonia/{filename}"
        print(f"{i+1}/{len(words)} {word!r} -> {spoken!r} -> {filename}")

        # Gentle pacing to avoid hammering the online synthesis service.
        await asyncio.sleep(0.08)

    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Generated {len(words)} files with {VOICE} at rate {RATE}")

if __name__ == "__main__":
    asyncio.run(main())
