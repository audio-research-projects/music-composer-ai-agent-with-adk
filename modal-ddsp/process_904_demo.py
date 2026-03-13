#!/usr/bin/env python3
"""Process first 3 chunks of 904.mp3 with DDSP."""

import os
import subprocess
from pathlib import Path
import modal
from modal_app import app, timbre_transfer

CHUNKS_DIR = Path("904_chunks")
OUTPUT_DIR = Path("904_output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Process only first 3 chunks
chunks = sorted(CHUNKS_DIR.glob("904_chunk_*.mp3"))[:3]

print(f"Processing {len(chunks)} chunks...\n")

with app.run():
    for i, chunk_mp3 in enumerate(chunks):
        chunk_num = chunk_mp3.stem.split('_')[-1]
        print(f"=== Chunk {chunk_num} ({i+1}/{len(chunks)}) ===")
        
        # Convert to WAV (16kHz mono)
        chunk_wav = OUTPUT_DIR / f"904_{chunk_num}_original.wav"
        subprocess.run([
            "ffmpeg", "-i", str(chunk_mp3), "-ar", "16000", "-ac", "1",
            "-y", str(chunk_wav)
        ], capture_output=True)
        
        # Read and process
        with open(chunk_wav, "rb") as f:
            audio_data = f.read()
        
        print(f"  Input: {len(audio_data)} bytes, processing...")
        
        result = timbre_transfer.remote(
            audio_data=audio_data,
            model_name="violin",
            pitch_shift=0.0,
            loudness_db_shift=0.0,
        )
        
        if result["status"] == "success":
            # Save violin
            violin_wav = OUTPUT_DIR / f"904_{chunk_num}_violin.wav"
            with open(violin_wav, "wb") as f:
                f.write(result["output_audio"])
            
            # Create stereo mix
            stereo_wav = OUTPUT_DIR / f"904_{chunk_num}_stereo.wav"
            subprocess.run([
                "sox", "-M", str(chunk_wav), str(violin_wav), str(stereo_wav)
            ], capture_output=True)
            
            print(f"  ✅ Done: {stereo_wav.name}")
        else:
            print(f"  ❌ Error: {result.get('error', 'Unknown')}")

print("\n✅ Demo complete!")
