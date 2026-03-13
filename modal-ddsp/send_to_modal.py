#!/usr/bin/env python3
"""Send audio clip to Modal DDSP for timbre transfer."""

import modal
from modal_app import app, timbre_transfer

# Read the 4s clip (model is trained for 4-second audio)
with open("433_clip_4s.wav", "rb") as f:
    audio_data = f.read()

print(f"Sending {len(audio_data)} bytes (4s audio at 16kHz) to Modal DDSP...")
print("Converting to violin...")

# Send to Modal
with app.run():
    result = timbre_transfer.remote(
        audio_data=audio_data,
        model_name="violin",
        pitch_shift=0.0,
        loudness_db_shift=0.0,
    )
    
    if result["status"] == "success":
        print(f"\n✅ Success!")
        print(f"  Model: {result['model_name']}")
        print(f"  Duration: {result['duration_seconds']:.2f}s")
        print(f"  Output size: {len(result['output_audio'])} bytes")
        
        # Save output
        output_path = "433_clip_4s_violin.wav"
        with open(output_path, "wb") as f:
            f.write(result["output_audio"])
        print(f"\n🎵 Saved violin version to: {output_path}")
    else:
        print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
        if 'traceback' in result:
            print(f"\nTraceback:\n{result['traceback'][:2000]}")
