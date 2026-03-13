"""Modal.com deployment for DDSP timbre transfer.

This module provides serverless GPU-powered timbre transfer using Modal.com.
It includes:
- Persistent volume for caching DDSP models
- GPU functions for timbre transfer
- Web endpoint API for integration

Usage:
    modal deploy modal_app.py
    modal run modal_app::download_all_models
"""
import modal
from pathlib import Path
from typing import Optional, BinaryIO
import io

# Modal configuration
app = modal.App("ddsp-timbre-transfer")

# Create persistent volume for models
models_volume = modal.Volume.from_name("ddsp-models", create_if_missing=True)

# Container image with DDSP and dependencies
# Force rebuild v13 - manual model construction
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
        "ddsp==3.2.0",  # Older version compatible with pretrained models
        "fastapi==0.103.2",
        "python-multipart==0.0.6",
    )
)

# Known pre-trained model URLs from Google Magenta
KNOWN_MODELS = {
    "violin": "https://storage.googleapis.com/ddsp/models/solo_violin_ckpt.zip",
    "flute": "https://storage.googleapis.com/ddsp/models/solo_flute_ckpt.zip",
    "flute2": "https://storage.googleapis.com/ddsp/models/solo_flute2_ckpt.zip",
}


def build_ddsp_model():
    """Build DDSP autoencoder model manually.
    
    Based on the architecture from solo_violin_ckpt operative_config-0.gin
    """
    import tensorflow as tf
    from ddsp import synths, processors, core
    from ddsp.training import preprocessing, decoders, models
    
    # Preprocessor: F0LoudnessPreprocessor
    preprocessor = preprocessing.F0LoudnessPreprocessor(
        time_steps=1000,
        frame_rate=250,
        sample_rate=16000,
        compute_loudness=True,
    )
    
    # Decoder: RnnFcDecoder
    # Output splits: 1 amp + 100 harmonic distribution + 25 noise magnitudes = 126
    decoder = decoders.RnnFcDecoder(
        rnn_channels=512,
        rnn_type='gru',
        ch=512,
        layers_per_stack=3,
        input_keys=('ld_scaled', 'f0_scaled'),
        output_splits=(
            ('amps', 1),
            ('harmonic_distribution', 100),
            ('noise_magnitudes', 25),
        ),
    )
    
    # Processor group: Harmonic + FilteredNoise + Add + Reverb
    harmonic = synths.Harmonic(
        n_samples=64000,
        sample_rate=16000,
        scale_fn=core.exp_sigmoid,
        normalize_below_nyquist=True,
    )
    
    filtered_noise = synths.FilteredNoise(
        n_samples=64000,
        scale_fn=core.exp_sigmoid,
        initial_bias=-5.0,
    )
    
    add = processors.Add(name='add')
    
    # Build DAG: Harmonic -> add with FilteredNoise
    dag = [
        (harmonic, ['amps', 'harmonic_distribution', 'f0_hz']),
        (filtered_noise, ['noise_magnitudes']),
        (add, ['filtered_noise/signal', 'harmonic/signal']),
    ]
    
    processor_group = processors.ProcessorGroup(dag=dag)
    
    # Create autoencoder
    model = models.Autoencoder(
        preprocessor=preprocessor,
        encoder=None,  # No encoder for inference
        decoder=decoder,
        processor_group=processor_group,
        losses=[],  # No losses needed for inference
    )
    
    return model


