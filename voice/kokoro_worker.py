"""Persistent Kokoro TTS worker subprocess.

Run inside the dedicated TTS virtualenv (``tts-venv``, Python 3.11+ where
Kokoro + spacy wheels exist). The model is loaded exactly once and kept in
memory, so the main backend never re-initializes TTS per sentence.

Protocol: JSON-lines over stdin/stdout.
  Request:  {"id": "...", "text": "...", "voice": "am_fenrir", "speed": 1.0, "out": "/tmp/x.wav"}
  Response: {"id": "...", "ok": true}
            {"id": "...", "ok": false, "error": "..."}

Control:
  {"cmd": "ping"} -> {"cmd": "ping", "ok": true}
  {"cmd": "shutdown"} -> exits 0

All logging goes to stderr so stdout stays a clean response channel.
"""

from __future__ import annotations

import json
import logging
import os
import sys

import numpy as np
import soundfile as sf

sys.stderr.write("[kokoro-worker] starting\n")
sys.stderr.flush()
logging.basicConfig(stream=sys.stderr, level=logging.WARNING)

# lang_code mapping derived from the Kokoro voice id prefix.
_LANG_BY_PREFIX = {
    "af": "a", "am": "a",
    "bf": "b", "bm": "b",
    "ef": "e", "em": "e",
    "ff": "f", "fm": "f",
    "hf": "h", "hm": "h",
    "jf": "j", "jm": "j",
}

_pipelines: dict[str, object] = {}


def _pipeline_for(voice: str):
    prefix = voice.split("_")[0] if "_" in voice else "af"
    lang = _LANG_BY_PREFIX.get(prefix, "a")
    if lang not in _pipelines:
        from kokoro import KPipeline

        repo_id = os.environ.get("KOKORO_MODEL_PATH") or "hexgrad/Kokoro-82M"
        _pipelines[lang] = KPipeline(lang_code=lang, repo_id=repo_id, model=True)
    return _pipelines[lang]


def render(text: str, voice: str, speed: float, out_path: str) -> None:
    pipeline = _pipeline_for(voice)
    gen = pipeline(text, voice=voice, speed=speed)
    chunks = []
    for _graphemes, _phonemes, audio in gen:
        if audio is None:
            continue
        chunks.append(np.asarray(audio, dtype="float32"))
    if not chunks:
        raise RuntimeError("Kokoro produced no audio.")
    merged = np.concatenate(chunks)
    sf.write(out_path, merged, 24000)


def main() -> int:
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        cmd = req.get("cmd")
        if cmd == "ping":
            sys.stdout.write(json.dumps({"cmd": "ping", "ok": True}) + "\n")
            sys.stdout.flush()
            continue
        if cmd == "shutdown":
            return 0
        job_id = req.get("id", "")
        try:
            render(req["text"], req.get("voice", "af_heart"), float(req.get("speed", 1.0)), req["out"])
            sys.stdout.write(json.dumps({"id": job_id, "ok": True}) + "\n")
        except Exception as exc:  # surface render errors to the caller
            sys.stderr.write(f"[kokoro-worker] render failed: {exc}\n")
            sys.stderr.flush()
            sys.stdout.write(json.dumps({"id": job_id, "ok": False, "error": str(exc)}) + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
