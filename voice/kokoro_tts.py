import asyncio
import contextlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from config.settings import get_settings

KOKORO_VOICES = [
    "af_heart", "af_bella", "af_nicole", "af_aoede", "af_kore", "af_sarah",
    "am_fenrir", "am_puck", "am_echo", "am_liam", "bm_george", "bm_fable",
    "bf_emma", "bf_isabella", "ef_dora", "em_alex", "em_santa", "ff_siwis",
    "hf_alpha", "hm_bb", "hm_omega", "jf_alpha", "jm_kumo",
]

# Human-readable catalog for the premium voice picker.
KOKORO_VOICE_META = {
    "af_heart": "Amelia Heart", "af_bella": "Bella", "af_nicole": "Nicole",
    "af_aoede": "Aoede", "af_kore": "Kore", "af_sarah": "Sarah",
    "am_fenrir": "Fenrir", "am_puck": "Puck", "am_echo": "Echo", "am_liam": "Liam",
    "bm_george": "George", "bm_fable": "Fable",
    "bf_emma": "Emma", "bf_isabella": "Isabella",
    "ef_dora": "Dora", "em_alex": "Alex", "em_santa": "Santa",
    "ff_siwis": "Siwis",
    "hf_alpha": "Alpha", "hm_bb": "BB", "hm_omega": "Omega",
    "jf_alpha": "Alpha", "jm_kumo": "Kumo",
}


def _voice_group(voice_id: str) -> str:
    prefix = voice_id.split("_")[0] if "_" in voice_id else "uk"
    groups = {
        "af": "American (Female)", "am": "American (Male)",
        "bf": "British (Female)", "bm": "British (Male)",
        "ef": "Spanish (Female)", "em": "Spanish (Male)",
        "ff": "French (Female)", "fm": "French (Male)",
        "hf": "Hindi (Female)", "hm": "Hindi (Male)",
        "jf": "Japanese (Female)", "jm": "Japanese (Male)",
    }
    return groups.get(prefix, "Other")


def _voice_gender(voice_id: str) -> str:
    """Return 'male' or 'female' for a Kokoro voice id (e.g. 'am_fenrir')."""
    prefix = voice_id.split("_")[0] if "_" in voice_id else ""
    if len(prefix) >= 2:
        return "female" if prefix[1] == "f" else "male"
    return "unknown"


def _lang_for_voice(voice_id: str) -> str:
    prefix = voice_id.split("_")[0] if "_" in voice_id else "af"
    langs = {
        "af": "a", "am": "a", "bf": "b", "bm": "b",
        "ef": "e", "em": "e", "ff": "f", "fm": "f",
        "hf": "h", "hm": "h", "jf": "j", "jm": "j",
    }
    return langs.get(prefix, "a")


class _KokoroWorker:
    """Persistent subprocess running ``voice/kokoro_worker.py``.

    The Kokoro model is loaded once inside the worker and reused for every
    utterance (no per-sentence initialization). Renders WAVs, which the caller
    plays back through PipeWire/PulseAudio.
    """

    def __init__(self, python_bin: str, worker_script: str):
        self._python_bin = python_bin
        self._worker_script = worker_script
        self._proc: subprocess.Popen | None = None
        self._lock = threading.RLock()
        self._next_id = 0

    def _start(self):
        settings = get_settings()
        env = dict(os.environ)
        model_path = getattr(settings, "kokoro_model_path", "") or os.environ.get("KOKORO_MODEL_PATH", "")
        if model_path:
            env["KOKORO_MODEL_PATH"] = model_path
        self._proc = subprocess.Popen(
            [self._python_bin, "-u", self._worker_script],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
            env=env,
        )

    def _ensure(self) -> bool:
        with self._lock:
            if self._proc is not None and self._proc.poll() is None:
                return True
            try:
                self._start()
                ping = self._request({"cmd": "ping"}, timeout=60)
                return bool(ping and ping.get("ok"))
            except Exception:
                if self._proc is not None:
                    with contextlib.suppress(Exception):
                        self._proc.kill()
                    self._proc = None
                return False

    def _request(self, payload: dict, timeout: float = 120.0, _depth: int = 0) -> dict | None:
        if _depth > 16:
            return None
        with self._lock:
            if self._proc is None:
                return None
            try:
                self._proc.stdin.write(json.dumps(payload) + "\n")
                self._proc.stdin.flush()
            except (BrokenPipeError, OSError):
                return None
            line = self._proc.stdout.readline()
            if not line:
                return None
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                # Libraries occasionally print stray text to stdout (e.g. model
                # load warnings). Skip non-JSON lines and read the real response.
                return self._request(payload, timeout=timeout, _depth=_depth + 1)

    def render(self, text: str, voice: str, speed: float, out_path: str) -> bool:
        if not self._ensure():
            return False
        job_id = f"j{self._next_id}"
        self._next_id += 1
        try:
            resp = self._request({
                "id": job_id,
                "text": text,
                "voice": voice,
                "speed": speed,
                "out": out_path,
            })
            return bool(resp and resp.get("ok"))
        except Exception:
            return False

    def stop(self):
        with self._lock:
            if self._proc is not None and self._proc.poll() is None:
                try:
                    self._proc.stdin.write(json.dumps({"cmd": "shutdown"}) + "\n")
                    self._proc.stdin.flush()
                    self._proc.wait(timeout=5)
                except Exception:
                    with contextlib.suppress(Exception):
                        self._proc.kill()
            self._proc = None


