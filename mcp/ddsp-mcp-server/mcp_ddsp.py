"""MCP Server for DDSP (Differentiable Digital Signal Processing).

Provides tools for:
- Timbre transfer: Transform audio to sound like a different instrument
- Audio synthesis with neural models
- Pitch detection and manipulation

DDSP models must be downloaded or trained separately.
"""
from mcp.server.fastmcp import FastMCP
import os
from pathlib import Path
from typing import Optional, Literal
import tempfile
import json

# Initialize FastMCP server
mcp = FastMCP("ddsp")

# Default model paths - users should place models here or provide custom paths
DEFAULT_MODELS_DIR = Path(__file__).parent / "models"


def _get_available_models() -> dict:
    """Scan for available DDSP models in the models directory."""
    models = {}
    if DEFAULT_MODELS_DIR.exists():
        for model_dir in DEFAULT_MODELS_DIR.iterdir():
            if model_dir.is_dir():
                # Look for checkpoint files
                ckpt_files = list(model_dir.glob("*.ckpt")) + list(model_dir.glob("*.index"))
                if ckpt_files:
                    models[model_dir.name] = str(model_dir)
    return models


@mcp.tool()
async def list_models() -> str:
    """List available DDSP models for timbre transfer.
    
    Returns:
        JSON string with available models and their instruments
    """
    try:
        models = _get_available_models()
        
        # Default model descriptions
        model_info = {
            "violin": "String instrument - suitable for melodic lines",
            "flute": "Woodwind instrument - soft, breathy tones",
            "saxophone": "Brass instrument - jazz, expressive",
            "trumpet": "Brass instrument - bright, piercing",
            "tenor_sax": "Brass instrument - warm, jazz tones",
            "flute2": "Alternative flute model",
        }
        
        result = {
            "available_models": models,
            "models_dir": str(DEFAULT_MODELS_DIR),
            "descriptions": {k: v for k, v in model_info.items() if k in models},
            "note": "Place trained DDSP models in the models/ directory"
        }
        
        if not models:
            result["message"] = "No models found. Download pre-trained models or train your own."
            result["download_url"] = "https://github.com/magenta/ddsp/tree/main/ddsp/colab"
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def timbre_transfer(
    input_path: str,
    output_path: str,
    model_name: str = "violin",
    pitch_shift: float = 0.0,
    loudness_db_shift: float = 0.0,
    model_path: Optional[str] = None,
) -> str:
    """Apply timbre transfer to transform audio to sound like a different instrument.
    
    Uses DDSP to transform the input audio, preserving pitch and timing but
    changing the timbre to match the target instrument model.
    
    Args:
        input_path: Path to input audio file (wav, mp3, etc.)
        output_path: Path for output audio file
        model_name: Name of the model to use (violin, flute, saxophone, etc.)
        pitch_shift: Pitch shift in semitones (optional)
        loudness_db_shift: Loudness adjustment in dB (optional)
        model_path: Custom path to model checkpoint (optional, overrides model_name)
        
    Returns:
        Success message with output file path
    """
    try:
        import ddsp
        import ddsp.training
        from ddsp.training.postprocessing import detect_notes
        import tensorflow as tf
        import librosa
        import soundfile as sf
        import numpy as np
        
        input_path = Path(input_path).expanduser().resolve()
        output_path = Path(output_path).expanduser().resolve()
        
        if not input_path.exists():
            return f"Error: Input file not found: {input_path}"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Determine model path
        if model_path:
            ckpt_path = Path(model_path).expanduser().resolve()
        else:
            ckpt_path = DEFAULT_MODELS_DIR / model_name
        
        if not ckpt_path.exists():
            available = _get_available_models()
            return f"Error: Model '{model_name}' not found at {ckpt_path}. Available: {list(available.keys())}"
        
        # Load audio
        audio, sr = librosa.load(str(input_path), sr=16000, mono=True)
        
        # Setup DDSP model
        gin_file = ckpt_path / "operative_config-0.gin"
        if gin_file.exists():
            ddsp.training.metrics.gin_parse(gin_file)
        
        # Load checkpoint
        checkpoint = tf.train.latest_checkpoint(str(ckpt_path))
        if checkpoint is None:
            return f"Error: No checkpoint found in {ckpt_path}"
        
        # Create model and restore
        model = ddsp.training.models.Autoencoder()
        model.restore(checkpoint)
        
        # Preprocess audio
        features = {
            'audio': audio,
            'sample_rate': sr,
        }
        
        # Extract features using DDSP
        features = ddsp.training.metrics.compute_audio_features(features)
        
        # Apply shifts
        if pitch_shift != 0:
            features['f0_hz'] *= 2 ** (pitch_shift / 12)
        if loudness_db_shift != 0:
            features['loudness_db'] += loudness_db_shift
        
        # Resynthesize with new timbre
        outputs = model(features, training=False)
        audio_gen = outputs['audio_synth'].numpy()
        
        # Save output
        sf.write(str(output_path), audio_gen, sr)
        
        return f"Successfully applied timbre transfer ({model_name}) to: {output_path}"
        
    except ImportError as e:
        return f"Error: DDSP not installed. Run: uv pip install ddsp tensorflow -e {e}"
    except Exception as e:
        return f"Error during timbre transfer: {str(e)}"