@app.function(
    image=image,
    volumes={"/models": models_volume},
    timeout=300,
)
def download_model(model_name: str, force: bool = False) -> dict:
    """Download a pre-trained DDSP model."""
    import urllib.request
    import zipfile
    import os
    
    model_dir = Path("/models") / model_name
    
    if model_name not in KNOWN_MODELS:
        return {
            "status": "error",
            "error": f"Unknown model. Available: {list(KNOWN_MODELS.keys())}"
        }
    
    if model_dir.exists() and not force:
        return {"status": "exists", "model_name": model_name}
    
    model_dir.mkdir(parents=True, exist_ok=True)
    url = KNOWN_MODELS[model_name]
    
    # Download
    zip_path = model_dir / "model.zip"
    urllib.request.urlretrieve(url, zip_path)
    
    # Extract
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.namelist():
            # Skip __MACOSX folder
            if '__MACOSX' in member:
                continue
            zf.extract(member, model_dir.parent)
    
    # Move files from nested folder to model_dir
    extracted_folder = model_dir.parent / f"solo_{model_name}_ckpt"
    if extracted_folder.exists():
        for f in extracted_folder.iterdir():
            target = model_dir / f.name
            if target.exists():
                target.unlink()
            f.rename(target)
        extracted_folder.rmdir()
    
    zip_path.unlink()
    
    return {"status": "downloaded", "model_name": model_name}


@app.function(
    image=image,
    volumes={"/models": models_volume},
    gpu="T4",
    timeout=120,
)
def timbre_transfer(
    audio_data: bytes,
    model_name: str = "violin",
    pitch_shift: float = 0.0,
    loudness_db_shift: float = 0.0,
    sample_rate: int = 16000,
) -> dict:
    """Perform timbre transfer using DDSP."""
    import tensorflow as tf
    import librosa
    import soundfile as sf
    import numpy as np
    import gc
    
    model_dir = Path("/models") / model_name
    
    if not model_dir.exists():
        return {"status": "error", "error": f"Model '{model_name}' not found"}
    
    try:
        # Load audio
        audio, sr = librosa.load(io.BytesIO(audio_data), sr=sample_rate, mono=True)
        duration = len(audio) / sr
        
        if duration > 60:
            return {"status": "error", "error": "Audio too long (max 60 seconds)"}
        
        # Find checkpoint
        checkpoint = tf.train.latest_checkpoint(str(model_dir))
        if checkpoint is None:
            # Fallback: look for .index files
            index_files = list(model_dir.glob("*.index"))
            if index_files:
                checkpoint = str(index_files[0]).replace(".index", "")
            else:
                return {"status": "error", "error": "No checkpoint found"}
        
        # Build model
        model = build_ddsp_model()
        
        # Restore weights
        model.restore(checkpoint, verbose=False)
        
        # Prepare features using DDSP's metrics
        from ddsp.training import metrics
        features = metrics.compute_audio_features(audio)
        
        # Apply shifts
        if pitch_shift != 0:
            features['f0_hz'] = features['f0_hz'] * (2 ** (pitch_shift / 12))
        if loudness_db_shift != 0:
            features['loudness_db'] = features['loudness_db'] + loudness_db_shift
        
        # Run inference
        outputs = model(features, training=False)
        audio_gen = outputs['audio_synth'].numpy()
        
        # Convert to bytes
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
    volumes={"/models": models_volume},
    timeout=60,
)
def list_models() -> dict:
    """List available and downloaded models."""
    available = list(KNOWN_MODELS.keys())
    downloaded = []
    
    models_dir = Path("/models")
    if models_dir.exists():
        for item in models_dir.iterdir():
            if item.is_dir() and any((item / f"{p}").exists() 
                                      for p in ["operative_config-0.gin", 
                                               "checkpoint",
                                               "model.ckpt-38100.index"]):
                downloaded.append(item.name)
    
    return {
        "available": available,
        "downloaded": downloaded,
    }


@app.local_entrypoint
def main():
    """CLI entry point for testing."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: modal run modal_app.py [download|list|transfer]")
        return
    
    cmd = sys.argv[1]
    
    if cmd == "download":
        model = sys.argv[2] if len(sys.argv) > 2 else "violin"
        result = download_model.remote(model)
        print(f"Download result: {result}")
    
    elif cmd == "list":
        result = list_models.remote()
        print(f"Models: {result}")
    
    elif cmd == "download_all":
        for model in KNOWN_MODELS.keys():
            print(f"Downloading {model}...")
            result = download_model.remote(model)
            print(f"  Result: {result['status']}")
    
    else:
        print(f"Unknown command: {cmd}")
