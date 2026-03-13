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
# Force rebuild v20 - CUDA base image with proper setup
image = (
    modal.Image.from_registry(
        "nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04",
        add_python="3.10"
    )
    .apt_install("libsndfile1", "ffmpeg", "wget", "unzip", "curl", "gnupg", "git")
    # Install Google Cloud SDK for gsutil
    .run_commands(
        "echo 'deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main' | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list",
        "curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -",
        "apt-get update && apt-get install -y google-cloud-sdk",
    )
    .pip_install("setuptools<58", "wheel")  # For crepe compatibility
    .pip_install(
        "tensorflow==2.11.1",
        "tensorflow-probability==0.19.0",
        "numpy<2.0",
        "scipy<1.11",
        "librosa<0.11",
        "soundfile",
    )
    # Install crepe separately with no build isolation
    .run_commands("pip install crepe==0.0.12 --no-build-isolation")
    .pip_install("ddsp==3.6.0", "fastapi", "python-multipart")
)

# Known pre-trained model URLs from Google Magenta
KNOWN_MODELS = {
    "violin": "https://storage.googleapis.com/ddsp/models/solo_violin_ckpt.zip",
    "flute": "https://storage.googleapis.com/ddsp/models/solo_flute_ckpt.zip",
    "flute2": "https://storage.googleapis.com/ddsp/models/solo_flute2_ckpt.zip",
}


def build_ddsp_model(duration_seconds: float = 4.0):
    """Build DDSP autoencoder model manually with configurable duration.
    
    Based on the architecture from solo_violin_ckpt operative_config-0.gin
    
    Args:
        duration_seconds: Length of audio to process (default 4.0, can go up to ~15-20s on T4)
    """
    import tensorflow as tf
    from ddsp import synths, processors, core
    from ddsp.training import preprocessing, decoders, models
    
    sample_rate = 16000
    frame_rate = 250
    
    # Calculate parameters based on duration
    n_samples = int(sample_rate * duration_seconds)
    time_steps = int(frame_rate * duration_seconds)
    
    print(f"Building model for {duration_seconds}s audio:")
    print(f"  n_samples: {n_samples}, time_steps: {time_steps}")
    
    # Preprocessor: F0LoudnessPreprocessor
    preprocessor = preprocessing.F0LoudnessPreprocessor(
        time_steps=time_steps,
        frame_rate=frame_rate,
        sample_rate=sample_rate,
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
    
    # Processor group: Harmonic + FilteredNoise + Add
    harmonic = synths.Harmonic(
        n_samples=n_samples,
        sample_rate=sample_rate,
        scale_fn=core.exp_sigmoid,
        normalize_below_nyquist=True,
    )
    
    filtered_noise = synths.FilteredNoise(
        n_samples=n_samples,
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
    """Download a pre-trained DDSP model using gsutil."""
    import subprocess
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
    
    # Extract bucket path from URL
    url = KNOWN_MODELS[model_name]
    # URL format: https://storage.googleapis.com/ddsp/models/solo_{model}_ckpt.zip
    # gsutil format: gs://ddsp/models/solo_{model}_ckpt.zip
    gs_path = url.replace("https://storage.googleapis.com/", "gs://")
    
    print(f"Downloading {model_name} from {gs_path}...")
    
    # Download using gsutil
    zip_path = model_dir / "model.zip"
    result = subprocess.run(
        ["gsutil", "cp", gs_path, str(zip_path)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        return {
            "status": "error",
            "error": f"gsutil failed: {result.stderr}",
            "stdout": result.stdout,
        }
    
    print(f"Downloaded to {zip_path}, extracting...")
    
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
    
    print(f"Model {model_name} ready at {model_dir}")
    return {"status": "downloaded", "model_name": model_name}


@app.function(
    image=image,
    volumes={"/models": models_volume},
    gpu="T4",
    timeout=300,  # Increased timeout for cold start
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
        import numpy as np
        
        # Verify GPU availability
        print(f"TensorFlow version: {tf.__version__}")
        print(f"CUDA available: {tf.test.is_built_with_cuda()}")
        gpus = tf.config.list_physical_devices('GPU')
        print(f"GPUs: {gpus}")
        
        # Load audio
        print("Loading audio...")
        audio, sr = librosa.load(io.BytesIO(audio_data), sr=sample_rate, mono=True)
        duration = len(audio) / sr
        print(f"Audio loaded: {duration:.2f}s, {len(audio)} samples")
        
        if duration > 60:
            return {"status": "error", "error": "Audio too long (max 60 seconds)"}
        
        # Find checkpoint
        print("Finding checkpoint...")
        checkpoint = tf.train.latest_checkpoint(str(model_dir))
        if checkpoint is None:
            # Fallback: look for .index files
            index_files = list(model_dir.glob("*.index"))
            if index_files:
                checkpoint = str(index_files[0]).replace(".index", "")
            else:
                return {"status": "error", "error": "No checkpoint found"}
        print(f"Checkpoint: {checkpoint}")
        
        # Build model with audio duration
        print("Building model...")
        model = build_ddsp_model(duration_seconds=duration)
        print("Model built, restoring weights...")
        
        # Restore weights
        model.restore(checkpoint, verbose=True)
        print("Weights restored")
        
        # Prepare features using DDSP's metrics
        print("Computing audio features...")
        from ddsp.training import metrics
        features = metrics.compute_audio_features(audio)
        print(f"Features computed: {list(features.keys())}")
        
        # Apply shifts
        if pitch_shift != 0:
            features['f0_hz'] = features['f0_hz'] * (2 ** (pitch_shift / 12))
        if loudness_db_shift != 0:
            features['loudness_db'] = features['loudness_db'] + loudness_db_shift
        
        # Run inference
        print("Running inference...")
        outputs = model(features, training=False)
        print(f"Outputs: {list(outputs.keys())}")
        audio_gen = outputs['audio_synth']
        # Convert to numpy if it's a tensor
        if hasattr(audio_gen, 'numpy'):
            audio_gen = audio_gen.numpy()
        # Ensure it's 1D array
        audio_gen = np.squeeze(audio_gen)
        print(f"Generated audio shape: {audio_gen.shape}, dtype: {audio_gen.dtype}")
        
        # Convert to bytes
        output_buffer = io.BytesIO()
        sf.write(output_buffer, audio_gen, sr, format='WAV')
        output_bytes = output_buffer.getvalue()
        print(f"Output audio: {len(output_bytes)} bytes")
        
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
    gpu="T4",
    timeout=60,
)
def gpu_check() -> dict:
    """Check GPU availability and TensorFlow configuration."""
    import tensorflow as tf
    import os
    
    # Check CUDA_VISIBLE_DEVICES
    cuda_devices = os.environ.get('CUDA_VISIBLE_DEVICES', 'Not set')
    
    # Check TensorFlow GPU
    gpus = tf.config.list_physical_devices('GPU')
    
    # Check if built with CUDA
    built_with_cuda = tf.test.is_built_with_cuda()
    
    # Try to get GPU info
    gpu_info = []
    for gpu in gpus:
        gpu_info.append({
            "name": gpu.name,
            "type": gpu.device_type,
        })
    
    return {
        "tensorflow_version": tf.__version__,
        "cuda_visible_devices": cuda_devices,
        "built_with_cuda": built_with_cuda,
        "gpus_found": len(gpus),
        "gpu_info": gpu_info,
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


@app.local_entrypoint()
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