@mcp.tool()
async def analyze_pitch(
    input_path: str,
    output_path: Optional[str] = None,
) -> str:
    """Analyze pitch and loudness contours of an audio file.
    
    Args:
        input_path: Path to input audio file
        output_path: Optional path to save pitch contour data (JSON)
        
    Returns:
        JSON string with pitch analysis data
    """
    try:
        import librosa
        import numpy as np
        import json
        
        input_path = Path(input_path).expanduser().resolve()
        
        if not input_path.exists():
            return json.dumps({"error": f"Input file not found: {input_path}"}, indent=2)
        
        # Load audio
        audio, sr = librosa.load(str(input_path), sr=16000, mono=True)
        
        # Extract pitch using CREPE-like algorithm (librosa pyin)
        f0, voiced_flag, voiced_probs = librosa.pyin(
            audio, 
            fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C7')
        )
        
        # Calculate loudness (RMS)
        hop_length = 256
        rms = librosa.feature.rms(y=audio, hop_length=hop_length)[0]
        
        # Convert to dB
        loudness_db = 20 * np.log10(rms + 1e-10)
        
        # Prepare results
        times = librosa.times_like(f0, sr=sr, hop_length=hop_length)
        
        analysis = {
            "duration": float(len(audio) / sr),
            "sample_rate": sr,
            "pitch_contour": {
                "times": times.tolist(),
                "frequencies": [float(f) if f is not None else 0.0 for f in f0],
                "voiced": voiced_flag.tolist(),
            },
            "loudness_db": {
                "times": librosa.times_like(rms, sr=sr, hop_length=hop_length).tolist(),
                "values": loudness_db.tolist(),
            },
            "mean_pitch_hz": float(np.nanmean(f0[f0 > 0])) if np.any(f0 > 0) else 0,
            "pitch_range_hz": {
                "min": float(np.nanmin(f0[f0 > 0])) if np.any(f0 > 0) else 0,
                "max": float(np.nanmax(f0[f0 > 0])) if np.any(f0 > 0) else 0,
            }
        }
        
        # Save if output path provided
        if output_path:
            output_path = Path(output_path).expanduser().resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(analysis, f, indent=2)
        
        return json.dumps(analysis, indent=2)
        
    except ImportError as e:
        return json.dumps({"error": f"Missing dependencies: {e}"}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def download_model(
    model_name: str,
    url: Optional[str] = None,
) -> str:
    """Download a pre-trained DDSP model.
    
    Args:
        model_name: Name for the model (e.g., 'violin', 'flute')
        url: Direct download URL (optional, uses known models if not provided)
        
    Returns:
        Success message with model path
    """
    try:
        import urllib.request
        import zipfile
        import shutil
        
        # Known model URLs (from DDSP demo colab)
        known_models = {
            "violin": "https://storage.googleapis.com/ddsp/models/violin.zip",
            "flute": "https://storage.googleapis.com/ddsp/models/flute.zip",
            "tenor_sax": "https://storage.googleapis.com/ddsp/models/tenor_sax.zip",
            "trumpet": "https://storage.googleapis.com/ddsp/models/trumpet.zip",
        }
        
        if url is None and model_name in known_models:
            url = known_models[model_name]
        
        if url is None:
            return f"Error: No known URL for model '{model_name}'. Provide a custom URL."
        
        model_dir = DEFAULT_MODELS_DIR / model_name
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Download to temp file
        temp_zip = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
        temp_zip.close()
        
        try:
            urllib.request.urlretrieve(url, temp_zip.name)
            
            # Extract
            with zipfile.ZipFile(temp_zip.name, 'r') as zip_ref:
                zip_ref.extractall(str(model_dir))
            
            return f"Successfully downloaded model '{model_name}' to: {model_dir}"
            
        finally:
            os.unlink(temp_zip.name)
            
    except Exception as e:
        return f"Error downloading model: {str(e)}"


@mcp.tool()
async def batch_process(
    input_dir: str,
    output_dir: str,
    model_name: str = "violin",
    file_pattern: str = "*.wav",
) -> str:
    """Batch process multiple audio files with timbre transfer.
    
    Args:
        input_dir: Directory containing input audio files
        output_dir: Directory for output files
        model_name: DDSP model to use
        file_pattern: File glob pattern (default: "*.wav")
        
    Returns:
        Summary of processed files
    """
    try:
        input_path = Path(input_dir).expanduser().resolve()
        output_path = Path(output_dir).expanduser().resolve()
        
        if not input_path.exists():
            return f"Error: Input directory not found: {input_path}"
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Find files
        files = list(input_path.glob(file_pattern))
        
        if not files:
            return f"No files matching '{file_pattern}' found in {input_path}"
        
        results = []
        for input_file in files:
            output_file = output_path / f"{input_file.stem}_{model_name}{input_file.suffix}"
            result = await timbre_transfer(
                str(input_file),
                str(output_file),
                model_name=model_name
            )
            results.append({
                "input": str(input_file.name),
                "output": str(output_file.name),
                "status": "success" if "Successfully" in result else "error",
                "message": result
            })
        
        summary = {
            "total": len(files),
            "successful": sum(1 for r in results if r["status"] == "success"),
            "failed": sum(1 for r in results if r["status"] == "error"),
            "results": results
        }
        
        return json.dumps(summary, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


if __name__ == "__main__":
    # Create models directory if it doesn't exist
    DEFAULT_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    mcp.run(transport="stdio")
