#!/usr/bin/env python3
"""Local test of DDSP timbre transfer."""

import numpy as np
import soundfile as sf
import tensorflow as tf
import ddsp
from ddsp import synths, processors, core
from ddsp.training import preprocessing, decoders, models

# Model path
MODEL_DIR = "/tmp/ddsp_models/solo_violin_ckpt"


def build_model():
    """Build the DDSP autoencoder model manually."""
    # Based on the gin config and checkpoint variables
    
    # Preprocessor: F0LoudnessPreprocessor
    preprocessor = preprocessing.F0LoudnessPreprocessor(
        time_steps=1000,
        frame_rate=250,
        sample_rate=16000,
    )
    
    # Encoder: None (input is raw audio features)
    encoder = None
    
    # Decoder: RnnFcDecoder
    # From checkpoint: output dimension is 126 (likely 100 harmonics + 26 noise bins)
    decoder = decoders.RnnFcDecoder(
        rnn_channels=512,
        rnn_type='gru',
        ch=512,
        layers_per_stack=3,
        input_keys=('ld_scaled', 'f0_scaled'),
        output_splits=(('amps', 1), ('harmonic_distribution', 100), ('noise_magnitudes', 25)),
    )
    
    # Processor group: Harmonic + FilteredNoise + Add
    harmonic = synths.Harmonic(
        n_samples=64000,
        sample_rate=16000,
        scale_fn=core.exp_sigmoid,
        normalize_below_nyquist=True,
    )
    
    filtered_noise = synths.FilteredNoise(
        n_samples=64000,
        scale_fn=core.exp_sigmoid,
    )
    
    add = processors.Add(name='add')
    
    # Build the dag
    dag = [
        (harmonic, ['amps', 'harmonic_distribution', 'f0_hz']),
        (filtered_noise, ['noise_magnitudes']),
        (add, ['filtered_noise/signal', 'harmonic/signal']),
    ]
    
    processor_group = processors.ProcessorGroup(dag=dag, name='processor_group')
    
    # Create autoencoder
    model = models.Autoencoder(
        preprocessor=preprocessor,
        encoder=encoder,
        decoder=decoder,
        processor_group=processor_group,
    )
    
    return model


def test_audio_features():
    """Test audio feature extraction."""
    # Create a simple test audio
    sr = 16000
    duration = 4.0
    t = np.linspace(0, duration, int(sr * duration))
    audio = np.sin(2 * np.pi * 440 * t) * 0.3
    
    print(f"Test audio shape: {audio.shape}")
    
    # Compute features using spectral_ops directly
    audio_16k = ddsp.core.resample(audio, 16000) if sr != 16000 else audio
    
    # Compute loudness
    loudness_db = ddsp.spectral_ops.compute_loudness(
        audio_16k, sample_rate=16000, frame_rate=250
    )
    
    # Compute f0 (without viterbi for now due to hmmlearn version issues)
    f0_hz, f0_confidence = ddsp.spectral_ops.compute_f0(audio_16k, frame_rate=250, viterbi=False)
    
    features = {
        'audio': audio_16k,
        'loudness_db': loudness_db,
        'f0_hz': f0_hz,
        'f0_confidence': f0_confidence,
    }
    
    print(f"Features: {list(features.keys())}")
    for k, v in features.items():
        if hasattr(v, 'shape'):
            print(f"  {k}: {v.shape}")
    
    return features


if __name__ == "__main__":
    print("Testing DDSP local setup...")
    print(f"TensorFlow version: {tf.__version__}")
    print(f"DDSP version: {ddsp.__version__ if hasattr(ddsp, '__version__') else 'unknown'}")
    
    # Test feature extraction
    print("\n--- Testing audio feature extraction ---")
    features = test_audio_features()
    
    # Build and test model
    print("\n--- Building model ---")
    try:
        model = build_model()
        print("Model built successfully!")
        print(f"Model preprocessor: {model.preprocessor}")
        print(f"Model decoder: {model.decoder}")
        print(f"Model processor_group: {model.processor_group}")
    except Exception as e:
        print(f"Error building model: {e}")
        import traceback
        traceback.print_exc()
