#!/usr/bin/env python3
"""Test script for Modal DDSP timbre transfer.

Usage:
    python test_transfer.py input.wav --model violin --output output.wav
    python test_transfer.py input.wav --model tenor_sax --pitch-shift 2
"""
import argparse
import modal
from pathlib import Path

APP_NAME = "ddsp-timbre-transfer"


def get_function(name: str):
    """Get a Modal function by name using the current API."""
    # Use modal.Function.from_name for newer API
    try:
        return modal.Function.from_name(APP_NAME, name)
    except Exception:
        # Fallback for older versions
        return modal.Function.lookup(APP_NAME, name)


def test_list_models():
    """Test listing models."""
    print("\n=== Testing list_models ===")
    try:
        f = get_function("list_models")
        result = f.remote()
        print(f"Available: {result.get('available_models')}")
        print(f"Downloaded: {result.get('downloaded_models')}")
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure the app is deployed: modal deploy modal_app.py")
        return {"available_models": [], "downloaded_models": []}


def test_download_model(model_name: str):
    """Test downloading a model."""
    print(f"\n=== Testing download_model: {model_name} ===")
    try:
        f = get_function("download_model")
        result = f.remote(model_name)
        print(f"Status: {result.get('status')}")
        if result.get('error'):
            print(f"Error: {result.get('error')}")
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"status": "error", "error": str(e)}


def test_timbre_transfer(input_path: Path, model: str, output_path: Path, pitch_shift: float = 0.0):
    """Test timbre transfer on an audio file."""
    print(f"\n=== Testing timbre_transfer ===")
    print(f"Input: {input_path}")
    print(f"Model: {model}")
    print(f"Pitch shift: {pitch_shift}")
    
    # Read input file
    audio_bytes = input_path.read_bytes()
    print(f"Input size: {len(audio_bytes)} bytes")
    
    try:
        # Call Modal function
        f = get_function("timbre_transfer")
        result = f.remote(
            audio_data=audio_bytes,
            model_name=model,
            pitch_shift=pitch_shift,
            loudness_db_shift=0.0,
        )
        
        if result.get('status') == 'error':
            print(f"❌ Error: {result.get('error')}")
            if result.get('traceback'):
                print(f"Traceback:\n{result.get('traceback')}")
            return False
        
        # Save output
        output_path.write_bytes(result['output_audio'])
        print(f"✅ Success!")
        print(f"  Duration: {result.get('duration_seconds', 0):.2f}s")
        print(f"  Output: {output_path}")
        print(f"  Output size: {len(result['output_audio'])} bytes")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_analyze_audio(input_path: Path):
    """Test audio analysis."""
    print(f"\n=== Testing analyze_audio ===")
    
    audio_bytes = input_path.read_bytes()
    
    try:
        f = get_function("analyze_audio")
        result = f.remote(audio_bytes)
        
        if result.get('status') == 'success':
            print(f"✅ Analysis complete:")
            print(f"  Duration: {result.get('duration', 0):.2f}s")
            pitch = result.get('pitch', {})
            print(f"  Pitch: {pitch.get('mean_hz', 0):.1f} Hz")
            print(f"  Range: {pitch.get('min_hz', 0):.1f} - {pitch.get('max_hz', 0):.1f} Hz")
        else:
            print(f"❌ Error: {result.get('error')}")
        
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"status": "error", "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Test Modal DDSP deployment")
    parser.add_argument("input", nargs="?", help="Input audio file")
    parser.add_argument("--model", default="violin", 
                       choices=["violin", "flute", "tenor_sax", "trumpet", "flute2"],
                       help="Model to use")
    parser.add_argument("--output", default="output.wav", help="Output file")
    parser.add_argument("--pitch-shift", type=float, default=0.0, help="Pitch shift in semitones")
    parser.add_argument("--list", action="store_true", help="List models only")
    parser.add_argument("--download", metavar="MODEL", help="Download a model")
    parser.add_argument("--analyze", action="store_true", help="Also run analysis")
    
    args = parser.parse_args()
    
    # Test list models
    models = test_list_models()
    
    if args.list:
        return
    
    # Download model if requested
    if args.download:
        test_download_model(args.download)
        return
    
    # Check if input file provided
    if not args.input:
        print("\nNo input file provided. Use --help for usage.")
        print("\nTo create a test audio file:")
        print("  sox -n -r 16000 -c 1 test_input.wav synth 5 sine 440")
        return
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Input file not found: {input_path}")
        return
    
    # Check if model is downloaded
    if args.model not in models.get('downloaded_models', []):
        print(f"\nModel '{args.model}' not downloaded. Downloading...")
        test_download_model(args.model)
    
    # Test timbre transfer
    output_path = Path(args.output)
    success = test_timbre_transfer(input_path, args.model, output_path, args.pitch_shift)
    
    # Optionally test analysis
    if success and args.analyze:
        test_analyze_audio(input_path)


if __name__ == "__main__":
    main()
