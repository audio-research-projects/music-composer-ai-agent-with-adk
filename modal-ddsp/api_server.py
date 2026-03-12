"""FastAPI server for DDSP Modal integration.

This module provides a FastAPI application that can be deployed to Modal
as a web endpoint for DDSP timbre transfer services.

Usage:
    modal deploy api_server.py
"""
import modal
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import io

from modal_app import (
    timbre_transfer,
    list_models,
    download_model,
    analyze_audio,
    models_volume,
)

# Create Modal app
app = modal.App("ddsp-api")

# Reuse the same image and volume from modal_app
image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install("libsndfile1", "ffmpeg", "wget", "unzip")
    .pip_install(
        "ddsp>=3.6.0",
        "tensorflow>=2.10.0,<2.16",
        "tensorflow-probability>=0.18.0,<0.24.0",
        "numpy>=1.23.0,<2.0",
        "scipy>=1.9.0,<1.14",
        "librosa>=0.9.0",
        "soundfile>=0.11.0",
        "gin-config>=0.5.0",
        "fastapi>=0.100.0",
        "python-multipart>=0.0.6",
        "uvicorn>=0.23.0",
    )
)


@app.function(
    image=image,
    volumes={"/models": models_volume},
    gpu="T4",
    timeout=300,
)
@modal.asgi_app()
def fastapi_app():
    """Deploy FastAPI app to Modal."""
    
    web_app = FastAPI(
        title="DDSP Timbre Transfer API",
        description="Neural audio timbre transfer powered by DDSP on Modal.com",
        version="1.0.0"
    )
    
    @web_app.get("/")
    async def root():
        return {
            "service": "DDSP Timbre Transfer API",
            "version": "1.0.0",
            "docs": "/docs",
            "endpoints": {
                "health": "/health",
                "models": "/models",
                "transfer": "/transfer",
                "analyze": "/analyze",
            }
        }
    
    @web_app.get("/health")
    async def health():
        """Health check endpoint."""
        models = list_models.remote()
        return {
            "status": "healthy",
            "models_available": models.get("downloaded_models", []),
            "models_dir": models.get("models_dir"),
        }
    
    @web_app.get("/models")
    async def get_models():
        """List available and downloaded models."""
        return list_models.remote()
    
    @web_app.post("/models/download/{model_name}")
    async def post_download_model(model_name: str, force: bool = False):
        """Download a specific model."""
        result = download_model.remote(model_name, force)
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    
    @web_app.post("/transfer")
    async def post_transfer(
        audio: UploadFile = File(...),
        model: str = Form("violin"),
        pitch_shift: float = Form(0.0),
        loudness_db_shift: float = Form(0.0),
    ):
        """Apply timbre transfer to uploaded audio.
        
        Args:
            audio: Audio file to process (WAV, MP3, etc.)
            model: Target instrument model (violin, flute, tenor_sax, trumpet)
            pitch_shift: Pitch shift in semitones (-12 to +12)
            loudness_db_shift: Loudness adjustment in dB (-20 to +20)
            
        Returns:
            Processed audio file as WAV
        """
        # Read uploaded file
        audio_bytes = await audio.read()
        
        # Validate file size (max 10MB)
        if len(audio_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large. Max 10MB.")
        
        # Run timbre transfer
        result = timbre_transfer.remote(
            audio_data=audio_bytes,
            model_name=model,
            pitch_shift=pitch_shift,
            loudness_db_shift=loudness_db_shift,
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Return audio file
        output_bytes = result["output_audio"]
        output_io = io.BytesIO(output_bytes)
        output_io.seek(0)
        
        return StreamingResponse(
            output_io,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename=overdub_{model}.wav",
                "X-Model-Used": model,
                "X-Duration": str(result["duration_seconds"]),
            }
        )
    
    @web_app.post("/analyze")
    async def post_analyze(
        audio: UploadFile = File(...),
    ):
        """Analyze pitch and loudness of audio file."""
        audio_bytes = await audio.read()
        
        if len(audio_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large. Max 10MB.")
        
        result = analyze_audio.remote(audio_bytes)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
    
    @web_app.get("/models/{model_name}/info")
    async def get_model_info(model_name: str):
        """Get info about a specific model."""
        models = list_models.remote()
        
        if model_name not in models.get("available_models", []):
            raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
        
        downloaded = model_name in models.get("downloaded_models", [])
        
        return {
            "name": model_name,
            "downloaded": downloaded,
            "url": models.get("model_urls", {}).get(model_name),
        }
    
    return web_app
