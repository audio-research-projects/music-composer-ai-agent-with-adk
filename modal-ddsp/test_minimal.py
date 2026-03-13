#!/usr/bin/env python3
"""Minimal test of Modal DDSP timbre transfer."""

import modal
from modal_app import app, timbre_transfer
import numpy as np
import soundfile as sf
import io

# Create test audio
sr = 16000
duration = 1.0  # Short 1 second audio
t = np.linspace(0, duration, int(sr * duration))
audio = np.sin(2 * np.pi * 440 * t) * 0.3

# Save to bytes
buffer = io.BytesIO()
sf.write(buffer, audio, sr, format='WAV')
audio_data = buffer.getvalue()

print(f"Test audio: {len(audio_data)} bytes, {duration}s")

# Test with app context
with app.run():
    print("\nCalling timbre_transfer...")
    try:
        result = timbre_transfer.remote(
            audio_data=audio_data,
            model_name="violin",
            pitch_shift=0.0,
            loudness_db_shift=0.0,
        )
        print(f"Result status: {result.get('status')}")
        if result['status'] == 'success':
            print(f"✅ Success!")
            print(f"  Output size: {len(result['output_audio'])} bytes")
        else:
            print(f"❌ Error: {result.get('error')}")
            if 'traceback' in result:
                print(f"Traceback:\n{result['traceback'][:2000]}")
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()
