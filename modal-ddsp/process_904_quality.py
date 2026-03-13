#!/usr/bin/env python3
"""Process 904.mp3 with quality-optimized settings."""

import subprocess
import numpy as np
import librosa
import soundfile as sf
import io
from pathlib import Path
import modal
from modal_app import app, timbre_transfer

CHUNKS_DIR = Path("904_chunks")
OUTPUT_DIR = Path("904_output_quality")
OUTPUT_DIR.mkdir(exist_ok=True)

# Quality settings
SETTINGS = {
    "natural": {"pitch": -1.0, "loudness": 0.0, "desc": "Natural with slight detune"},
    "deep": {"pitch": -12.0, "loudness": 3.0, "desc": "Deep bass violin"},
    "bright": {"pitch": 7.0, "loudness": -1.0, "desc": "Bright, ethereal"},
    "subtle": {"pitch": -5.0, "loudness": 2.0, "desc": "Subtle lower shift"},
}

def normalize_audio(audio, target_db=-18.0):
    """Normalize audio to target dB."""
    # Calculate current RMS
    rms = np.sqrt(np.mean(audio**2))
    current_db = 20 * np.log10(rms + 1e-10)
    
    # Calculate gain needed
    gain_db = target_db - current_db
    gain_linear = 10 ** (gain_db / 20)
    
    # Apply gain with headroom
    audio_normalized = audio * gain_linear * 0.8
    
    # Soft clip to prevent hard clipping
    audio_normalized = np.tanh(audio_normalized)
    
    return audio_normalized

# Process first 2 chunks with different settings
chunks = sorted(CHUNKS_DIR.glob("904_*.wav"))[:2]

print(f"Processing {len(chunks)} chunks with {len(SETTINGS)} quality settings...\n")

with app.run():
    for chunk_wav in chunks:
        chunk_num = chunk_wav.stem.split('_')[-1]
        
        # Load and preprocess
        audio, sr = librosa.load(chunk_wav, sr=16000, mono=True)
        
        # Normalize
        audio = normalize_audio(audio, target_db=-18.0)
        
        # Trim silence
        audio, _ = librosa.effects.trim(audio, top_db=20)
        
        # Ensure exact 15s (pad if needed)
        target_samples = 15 * 16000
        if len(audio) < target_samples:
            audio = np.pad(audio, (0, target_samples - len(audio)), mode='constant')
        else:
            audio = audio[:target_samples]
        
        # Save processed input
        sf.write(chunk_wav, audio, 16000)
        
        print(f"\n=== Chunk {chunk_num} ({len(audio)/16000:.2f}s) ===")
        
        for setting_name, params in SETTINGS.items():
            print(f"  Processing: {setting_name} - {params['desc']}")
            
            # Convert to bytes
            buffer = io.BytesIO()
            sf.write(buffer, audio, 16000, format='WAV')
            audio_data = buffer.getvalue()
            
            # Process with DDSP
            result = timbre_transfer.remote(
                audio_data=audio_data,
                model_name="violin",
                pitch_shift=params["pitch"],
                loudness_db_shift=params["loudness"],
            )
            
            if result["status"] == "success":
                # Save with descriptive name
                output_name = f"904_{chunk_num}_{setting_name}_p{int(params['pitch'])}_l{int(params['loudness'])}.wav"
                output_path = OUTPUT_DIR / output_name
                
                with open(output_path, "wb") as f:
                    f.write(result["output_audio"])
                
                print(f"    ✅ Saved: {output_name}")
            else:
                print(f"    ❌ Error: {result.get('error', 'Unknown')[:80]}")

print("\n✅ Quality comparison complete!")
print(f"Files in: {OUTPUT_DIR}")
