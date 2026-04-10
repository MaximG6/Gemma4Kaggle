"""
Audio capture module — entry point for the VoiceBridge pipeline.

Provides two endpoints:
  POST /audio/upload   — accepts a WAV/MP3/OGG file, resamples to 16 kHz mono,
                         returns duration and sample count.
  WS   /audio/stream   — accepts raw float32 PCM chunks over WebSocket,
                         concatenates and returns final sample count.
"""

import io

import librosa
import numpy as np
from fastapi import APIRouter, UploadFile, WebSocket

router = APIRouter()


def resample_to_16k(audio_bytes: bytes) -> np.ndarray:
    """Load any audio format from bytes and return a 16 kHz mono float32 array."""
    audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=None, mono=True)
    if sr != 16000:
        audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
    return audio.astype(np.float32)


@router.post("/audio/upload")
async def upload_audio(file: UploadFile):
    """
    Accept a WAV/MP3/OGG upload, resample to 16 kHz mono.

    Returns:
        duration_s   – clip length in seconds (float, 2 d.p.)
        samples      – number of samples at 16 kHz
        filename     – original filename from the upload
    """
    raw = await file.read()
    audio_array = resample_to_16k(raw)
    return {
        "duration_s": round(len(audio_array) / 16000, 2),
        "samples": len(audio_array),
        "filename": file.filename,
    }


@router.websocket("/audio/stream")
async def stream_audio(ws: WebSocket):
    """
    Accept a stream of raw float32 PCM chunks at 16 kHz.

    Client sends binary frames (raw float32 little-endian).
    After the client closes the connection, the server responds with
    the total number of samples received.
    """
    await ws.accept()
    chunks: list[np.ndarray] = []
    async for data in ws.iter_bytes():
        chunks.append(np.frombuffer(data, dtype=np.float32))
    full = np.concatenate(chunks) if chunks else np.array([], dtype=np.float32)
    await ws.send_json({
        "samples": len(full),
        "duration_s": round(len(full) / 16000, 2),
    })