def _find_worker_python() -> str | None:
    """Locate the Python interpreter for the dedicated Kokoro worker venv."""
    settings = get_settings()
    candidates: list[Path] = []
    venv_dir = getattr(settings, "tts_venv_dir", "") or os.environ.get("KOKORO_VENV", "")
    if venv_dir:
        base = Path(venv_dir)
        candidates += [base / "bin" / "python", base / "bin" / "python3"]
    candidates += [
        Path("tts-venv/bin/python"),
        Path("tts-venv/bin/python3"),
        Path(sys.prefix).parent / "tts-venv/bin/python",
    ]
    for cand in candidates:
        try:
            if cand.exists() and os.access(cand, os.X_OK):
                return str(cand)
        except OSError:
            continue
    return None


class KokoroTTS:
    """Kokoro TTS with graceful fallbacks, fully non-blocking.

    Backends (in priority order):
      1. ``python``   — kokoro importable in the main interpreter,
      2. ``worker``   — persistent ``voice/kokoro_worker.py`` subprocess,
      3. ``espeak``   — espeak-ng + PipeWire/PulseAudio playback.

    Speech is rendered and played on a dedicated worker thread so the asyncio
    event loop is never blocked while JARVIS is speaking.
    """

    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self.voice = self.settings.tts_voice
        self.speed = self.settings.tts_speed
        self.volume = self.settings.tts_volume
        self._available = False
        self._backend: str | None = None
        self._worker: _KokoroWorker | None = None
        self._check_availability()

    def _check_availability(self):
        try:
            import kokoro  # noqa: F401
            self._available = True
            self._backend = "python"
            return
        except ImportError:
            pass
        try:
            subprocess.run(["kokoro", "--version"], capture_output=True, check=True)
            self._available = True
            self._backend = "cli"
            return
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass
        python_bin = _find_worker_python()
        if python_bin:
            worker_script = str(Path(__file__).resolve().parent / "kokoro_worker.py")
            probe = _KokoroWorker(python_bin, worker_script)
            if probe._ensure():
                self._worker = probe
                self._available = True
                self._backend = "worker"
                return
        if shutil.which("espeak-ng") and shutil.which(self._find_player() or ""):
            self._available = True
            self._backend = "espeak"

    def is_available(self) -> bool:
        return self._available

    @property
    def backend(self) -> str | None:
        return self._backend

    @staticmethod
    def _find_player() -> str | None:
        for binary in ("pw-play", "paplay", "aplay"):
            if shutil.which(binary):
                return binary
        return None

    def list_voices(self) -> list[str]:
        if self._backend == "espeak":
            try:
                out = subprocess.run(["espeak-ng", "--voices"], capture_output=True, text=True, check=False).stdout
                voices = []
                for line in out.splitlines()[1:]:
                    parts = line.split()
                    if len(parts) >= 2:
                        voices.append(parts[1])
                return voices or ["en+f3", "en-us", "en-gb"]
            except Exception:
                return ["en+f3", "en-us", "en-gb"]
        return KOKORO_VOICES

    def voice_catalog(self) -> list[dict]:
        """Structured voice list for the premium UI voice picker.

        Each entry: {id, label, group, gender, engine}.
        """
        if self._backend == "espeak":
            voices = self.list_voices()
            return [
                {"id": v, "label": v, "group": "eSpeak", "gender": "unknown", "engine": "espeak-ng"}
                for v in voices
            ]
        catalog = []
        for voice_id in KOKORO_VOICES:
            gender = _voice_gender(voice_id)
            catalog.append({
                "id": voice_id,
                "label": KOKORO_VOICE_META.get(voice_id, voice_id),
                "group": _voice_group(voice_id),
                "gender": gender,
                "engine": "kokoro",
            })
        return catalog

    def _render_to_wav(self, text: str, wav_path: str) -> bool:
        if self._backend == "python":
            return self._render_inprocess(text, wav_path)
        if self._backend == "cli":
            return self._render_cli(text, wav_path)
        if self._backend == "worker":
            return bool(self._worker and self._worker.render(
                text, self.voice, max(0.5, min(2.5, self.speed / 150.0)), wav_path
            ))
        return False

    def _render_inprocess(self, text: str, wav_path: str) -> bool:
        speed_mult = max(0.5, min(2.5, self.speed / 150.0))
        try:
            import numpy as np
            from kokoro import KPipeline

            try:
                pipeline = KPipeline(lang_code=_lang_for_voice(self.voice), repo_id="hexgrad/Kokoro-82M", model=True)
                gen = pipeline(text, voice=self.voice, speed=speed_mult)
            except Exception:
                pipeline = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M", model=True)
                gen = pipeline(text, voice=self.voice, speed=speed_mult)
            chunks = []
            for _graphemes, _phonemes, audio in gen:
                if audio is None:
                    continue
                chunks.append(np.asarray(audio, dtype="float32"))
            if not chunks:
                return False
            import soundfile as sf

            sf.write(wav_path, np.concatenate(chunks), 24000)
            return True
        except Exception:
            try:
                import soundfile as sf
                from kokoro import generate

                samples, sr = generate(text, voice=self.voice, speed=speed_mult)
                sf.write(wav_path, samples, sr)
                return True
            except Exception:
                return False

    def _render_cli(self, text: str, wav_path: str) -> bool:
        cmd = [
            "kokoro",
            "--voice", self.voice,
            "--speed", str(self.speed),
            "--text", text,
            "--output", wav_path,
        ]
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return Path(wav_path).exists()
        except Exception:
            return False

    def _speak_blocking(self, text: str) -> bool:
        if not text.strip() or not self._available:
            return False
        if self._backend == "espeak":
            return self._speak_espeak(text)
        player = self._find_player()
        if not player:
            return False
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                wav_path = tmp.name
            if not self._render_to_wav(text, wav_path):
                os.unlink(wav_path)
                return False
            vol = max(0.0, min(1.0, self.volume / 100.0))
            play_cmd = [player, "--volume", f"{vol:.2f}", wav_path] if player == "pw-play" else [player, wav_path]
            subprocess.run(play_cmd, capture_output=True, check=True)
            with contextlib.suppress(OSError):
                os.unlink(wav_path)
            return True
        except Exception:
            with contextlib.suppress(OSError, UnboundLocalError):
                os.unlink(wav_path)
            return False

    def _speak_espeak(self, text: str) -> bool:
        player = self._find_player()
        if not player:
            return False
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                wav_path = tmp.name
            subprocess.run(
                ["espeak-ng", "-w", wav_path, "-v", self.voice, "-s", str(self.speed), text],
                capture_output=True,
                check=True,
            )
            vol = max(0.0, min(1.0, self.volume / 100.0))
            play_cmd = [player, "--volume", f"{vol:.2f}", wav_path] if player == "pw-play" else [player, wav_path]
            subprocess.run(play_cmd, capture_output=True, check=True)
            with contextlib.suppress(OSError):
                os.unlink(wav_path)
            return True
        except Exception:
            return False

    async def speak(self, text: str) -> bool:
        """Render + play on a worker thread so the event loop stays responsive."""
        if not text.strip() or not self._available:
            return False
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._speak_blocking, text)

    def speak_sync(self, text: str) -> bool:
        return self._speak_blocking(text)

    def set_voice(self, voice: str):
        self.voice = voice

    def set_speed(self, speed: int):
        self.speed = max(50, min(500, int(speed)))

    def set_volume(self, volume: int):
        self.volume = max(0, min(100, int(volume)))

    def shutdown(self):
        if self._worker is not None:
            with contextlib.suppress(Exception):
                self._worker.stop()
            self._worker = None
