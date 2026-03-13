#!/usr/bin/env python3
"""Process 904.mp3 chunks with DDSP and create stereo mixes."""

import os
import subprocess
from pathlib import Path
import modal
from modal_app import app, timbre_transfer

CHUNKS_DIR = Path("904_chunks")
OUTPUT_DIR = Path("904_output")
OUTPUT_DIR.mkdir(exist_ok=True)

def convert_to_wav(mp3_path, wav_path):
    """Convert MP3 to 16kHz mono WAV."""
    subprocess.run([
        "ffmpeg", "-i", str(mp3_path),
        "-ar", "16000", "-ac", "1",
        "-y", str(wav_path)
    ], capture_output=True)
    return wav_path.exists()

def create_stereo_mix(original_wav, violin_wav, output_wav):
    """Create stereo mix with original L and violin R."""
    subprocess.run([
        "sox", "-M",
        str(original_wav), str(violin_wav),
        str(output_wav)
    ], capture_output=True)
    return output_wav.exists()

# Get all chunks
chunks = sorted(CHUNKS_DIR.glob("904_chunk_*.mp3"))
print(f"Found {len(chunks)} chunks to process\n")

# Process each chunk
for i, chunk_mp3 in enumerate(chunks):
    chunk_num = chunk_mp3.stem.split('_')[-1]
    print(f"=== Processing chunk {chunk_num} ({i+1}/{len(chunks)}) ===")
    
    # Convert to WAV
    chunk_wav = OUTPUT_DIR / f"904_{chunk_num}_original.wav"
    if not convert_to_wav(chunk_mp3, chunk_wav):
        print(f"❌ Failed to convert {chunk_mp3}")
        continue
    
    # Read audio data
    with open(chunk_wav, "rb") as f:
        audio_data = f.read()
    
    print(f"  Input: {len(audio_data)} bytes")
    
    # Process with DDSP
    try:
        with app.run():
            result = timbre_transfer.remote(
                audio_data=audio_data,
                model_name="violin",
                pitch_shift=0.0,
                loudness_db_shift=0.0,
            )
            
            if result["status"] == "success":
                # Save violin version
                violin_wav = OUTPUT_DIR / f"904_{chunk_num}_violin.wav"
                with open(violin_wav, "wb") as f:
                    f.write(result["output_audio"])
                print(f"  ✅ DDSP: {len(result['output_audio'])} bytes")
                
                # Create stereo mix
                stereo_wav = OUTPUT_DIR / f"904_{chunk_num}_stereo.wav"
                if create_stereo_mix(chunk_wav, violin_wav, stereo_wav):
                    print(f"  ✅ Stereo mix: {stereo_wav.name}")
                else:
                    print(f"  ❌ Failed to create stereo mix")
            else:
                print(f"  ❌ DDSP error: {result.get('error', 'Unknown')}")
    except Exception as e:
        print(f"  ❌ Exception: {e}")

print(f"\n✅ All chunks processed!")
print(f"Output files in: {OUTPUT_DIR}")
