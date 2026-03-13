#!/usr/bin/env python3
"""Process 904.wav chunks with DDSP and create stereo mixes."""

import subprocess
from pathlib import Path
import modal
from modal_app import app, timbre_transfer

CHUNKS_DIR = Path("904_chunks")
OUTPUT_DIR = Path("904_output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Process first 3 chunks
chunks = sorted(CHUNKS_DIR.glob("904_*.wav"))[:3]

print(f"Processing {len(chunks)} chunks of 15s each (pitch: -1 octave)...\n")

with app.run():
    for i, chunk_wav in enumerate(chunks):
        chunk_num = chunk_wav.stem.split('_')[-1]
        print(f"=== Chunk {chunk_num} ({i+1}/{len(chunks)}) ===")
        
        # Read audio
        with open(chunk_wav, "rb") as f:
            audio_data = f.read()
        
        print(f"  Input: {len(audio_data)} bytes ({len(audio_data)/2/16000:.2f}s)")
        
        # Process with DDSP (one octave down = -12 semitones)
        result = timbre_transfer.remote(
            audio_data=audio_data,
            model_name="violin",
            pitch_shift=-12.0,  # One octave down
            loudness_db_shift=0.0,
        )
        
        if result["status"] == "success":
            # Save outputs
            orig_out = OUTPUT_DIR / f"904_{chunk_num}_original.wav"
            violin_out = OUTPUT_DIR / f"904_{chunk_num}_violin_down1oct.wav"
            stereo_out = OUTPUT_DIR / f"904_{chunk_num}_stereo_down1oct.wav"
            
            # Copy original
            subprocess.run(["cp", str(chunk_wav), str(orig_out)])
            
            # Save violin
            with open(violin_out, "wb") as f:
                f.write(result["output_audio"])
            
            # Create stereo mix (original L, violin R)
            subprocess.run([
                "sox", "-M", str(orig_out), str(violin_out), str(stereo_out)
            ], capture_output=True)
            
            # Verify
            info = subprocess.run(
                ["soxi", str(stereo_out)],
                capture_output=True, text=True
            )
            duration = [l for l in info.stdout.split('\n') if 'Duration' in l]
            print(f"  ✅ Stereo: {stereo_out.name}")
            if duration:
                print(f"     {duration[0]}")
        else:
            print(f"  ❌ Error: {result.get('error', 'Unknown')[:100]}")

print("\n✅ Done! Files in 904_output/")
