#!/usr/bin/env python3
"""Debug script to check model files on Modal.

Usage:
    modal run modal_app::debug_model_info --model-name violin
"""
import modal

app = modal.App("ddsp-debug")

# Use same image as main app
image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install("libsndfile1", "ffmpeg", "wget", "unzip")
    .pip_install(
        "tensorflow==2.11.1",
        "tensorflow-probability==0.19.0",
        "numpy==1.23.5",
    )
)

models_volume = modal.Volume.from_name("ddsp-models")


@app.function(
    image=image,
    volumes={"/models": models_volume},
)
def debug_model_info(model_name: str = "violin") -> dict:
    """Debug info about model files."""
    from pathlib import Path
    import tensorflow as tf
    
    model_dir = Path("/models") / model_name
    
    result = {
        "model_name": model_name,
        "model_dir": str(model_dir),
        "exists": model_dir.exists(),
        "files": [],
        "checkpoint": None,
    }
    
    if model_dir.exists():
        # List all files
        for f in sorted(model_dir.rglob("*")):
            if f.is_file():
                size = f.stat().st_size
                result["files"].append({
                    "path": str(f.relative_to(model_dir)),
                    "size": size,
                })
        
        # Check for checkpoint
        checkpoint = tf.train.latest_checkpoint(str(model_dir))
        result["checkpoint"] = checkpoint
        
        # Check parent directory (in case files are nested)
        parent = model_dir.parent
        result["parent_files"] = [f.name for f in parent.iterdir() if f.is_dir()]
    
    return result


@app.local_entrypoint()
def main(model_name: str = "violin"):
    """Run debug from local CLI."""
    import json
    result = debug_model_info.remote(model_name)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
