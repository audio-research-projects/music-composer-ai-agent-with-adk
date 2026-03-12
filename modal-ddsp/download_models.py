"""Download and manage DDSP models for Modal deployment.

This script downloads pre-trained DDSP models from Google's storage
and prepares them for Modal deployment.

Usage:
    # Download all models
    python download_models.py --all
    
    # Download specific model
    python download_models.py --model violin
    
    # List available models
    python download_models.py --list
    
    # Upload to Modal volume
    python download_models.py --upload violin
"""
import argparse
import urllib.request
import zipfile
from pathlib import Path
import os
import sys

# Known pre-trained model URLs from Google Magenta
KNOWN_MODELS = {
    "violin": "https://storage.googleapis.com/ddsp/models/violin.zip",
    "flute": "https://storage.googleapis.com/ddsp/models/flute.zip",
    "tenor_sax": "https://storage.googleapis.com/ddsp/models/tenor_sax.zip",
    "trumpet": "https://storage.googleapis.com/ddsp/models/trumpet.zip",
    "flute2": "https://storage.googleapis.com/ddsp/models/flute2.zip",
}

DEFAULT_MODELS_DIR = Path(__file__).parent / "models"


def download_file(url: str, dest: Path, chunk_size: int = 8192) -> None:
    """Download a file with progress."""
    print(f"Downloading {url}...")
    
    def report_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(downloaded * 100 / total_size, 100)
        mb = downloaded / 1024 / 1024
        total_mb = total_mb / 1024 / 1024
        print(f"\r  Progress: {percent:.1f}% ({mb:.1f}/{total_mb:.1f} MB)", end="", flush=True)
    
    urllib.request.urlretrieve(url, str(dest), reporthook=report_progress)
    print()  # New line after progress


def download_model(model_name: str, models_dir: Path = DEFAULT_MODELS_DIR, force: bool = False) -> bool:
    """Download a specific model.
    
    Args:
        model_name: Name of the model
        models_dir: Directory to save models
        force: Re-download even if exists
        
    Returns:
        True if successful
    """
    if model_name not in KNOWN_MODELS:
        print(f"Error: Unknown model '{model_name}'")
        print(f"Available: {list(KNOWN_MODELS.keys())}")
        return False
    
    model_dir = models_dir / model_name
    
    if model_dir.exists() and not force:
        print(f"Model '{model_name}' already exists at {model_dir}")
        print("Use --force to re-download")
        return True
    
    model_dir.mkdir(parents=True, exist_ok=True)
    url = KNOWN_MODELS[model_name]
    zip_path = model_dir / "model.zip"
    
    try:
        # Download
        download_file(url, zip_path)
        
        # Extract
        print(f"Extracting to {model_dir}...")
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(str(model_dir))
        
        # Clean up
        zip_path.unlink()
        
        print(f"✓ Model '{model_name}' ready at {model_dir}")
        
        # List contents
        files = list(model_dir.iterdir())
        print(f"  Contents: {[f.name for f in files]}")
        
        return True
        
    except Exception as e:
        print(f"Error downloading {model_name}: {e}")
        return False


def upload_to_modal(model_name: str, models_dir: Path = DEFAULT_MODELS_DIR) -> bool:
    """Upload a model to Modal's persistent volume.
    
    Requires Modal CLI to be installed and authenticated.
    """
    import subprocess
    
    model_path = models_dir / model_name
    
    if not model_path.exists():
        print(f"Error: Model not found at {model_path}")
        print("Download it first with: python download_models.py --model " + model_name)
        return False
    
    print(f"Uploading {model_name} to Modal volume...")
    
    try:
        result = subprocess.run(
            ["modal", "volume", "put", "ddsp-models", str(model_path), f"/models/{model_name}"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✓ Uploaded successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error uploading: {e}")
        print(f"stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print("Error: 'modal' CLI not found. Install with: pip install modal")
        return False


def list_local_models(models_dir: Path = DEFAULT_MODELS_DIR) -> None:
    """List downloaded models."""
    print("\nLocal models:")
    print("-" * 40)
    
    if not models_dir.exists():
        print("No models directory found")
        return
    
    found = False
    for model_dir in sorted(models_dir.iterdir()):
        if model_dir.is_dir():
            found = True
            size = sum(f.stat().st_size for f in model_dir.rglob('*') if f.is_file())
            size_mb = size / 1024 / 1024
            print(f"  {model_dir.name:15} {size_mb:6.1f} MB")
    
    if not found:
        print("  No models downloaded")
    
    print()


def list_available() -> None:
    """List available models from Google."""
    print("\nAvailable models:")
    print("-" * 40)
    
    for name, url in KNOWN_MODELS.items():
        size = "~50-150 MB"  # Approximate
        print(f"  {name:15} {size}")
    
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Download and manage DDSP models"
    )
    parser.add_argument(
        "--model",
        choices=list(KNOWN_MODELS.keys()),
        help="Download a specific model"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Download all available models"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List local models"
    )
    parser.add_argument(
        "--available",
        action="store_true",
        help="List available models"
    )
    parser.add_argument(
        "--upload",
        metavar="MODEL",
        help="Upload a model to Modal volume"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if exists"
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=DEFAULT_MODELS_DIR,
        help=f"Models directory (default: {DEFAULT_MODELS_DIR})"
    )
    
    args = parser.parse_args()
    
    # Default action if no args
    if not any([args.model, args.all, args.list, args.available, args.upload]):
        parser.print_help()
        return
    
    # Execute actions
    if args.available:
        list_available()
    
    if args.list:
        list_local_models(args.dir)
    
    if args.model:
        download_model(args.model, args.dir, args.force)
    
    if args.all:
        print("Downloading all models...")
        success = 0
        for model_name in KNOWN_MODELS.keys():
            if download_model(model_name, args.dir, args.force):
                success += 1
            print()
        print(f"Downloaded {success}/{len(KNOWN_MODELS)} models")
    
    if args.upload:
        upload_to_modal(args.upload, args.dir)


if __name__ == "__main__":
    main()
