#!/usr/bin/env python3
"""Download pre-trained DDSP models for local testing.

Usage:
    python download_models.py --model violin
    python download_models.py --all
    python download_models.py --list
"""
import argparse
import urllib.request
import zipfile
from pathlib import Path
from tqdm import tqdm
import os

# Known pre-trained model URLs from Google Magenta
KNOWN_MODELS = {
    "violin": "https://storage.googleapis.com/ddsp/models/violin.zip",
    "flute": "https://storage.googleapis.com/ddsp/models/flute.zip",
    "tenor_sax": "https://storage.googleapis.com/ddsp/models/tenor_sax.zip",
    "trumpet": "https://storage.googleapis.com/ddsp/models/trumpet.zip",
    "flute2": "https://storage.googleapis.com/ddsp/models/flute2.zip",
}

DEFAULT_MODELS_DIR = Path(__file__).parent / "models"


class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)


def download_file(url: str, dest: Path) -> None:
    """Download a file with progress bar."""
    print(f"Downloading {url}...")
    with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc=dest.name) as t:
        urllib.request.urlretrieve(url, str(dest), reporthook=t.update_to)


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


def list_models(models_dir: Path = DEFAULT_MODELS_DIR) -> None:
    """List available and downloaded models."""
    print("\nAvailable models:")
    print("-" * 40)
    for name, url in KNOWN_MODELS.items():
        print(f"  {name:15} {url}")
    
    print("\nDownloaded models:")
    print("-" * 40)
    
    if models_dir.exists():
        downloaded = [d.name for d in models_dir.iterdir() if d.is_dir()]
        if downloaded:
            for name in sorted(downloaded):
                model_path = models_dir / name
                size = sum(f.stat().st_size for f in model_path.rglob('*') if f.is_file())
                size_mb = size / 1024 / 1024
                print(f"  {name:15} {size_mb:6.1f} MB")
        else:
            print("  None")
    else:
        print("  None")
    
    print()


def main():
    parser = argparse.ArgumentParser(description="Download DDSP models for local testing")
    parser.add_argument("--model", choices=list(KNOWN_MODELS.keys()), help="Download a specific model")
    parser.add_argument("--all", action="store_true", help="Download all available models")
    parser.add_argument("--list", action="store_true", help="List models")
    parser.add_argument("--force", action="store_true", help="Re-download even if exists")
    parser.add_argument("--dir", type=Path, default=DEFAULT_MODELS_DIR, help=f"Models directory (default: {DEFAULT_MODELS_DIR})")
    
    args = parser.parse_args()
    
    if args.list:
        list_models(args.dir)
        return
    
    if args.model:
        download_model(args.model, args.dir, args.force)
    elif args.all:
        print("Downloading all models...")
        success = 0
        for model_name in KNOWN_MODELS.keys():
            print()
            if download_model(model_name, args.dir, args.force):
                success += 1
        print(f"\nDownloaded {success}/{len(KNOWN_MODELS)} models")
    else:
        parser.print_help()
        print("\nExample: python download_models.py --model violin")


if __name__ == "__main__":
    main()
