#!/usr/bin/env python3
"""Full end-to-end test of Modal DDSP timbre transfer."""

import modal
import os

# Create test audio if not exists
if not os.path.exists("test_input.wav"):
    print("Creating test audio...")
    import numpy as np
    import soundfile as sf
    
    sr = 16000
    duration = 3.0
    t = np.linspace(0, duration, int(sr * duration))
    audio = np.sin(2 * np.pi * 440 * t) * 0.3
    audio += np.sin(2 * np.pi * 880 * t) * 0.1
    sf.write("test_input.wav", audio, sr)
    print("Created test_input.wav")

# Read test audio
with open("test_input.wav", "rb") as f:
    audio_data = f.read()

print(f"Input audio: {len(audio_data)} bytes")

# Import the Modal app
from modal_app import app, timbre_transfer, download_model, list_models

# Run tests within the app context
with app.run():
    # List models
    print("\n=== Listing models ===")
    result = list_models.remote()
    print(f"Available: {result.get('available', [])}")
    print(f"Downloaded: {result.get('downloaded', [])}")
    
    # Download violin model
    print("\n=== Downloading violin model ===")
    result = download_model.remote("violin")
    print(f"Status: {result.get('status')}")
    
    # Test timbre transfer
    print("\n=== Testing timbre_transfer ===")
    result = timbre_transfer.remote(
        audio_data=audio_data,
        model_name="violin",
        pitch_shift=0.0,
        loudness_db_shift=0.0,
    )
    
    if result["status"] == "success":
        print(f"✅ Success!")
        print(f"  Model: {result['model_name']}")
        print(f"  Duration: {result['duration_seconds']:.2f}s")
        print(f"  Output size: {len(result['output_audio'])} bytes")
        
        # Save output
        with open("test_output_violin.wav", "wb") as f:
            f.write(result["output_audio"])
        print(f"  Saved to: test_output_violin.wav")
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
        if 'traceback' in result:
            print(f"\nTraceback:\n{result['traceback'][:2000]}")

print("\n✅ Test completed!")
