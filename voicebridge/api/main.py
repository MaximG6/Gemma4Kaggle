"""
VoiceBridge FastAPI application entry point.

Run:
    uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI

from api.audio_capture import router as audio_router

app = FastAPI(
    title="VoiceBridge",
    description="Offline multilingual clinical intake AI",
    version="0.1.0",
)

app.include_router(audio_router)


@app.get("/health")
def health():
    return {"status": "ok"}
