#!/usr/bin/env python3
"""Test local DDSP setup.

Usage:
    python test_local.py
"""
import sys
from pathlib import Path


def test_imports():
    """Test that all required packages can be imported."""
    print("Testing imports...")
    errors = []
    
    try:
        import tensorflow as tf
        print(f"  ✓ TensorFlow {tf.__version__}")
    except ImportError as e:
        print(f"  ✗ TensorFlow: {e}")
        errors.append("tensorflow")
    
    try:
        import tensorflow_probability as tfp
        print(f"  ✓ TensorFlow Probability {tfp.__version__}")
    except ImportError as e:
        print(f"  ✗ TensorFlow Probability: {e}")
        errors.append("tensorflow-probability")
    
    try:
        import ddsp
        print(f"  ✓ DDSP {ddsp.__version__}")
    except ImportError as e:
        print(f"  ✗ DDSP: {e}")
        errors.append("ddsp")
    
    try:
        import librosa
        print(f"  ✓ librosa {librosa.__version__}")
    except ImportError as e:
        print(f"  ✗ librosa: {e}")
        errors.append("librosa")
    
    try:
        import soundfile as sf
        print(f"  ✓ soundfile")
    except ImportError as e:
        print(f"  ✗ soundfile: {e}")
        errors.append("soundfile")
    
    try:
        import numpy as np
        print(f"  ✓ numpy {np.__version__}")
    except ImportError as e:
        print(f"  ✗ numpy: {e}")
        errors.append("numpy")
    
    if errors:
        print(f"\nMissing packages: {', '.join(errors)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    print("\n✓ All imports successful")
    return True


def test_models_dir():
    """Test models directory."""
    print("\nTesting models directory...")
    models_dir = Path(__file__).parent / "models"
    
    if not models_dir.exists():
        print(f"  Creating {models_dir}")
        models_dir.mkdir(exist_ok=True)
    
    models = [d.name for d in models_dir.iterdir() if d.is_dir()]
    
    if models:
        print(f"  ✓ Found {len(models)} models: {', '.join(models)}")
    else:
        print(f"  ⚠ No models found in {models_dir}")
        print("    Download with: python download_models.py --model violin")
    
    return True


def test_create_audio():
    """Create test audio file."""
    print("\nCreating test audio...")
    
    try:
        import soundfile as sf
        import numpy as np
        
        # Generate 5 seconds of 440Hz sine wave
        sr = 16000
        duration = 5
        t = np.linspace(0, duration, int(sr * duration))
        audio = 0.5 * np.sin(2 * np.pi * 440 * t)
        
        output_path = Path(__file__).parent / "input" / "test_tone.wav"
        output_path.parent.mkdir(exist_ok=True)
        sf.write(str(output_path), audio, sr)
        
        print(f"  ✓ Created {output_path}")
        return output_path
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None


def main():
    print("=" * 50)
    print("Local DDSP Test Suite")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed")
        return 1
    
    # Test models directory
    test_models_dir()
    
    # Create test audio
    test_audio = test_create_audio()
    
    print("\n" + "=" * 50)
    print("Setup complete!")
    print("=" * 50)
    
    if test_audio:
        print(f"\nNext steps:")
        print(f"  1. Download a model: python download_models.py --model violin")
        print(f"  2. Test transfer: python timbre_transfer.py {test_audio} --model violin")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
