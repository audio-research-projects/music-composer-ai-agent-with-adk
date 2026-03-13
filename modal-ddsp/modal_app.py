"""Modal.com deployment for DDSP timbre transfer.

This module provides serverless GPU-powered timbre transfer using Modal.com.
It includes:
- Persistent volume for caching DDSP models
- GPU functions for timbre transfer
- Web endpoint API for integration
- MCP-compatible server interface

Usage:
    modal deploy modal_app.py
    modal run modal_app::download_all_models
"""
import modal
from pathlib import Path
from typing import Optional, BinaryIO
import io
import re

# Modal configuration
app = modal.App("ddsp-timbre-transfer")

# Create persistent volume for models
# Models are downloaded once and cached across invocations
models_volume = modal.Volume.from_name("ddsp-models", create_if_missing=True)

# Container image with DDSP and dependencies
# Force rebuild v6 - regex-based gin config filtering
image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install("libsndfile1", "ffmpeg", "wget", "unzip")
    .pip_install(
        "tensorflow==2.11.1",
        "tensorflow-probability==0.19.0",
        "numpy==1.23.5",
        "scipy==1.10.1",
        "librosa==0.9.2",
        "soundfile==0.12.1",
        "ddsp==3.6.0",
        "gin-config==0.5.0",
        "fastapi==0.103.2",
        "python-multipart==0.0.6",
    )
)

# Known pre-trained model URLs from Google Magenta
# Note: Models are in /models/ directory, not root
KNOWN_MODELS = {
    "violin": "https://storage.googleapis.com/ddsp/models/solo_violin_ckpt.zip",
    "flute": "https://storage.googleapis.com/ddsp/models/solo_flute_ckpt.zip",
    "flute2": "https://storage.googleapis.com/ddsp/models/solo_flute2_ckpt.zip",
    # Additional models available:
    # "tenor_sax": "https://storage.googleapis.com/ddsp/models/solo_tenor_saxophone_ckpt.zip",
    # "trumpet": "https://storage.googleapis.com/ddsp/models/solo_trumpet_ckpt.zip",
    # "saxophone": "https://storage.googleapis.com/ddsp/models/solo_saxophone_ckpt.zip",
}


