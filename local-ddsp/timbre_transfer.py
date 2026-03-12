#!/usr/bin/env python3
"""Local DDSP Timbre Transfer.

Run timbre transfer locally using pre-trained DDSP models.

Usage:
    # Transfer audio to violin
    python timbre_transfer.py input.wav --model violin --output output.wav
    
    # With pitch shift
    python timbre_transfer.py input.wav --model flute --pitch-shift 2 --output output.wav
    
    # Adjust loudness
    python timbre_transfer.py input.wav --model tenor_sax --loudness-db 3 --output output.wav

Requirements:
    pip install -r requirements.txt
"""
import argparse
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Reduce TF logging

import tensorflow as tf
import librosa
import soundfile as sf
import numpy as np
import ddsp
import ddsp.training
from pathlib import Path
import time


def timbre_transfer(
    input_path: Path,
    output_path: Path,
    model_path: Path,
    pitch_shift: float = 0.0,
    loudness_db_shift: float = 0.0,
    sample_rate: int = 16000,
) -> dict:
    """Apply timbre transfer to audio file.
    
    Args:
        input_path: Input audio file
        output_path: Output audio file
        model_path: Path to DDSP model directory
        pitch_shift: Pitch shift in semitones
        loudness_db_shift: Loudness adjustment in dB
        sample_rate: Target sample rate
        
    Returns:
        Dict with status and metadata
    """
    start_time = time.time()
    
    # Load audio
    print(f"Loading audio from {input_path}...")
    audio, sr = librosa.load(str(input_path), sr=sample_rate, mono=True)
    duration = len(audio) / sr
    print(f"  Duration: {duration:.2f}s, Sample rate: {sr}Hz")
    
    # Find checkpoint
    print(f"Loading model from {model_path}...")
    checkpoint = tf.train.latest_checkpoint(str(model_path))
    if checkpoint is None:
        raise ValueError(f"No checkpoint found in {model_path}")
    print(f"  Checkpoint: {checkpoint}")
    
    # Load gin config if exists
    gin_file = model_path / "operative_config-0.gin"
    if gin_file.exists():
        print(f"  Loading gin config...")
        ddsp.training.metrics.gin_parse(str(gin_file))
    
    # Create and restore model
    print("Building model...")
    model = ddsp.training.models.Autoencoder()
    model.restore(checkpoint)
    print("  Model restored")
    
    # Prepare features
    print("Computing audio features...")
    features = {
        'audio': audio,
        'sample_rate': sr,
    }
    features = ddsp.training.metrics.compute_audio_features(features)
    
    # Apply shifts
    if pitch_shift != 0:
        features['f0_hz'] = features['f0_hz'] * (2 ** (pitch_shift / 12))
        print(f"  Pitch shift: {pitch_shift:+} semitones")
    
    if loudness_db_shift != 0:
        features['loudness_db'] = features['loudness_db'] + loudness_db_shift
        print(f"  Loudness shift: {loudness_db_shift:+} dB")
    
    # Run inference
    print("Running inference...")
    outputs = model(features, training=False)
    audio_gen = outputs['audio_synth'].numpy()
    
    # Save output
    print(f"Saving to {output_path}...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), audio_gen, sr)
    
    elapsed = time.time() - start_time
    print(f"✓ Done in {elapsed:.1f}s")
    
    return {
        'status': 'success',
        'input_duration': duration,
        'output_path': str(output_path),
        'elapsed_seconds': elapsed,
        'pitch_shift': pitch_shift,
        'loudness_db_shift': loudness_db_shift,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Local DDSP Timbre Transfer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.wav --model violin
  %(prog)s input.wav --model flute --pitch-shift -2
  %(prog)s input.wav --model tenor_sax --output jazz_sax.wav
        """
    )
    parser.add_argument("input", type=Path, help="Input audio file")
    parser.add_argument("--model", default="violin",
                       choices=["violin", "flute", "tenor_sax", "trumpet", "flute2"],
                       help="Model to use (default: violin)")
    parser.add_argument("--model-path", type=Path, 
                       help="Custom model path (overrides --model)")
    parser.add_argument("--output", "-o", type=Path, 
                       help="Output file (default: input_MODEL.wav)")
    parser.add_argument("--pitch-shift", type=float, default=0.0,
                       help="Pitch shift in semitones (default: 0)")
    parser.add_argument("--loudness-db", type=float, default=0.0,
                       help="Loudness adjustment in dB (default: 0)")
    parser.add_argument("--sample-rate", type=int, default=16000,
                       help="Sample rate (default: 16000)")
    parser.add_argument("--models-dir", type=Path, default=Path(__file__).parent / "models",
                       help="Models directory")
    
    args = parser.parse_args()
    
    # Validate input
    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}")
        return 1
    
    # Determine model path
    if args.model_path:
        model_path = args.model_path
    else:
        model_path = args.models_dir / args.model
    
    if not model_path.exists():
        print(f"Error: Model not found: {model_path}")
        print(f"Download it with: python download_models.py --model {args.model}")
        return 1
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        output_path = args.input.parent / f"{args.input.stem}_{args.model}{args.input.suffix}"
    
    # Run timbre transfer
    try:
        result = timbre_transfer(
            input_path=args.input,
            output_path=output_path,
            model_path=model_path,
            pitch_shift=args.pitch_shift,
            loudness_db_shift=args.loudness_db,
            sample_rate=args.sample_rate,
        )
        print(f"\nOutput saved to: {result['output_path']}")
        return 0
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
