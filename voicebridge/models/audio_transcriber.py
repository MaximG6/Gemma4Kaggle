"""
Audio transcription using Gemma 4 native audio tower via llama-mtmd-cli.

Converts 16 kHz mono WAV audio to a text transcript using:
  - Base Gemma 4 E4B Q4_K_M GGUF  (from unsloth/gemma-4-E4B-it-GGUF)
  - mmproj-BF16.gguf               (multimodal projector, same repo)

The binary llama-mtmd-cli must be built before use — see scripts/build_llama_mtmd.ps1.
Override with env var LLAMA_MTMD_CLI to point at a pre-built binary.

Model paths resolve in order:
  1. Env var (VOICEBRIDGE_BASE_GGUF_PATH / VOICEBRIDGE_MMPROJ_PATH)
  2. models/ directory alongside this file
  3. HuggingFace Hub download (cached under ~/.cache/huggingface/hub)
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np

_BASE_GGUF_REPO = "unsloth/gemma-4-E4B-it-GGUF"
_BASE_GGUF_FILENAME = "gemma-4-E4B-it-Q4_K_M.gguf"
_MMPROJ_FILENAME = "mmproj-BF16.gguf"

# Raw user instruction — passed with --jinja so llama-mtmd-cli applies the
# model's Gemma 4 Jinja chat template.  Do NOT pre-format with <start_of_turn>
# tags here; that causes double-formatting and empty output.
_USER_PROMPT = "Transcribe the audio to text verbatim. Output only the spoken words, nothing else."

# llama-mtmd-cli search paths (Windows native, checked before falling back to env var)
_CLI_SEARCH_PATHS = [
    Path(r"C:\llama.cpp\build\bin\Release\llama-mtmd-cli.exe"),
    Path(r"C:\llama.cpp\build\bin\llama-mtmd-cli.exe"),
    Path(r"C:\llama.cpp\build\bin\Debug\llama-mtmd-cli.exe"),
    Path.home() / "llama.cpp" / "build" / "bin" / "Release" / "llama-mtmd-cli.exe",
    Path.home() / "llama.cpp" / "build" / "bin" / "llama-mtmd-cli.exe",
    Path.home() / "llama.cpp" / "build" / "bin" / "Release" / "llama-mtmd-cli",
    Path.home() / "llama.cpp" / "build" / "bin" / "llama-mtmd-cli",
    # WSL-accessible path
    Path("/usr/local/bin/llama-mtmd-cli"),
    Path("/usr/bin/llama-mtmd-cli"),
]

_BUILD_HINT = (
    "llama-mtmd-cli not found. Build it from source:\n\n"
    "  Windows (PowerShell):\n"
    "    .\\voicebridge\\scripts\\build_llama_mtmd.ps1\n\n"
    "  Linux / WSL:\n"
    "    git clone --depth 1 https://github.com/ggerganov/llama.cpp\n"
    "    cmake -B llama.cpp/build llama.cpp -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=89\n"
    "    cmake --build llama.cpp/build --config Release --target llama-mtmd-cli -j\n\n"
    "Then set env var LLAMA_MTMD_CLI=/path/to/llama-mtmd-cli[.exe]"
)


def _find_mtmd_cli() -> str:
    env_val = os.environ.get("LLAMA_MTMD_CLI", "").strip()
    if env_val and Path(env_val).is_file():
        return env_val

    for candidate in _CLI_SEARCH_PATHS:
        if candidate.is_file():
            return str(candidate)

    raise FileNotFoundError(_BUILD_HINT)


def _resolve_model_file(env_var: str, models_dir: Path, filename: str) -> str:
    env_val = os.environ.get(env_var, "").strip()
    if env_val and Path(env_val).is_file():
        return env_val

    local = models_dir / filename
    if local.is_file():
        return str(local)

    print(f"{filename} not found locally — downloading from {_BASE_GGUF_REPO} ...")
    from huggingface_hub import hf_hub_download
    path = hf_hub_download(repo_id=_BASE_GGUF_REPO, filename=filename)
    print(f"Downloaded to {path}")
    return path


def _strip_ansi(text: str) -> str:
    text = re.sub(r"\x1b\[[0-9;]*[mGKHFABCDJKlh]", "", text)
    text = re.sub(r"\x1b[()][AB012]", "", text)
    text = re.sub(r"[\r\x00]", "", text)
    return text


class GemmaAudioTranscriber:
    """
    Transcribes 16 kHz mono WAV audio to text via llama-mtmd-cli subprocess.

    Uses the base Gemma 4 E4B audio tower — not the fine-tuned triage model.
    Designed to run on GPU 1 (RTX 4090); set CUDA_VISIBLE_DEVICES=1 in env or
    pass gpu_device=1 to the constructor.
    """

    def __init__(
        self,
        model_path: str | None = None,
        mmproj_path: str | None = None,
        n_gpu_layers: int = 99,
        gpu_device: int = -1,
        n_threads: int = 4,
    ) -> None:
        import sys
        models_dir = Path(__file__).parent

        self._mtmd_cli = _find_mtmd_cli()
        self._model_path = model_path or _resolve_model_file(
            "VOICEBRIDGE_BASE_GGUF_PATH", models_dir, _BASE_GGUF_FILENAME
        )
        self._mmproj_path = mmproj_path or _resolve_model_file(
            "VOICEBRIDGE_MMPROJ_PATH", models_dir, _MMPROJ_FILENAME
        )
        self._ngl = n_gpu_layers
                # CUDA ordering on this machine: device 0 = RTX 5090, device 1 = RTX 4090.
        # Default to GPU 1 (RTX 4090) for audio transcription.
        if gpu_device == -1:
            gpu_device = 1
        self._gpu_device = gpu_device
        self._n_threads = n_threads

    def transcribe_audio(self, wav_path: str) -> str:
        """
        Transcribe a 16 kHz mono WAV file to text.

        Args:
            wav_path: Path to a 16 kHz mono WAV file.

        Returns:
            Transcribed text string.

        Raises:
            FileNotFoundError: If wav_path does not exist.
            RuntimeError:      If llama-mtmd-cli produces no output or times out.
        """
        if not Path(wav_path).is_file():
            raise FileNotFoundError(f"WAV file not found: {wav_path}")

        cmd = [
            self._mtmd_cli,
            "-m", self._model_path,
            "--mmproj", self._mmproj_path,
            "--audio", wav_path,
            "-p", _USER_PROMPT,
            "--jinja",
            "-n", "512",
            "--threads", str(self._n_threads),
            "--temp", "0.0",
            "-ngl", str(self._ngl),
            "--no-mmap",
            "--no-warmup",
        ]

        env = os.environ.copy()
        # Restrict to a single GPU so llama.cpp does NOT split the graph across
        # devices.  Multi-device splitting with multimodal inputs (audio + text)
        # exceeds GGML_SCHED_MAX_SPLIT_INPUTS and crashes with an assertion failure.
        # Use the physical GPU index directly — do NOT rely on CUDA_VISIBLE_DEVICES
        # inherited from the parent process (which points to the wrong device after
        # the main process already remapped it).
        env["CUDA_VISIBLE_DEVICES"] = str(self._gpu_device)
        # LD_LIBRARY_PATH: conda's CUDA libs may be a different version than what
        # the binary was compiled against; removing lets it use system CUDA from
        # /etc/ld.so.conf (which matches the build environment)
        env.pop("LD_LIBRARY_PATH", None)

        try:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                env=env,
                timeout=300,
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Audio transcription timed out (300 s)")

        raw = proc.stdout.decode(errors="replace").strip()
        stderr_text = proc.stderr.decode(errors="replace")

        # Some llama.cpp builds route generated text to stderr instead of stdout.
        # Fall back to stderr if stdout is empty.
        if not raw:
            after_marker = stderr_text.rfind("<start_of_turn>model")
            if after_marker != -1:
                raw = stderr_text[after_marker + len("<start_of_turn>model"):].strip()

        if not raw:
            raise RuntimeError(
                f"llama-mtmd-cli produced no output (exit {proc.returncode}). "
                f"stderr (last 3000 chars): {stderr_text[-3000:]}"
            )

        raw = _strip_ansi(raw)

        # Extract model output — everything after the last turn marker
        marker = "<start_of_turn>model"
        idx = raw.rfind(marker)
        if idx != -1:
            raw = raw[idx + len(marker):]

        # Drop any trailing end-of-turn token
        raw = raw.replace("<end_of_turn>", "").strip()
        return raw

    def transcribe_audio_array(self, audio: "np.ndarray", sample_rate: int = 16000) -> str:
        """
        Convenience wrapper: transcribe a numpy float32 PCM array.

        Writes a temporary WAV file, calls transcribe_audio, then cleans up.
        """
        import soundfile as sf

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            sf.write(tmp_path, audio, sample_rate)
            return self.transcribe_audio(tmp_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)
