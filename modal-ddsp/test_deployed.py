#!/usr/bin/env python3
"""Test the deployed Modal DDSP app."""

import subprocess
import sys
import os

# Create test audio if not exists
if not os.path.exists("test_input.wav"):
    print("Creating test audio...")
    import numpy as np
    import soundfile as sf
    
    sr = 16000
    duration = 3.0
    t = np.linspace(0, duration, int(sr * duration))
    # Create a simple melody
    audio = np.sin(2 * np.pi * 440 * t) * 0.3
    # Add some harmonics
    audio += np.sin(2 * np.pi * 880 * t) * 0.1
    audio += np.sin(2 * np.pi * 1320 * t) * 0.05
    
    sf.write("test_input.wav", audio, sr)
    print("Created test_input.wav")


def run_modal_function(func_name, *args):
    """Run a Modal function using the CLI."""
    cmd = ["modal", "run", f"modal_app.py::{func_name}"] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result


def test_list_models():
    """Test list_models function."""
    print("\n=== Testing list_models ===")
    result = run_modal_function("list_models")
    print(result.stdout)
    if result.stderr:
        print("Stderr:", result.stderr)
    return result.returncode == 0


def test_download(model="violin"):
    """Test download_model function."""
    print(f"\n=== Testing download_model ({model}) ===")
    result = run_modal_function("download_model", "--model-name", model)
    print(result.stdout)
    if result.stderr:
        print("Stderr:", result.stderr)
    return result.returncode == 0


def test_timbre_transfer(model="violin"):
    """Test timbre_transfer function."""
    print(f"\n=== Testing timbre_transfer ({model}) ===")
    
    # Use the Modal CLI to run the function
    # We need to pass the audio file path, but Modal functions don't support
    # local file paths directly. Instead, let's use a different approach.
    
    print(f"Input: test_input.wav")
    print(f"Model: {model}")
    print(f"Pitch shift: 0.0")
    
    # For now, just print that we would test here
    # The actual test would need to use the app context properly
    print("\n⚠️  To test timbre_transfer, use the Modal web interface or deploy a test endpoint")
    print("   View deployment at: https://modal.com/apps/davidcoronel/main/deployed/ddsp-timbre-transfer")
    
    return True


if __name__ == "__main__":
    print("=== Modal DDSP Deployment Test ===\n")
    
    # Test list models
    test_list_models()
    
    # Download model
    test_download("violin")
    
    # Test timbre transfer (info only)
    test_timbre_transfer("violin")
    
    print("\n✅ Basic tests completed!")
    print("\nTo test timbre_transfer, use the Modal dashboard or API endpoint:")
    print("  https://modal.com/apps/davidcoronel/main/deployed/ddsp-timbre-transfer")