@app.function(
    image=image,
    volumes={"/models": models_volume},
    timeout=300,
)
def download_model(model_name: str, force: bool = False) -> dict:
    """Download a pre-trained DDSP model to the persistent volume.
    
    Args:
        model_name: Name of the model (violin, flute, tenor_sax, trumpet, flute2)
        force: Re-download even if model exists
        
    Returns:
        Status dict with model path or error
    """
    import urllib.request
    import zipfile
    import os
    
    model_dir = Path("/models") / model_name
    
    if model_name not in KNOWN_MODELS:
        available = list(KNOWN_MODELS.keys())
        return {
            "status": "error",
            "error": f"Unknown model '{model_name}'. Available: {available}"
        }
    
    # Check if already exists
    if model_dir.exists() and not force:
        return {
            "status": "exists",
            "model_name": model_name,
            "path": str(model_dir),
            "message": "Model already cached"
        }
    
    model_dir.mkdir(parents=True, exist_ok=True)
    url = KNOWN_MODELS[model_name]
    
    files_before = list(model_dir.iterdir()) if model_dir.exists() else []
    
    try:
        # Download to temp file
        zip_path = model_dir / "model.zip"
        print(f"Downloading {url} to {zip_path}...")
        urllib.request.urlretrieve(url, str(zip_path))
        zip_size = zip_path.stat().st_size
        print(f"Downloaded {zip_size} bytes")
        
        # Extract
        extract_dir = model_dir / "extract"
        extract_dir.mkdir(parents=True, exist_ok=True)
        print(f"Extracting to {extract_dir}...")
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(str(extract_dir))
        
        # Show what was extracted
        extracted_files = list(extract_dir.rglob("*"))
        print(f"Extracted {len(extracted_files)} items")
        for f in extracted_files[:10]:  # Show first 10
            print(f"  - {f.relative_to(extract_dir)}")
        
        # Move files if they were extracted to a subdirectory
        # Filter out macOS metadata directory
        extracted_dirs = [d for d in extract_dir.iterdir() if d.is_dir() and d.name != "__MACOSX"]
        print(f"Found {len(extracted_dirs)} directories in extract folder (excluding __MACOSX)")
        
        # Check if there's a nested directory with checkpoint files
        model_subdir = None
        for d in extracted_dirs:
            if (d / "operative_config-0.gin").exists() or list(d.glob("*.ckpt*")):
                model_subdir = d
                break
        
        if model_subdir:
            # Files are nested in a subdirectory, move them up
            print(f"Moving files from nested dir: {model_subdir.name}")
            for f in model_subdir.iterdir():
                dest = model_dir / f.name
                print(f"  Moving {f.name} -> {dest}")
                f.rename(dest)
            model_subdir.rmdir()
            # Also clean up __MACOSX if present
            macosx_dir = extract_dir / "__MACOSX"
            if macosx_dir.exists():
                import shutil
                shutil.rmtree(str(macosx_dir))
        elif len(extracted_dirs) == 1 and not (extract_dir / "operative_config-0.gin").exists():
            # Single nested dir (fallback)
            nested_dir = extracted_dirs[0]
            print(f"Moving files from nested dir: {nested_dir.name}")
            for f in nested_dir.iterdir():
                dest = model_dir / f.name
                print(f"  Moving {f.name} -> {dest}")
                f.rename(dest)
            nested_dir.rmdir()
        else:
            # Files are at root of extract dir, move them up
            print(f"Moving files from extract dir to {model_dir}")
            for f in extract_dir.iterdir():
                if f.name == "__MACOSX":
                    continue  # Skip macOS metadata
                dest = model_dir / f.name
                print(f"  Moving {f.name} -> {dest}")
                f.rename(dest)
        
        extract_dir.rmdir()
        
        # Clean up zip
        zip_path.unlink()
        
        # Show final files before commit
        final_files = list(model_dir.iterdir())
        print(f"Files in {model_dir} before commit: {[f.name for f in final_files]}")
        
        # Commit to volume
        print("Committing to volume...")
        models_volume.commit()
        
        return {
            "status": "success",
            "model_name": model_name,
            "path": str(model_dir),
            "url": url,
            "zip_size": zip_size,
            "files": [f.name for f in final_files],
        }
        
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "model_name": model_name,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "files_before": [f.name for f in files_before],
        }


@app.function(
    image=image,
    volumes={"/models": models_volume},
    timeout=60,
)
def list_models() -> dict:
    """List available and downloaded models.
    
    Returns:
        Dict with available models and their download status
    """
    models_path = Path("/models")
    downloaded = []
    
    if models_path.exists():
        downloaded = [d.name for d in models_path.iterdir() if d.is_dir()]
    
    return {
        "available_models": list(KNOWN_MODELS.keys()),
        "downloaded_models": downloaded,
        "models_dir": str(models_path),
        "model_urls": KNOWN_MODELS
    }


@app.function(
    image=image,
    volumes={"/models": models_volume},
    gpu="T4",  # GPU for faster inference
    timeout=300,
    memory=8192,  # 8GB RAM
)
def timbre_transfer(
    audio_data: bytes,
    model_name: str = "violin",
    pitch_shift: float = 0.0,
    loudness_db_shift: float = 0.0,
    sample_rate: int = 16000,
) -> dict:
    """Apply timbre transfer to audio using DDSP.
    
    Args:
        audio_data: Raw audio bytes (WAV format preferred)
        model_name: DDSP model to use
        pitch_shift: Pitch shift in semitones
        loudness_db_shift: Loudness adjustment in dB
        sample_rate: Expected sample rate (default 16000)
        
    Returns:
        Dict with status, output audio bytes, and metadata
    """
    import tensorflow as tf
    import librosa
    import soundfile as sf
    import numpy as np
    import io
    import ddsp
    import ddsp.training
    import gc
    
    model_dir = Path("/models") / model_name
    
    if not model_dir.exists():
        return {
            "status": "error",
            "error": f"Model '{model_name}' not found. Run download_model first."
        }
    
    # Clean up leftover directories from previous extractions
    for leftover in ["__MACOSX", f"solo_{model_name}_ckpt"]:
        leftover_path = model_dir / leftover
        if leftover_path.exists():
            import shutil
            print(f"Cleaning up leftover directory: {leftover}")
            shutil.rmtree(str(leftover_path))
    
    try:
        # Load audio from bytes
        audio, sr = librosa.load(io.BytesIO(audio_data), sr=sample_rate, mono=True)
        duration = len(audio) / sr
        
        if duration > 60:  # Limit to 60 seconds
            return {
                "status": "error",
                "error": "Audio too long. Maximum 60 seconds allowed."
            }
        
        # Find checkpoint
        checkpoint = tf.train.latest_checkpoint(str(model_dir))
        
        # If no checkpoint file, look for .index files directly
        if checkpoint is None:
            index_files = list(model_dir.glob("*.index"))
            if index_files:
                # Use the first (or highest numbered) checkpoint
                checkpoint = str(index_files[0]).replace(".index", "")
                print(f"Found checkpoint directly: {checkpoint}")
        
        if checkpoint is None:
            # Debug: list files in model directory
            files = []
            if model_dir.exists():
                for f in model_dir.rglob("*"):
                    if f.is_file():
                        files.append(str(f.relative_to(model_dir)))
            return {
                "status": "error",
                "error": f"No checkpoint found in {model_dir}",
                "debug_files": files[:20],  # First 20 files
                "hint": "Run 'modal run modal_app::download_model --model-name MODEL' first"
            }
        
        # Parse gin config but skip incompatible parameters
        # Models were trained with newer DDSP, some params don't exist in our version
        gin_file = model_dir / "operative_config-0.gin"
        if gin_file.exists():
            import gin
            config_text = gin_file.read_text()
            
            # Remove problematic parameters with regex
            # These params exist in newer DDSP but not in our pinned version
            removals = [
                r'FilteredNoise\.noise_fade_fn\s*=\s*[^\n]+\n',
                r'SpectralLoss\.delta_delta_freq_weight\s*=\s*[^\n]+\n', 
                r'SpectralLoss\.delta_delta_time_weight\s*=\s*[^\n]+\n',
                r'SpectralLoss\.delta_freq_weight\s*=\s*[^\n]+\n',
                r'SpectralLoss\.delta_time_weight\s*=\s*[^\n]+\n',
            ]
            
            for pattern in removals:
                config_text = re.sub(pattern, '', config_text)
            
            # Fix ambiguous Add reference
            config_text = re.sub(r'(?<![\w.])Add\.', 'ddsp.processors.Add.', config_text)
            
            with gin.unlock_config():
                gin.parse_config(config_text, skip_unknown=True)
                print(f"  Loaded gin config (filtered for compatibility)")
        
        # Create and restore model
        model = ddsp.training.models.Autoencoder()
        model.restore(checkpoint, verbose=False)
        
        # Prepare features
        features = ddsp.training.metrics.compute_audio_features(audio, frame_rate=250)
        
        # Apply shifts
        if pitch_shift != 0:
            features['f0_hz'] = features['f0_hz'] * (2 ** (pitch_shift / 12))
        if loudness_db_shift != 0:
            features['loudness_db'] = features['loudness_db'] + loudness_db_shift
        
        # Run inference
        outputs = model(features, training=False)
        audio_gen = outputs['audio_synth'].numpy()
        
        # Convert back to bytes
        output_buffer = io.BytesIO()
        sf.write(output_buffer, audio_gen, sr, format='WAV')
        output_bytes = output_buffer.getvalue()
        
        # Cleanup
        del model, outputs
        gc.collect()
        tf.keras.backend.clear_session()
        
        return {
            "status": "success",
            "model_name": model_name,
            "duration_seconds": float(duration),
            "pitch_shift": pitch_shift,
            "loudness_shift": loudness_db_shift,
            "output_audio": output_bytes,
            "output_format": "wav",
            "sample_rate": sample_rate,
        }
        
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@app.function(
    image=image,
    timeout=60,
)
def analyze_audio(
    audio_data: bytes,
    sample_rate: int = 16000,
) -> dict:
    """Analyze pitch and loudness of audio.
    
    Args:
        audio_data: Raw audio bytes
        sample_rate: Expected sample rate
        
    Returns:
        Analysis results with pitch contour and statistics
    """
    import librosa
    import numpy as np
    import io
    
    try:
        # Load audio
        audio, sr = librosa.load(io.BytesIO(audio_data), sr=sample_rate, mono=True)
        
        # Extract pitch
        f0, voiced_flag, voiced_probs = librosa.pyin(
            audio,
            fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C7')
        )
        
        # Calculate loudness
        hop_length = 256
        rms = librosa.feature.rms(y=audio, hop_length=hop_length)[0]
        loudness_db = 20 * np.log10(rms + 1e-10)
        
        # Statistics
        valid_f0 = f0[f0 > 0]
        
        return {
            "status": "success",
            "duration": float(len(audio) / sr),
            "sample_rate": sr,
            "pitch": {
                "mean_hz": float(np.mean(valid_f0)) if len(valid_f0) > 0 else 0,
                "min_hz": float(np.min(valid_f0)) if len(valid_f0) > 0 else 0,
                "max_hz": float(np.max(valid_f0)) if len(valid_f0) > 0 else 0,
            },
            "loudness": {
                "mean_db": float(np.mean(loudness_db)),
                "min_db": float(np.min(loudness_db)),
                "max_db": float(np.max(loudness_db)),
            },
            "voiced_frames": int(np.sum(voiced_flag)),
            "total_frames": len(voiced_flag),
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


# Web API endpoint for external integration
@app.function(
    image=image,
    volumes={"/models": models_volume},
    gpu="T4",
)
@modal.fastapi_endpoint(method="POST")
def api_timbre_transfer(
    audio: bytes,
    model: str = "violin",
    pitch_shift: float = 0.0,
    loudness_db_shift: float = 0.0,
) -> dict:
    """Web API endpoint for timbre transfer.
    
    Can be called via HTTP POST with multipart/form-data.
    """
    result = timbre_transfer.remote(
        audio_data=audio,
        model_name=model,
        pitch_shift=pitch_shift,
        loudness_db_shift=loudness_db_shift,
    )
    
    # Don't return raw bytes in JSON, encode or provide download URL
    if result["status"] == "success":
        import base64
        result["output_audio_base64"] = base64.b64encode(
            result.pop("output_audio")
        ).decode('utf-8')
    
    return result


@app.function(
    image=image,
    volumes={"/models": models_volume},
)
@modal.fastapi_endpoint(method="GET")
def api_health() -> dict:
    """Health check endpoint."""
    models = list_models.remote()
    return {
        "status": "healthy",
        "service": "ddsp-timbre-transfer",
        "models_cached": models.get("downloaded_models", []),
    }


@app.local_entrypoint()
def download_all_models():
    """Download all known models (run with: modal run modal_app::download_all_models)"""
    print("Downloading all DDSP models...")
    
    for model_name in KNOWN_MODELS.keys():
        print(f"\nDownloading {model_name}...")
        result = download_model.remote(model_name)
        print(f"Result: {result['status']}")
        if result['status'] == 'error':
            print(f"Error: {result.get('error')}")
    
    print("\nAll models downloaded!")
    print(list_models.remote())
