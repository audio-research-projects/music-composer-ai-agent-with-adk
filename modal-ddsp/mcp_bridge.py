"""MCP Server bridge for Modal-hosted DDSP.

This MCP server provides tools that call the Modal-hosted DDSP functions,
allowing the local ADK agent to use remote GPU-powered timbre transfer.

Usage:
    uv run mcp_bridge.py
    
Environment:
    MODAL_TOKEN_ID: Modal token ID for authentication
    MODAL_TOKEN_SECRET: Modal token secret
    MODAL_APP_NAME: Name of the deployed Modal app (default: "ddsp-timbre-transfer")
"""
from mcp.server.fastmcp import FastMCP
import modal
import os
from pathlib import Path
from typing import Optional
import tempfile
import base64

# Initialize FastMCP server
mcp = FastMCP("ddsp-modal")

# Modal app configuration
MODAL_APP_NAME = os.environ.get("MODAL_APP_NAME", "ddsp-timbre-transfer")


def _get_modal_app():
    """Get reference to deployed Modal app."""
    try:
        # Lookup deployed app
        app = modal.lookup(MODAL_APP_NAME)
        return app
    except Exception as e:
        raise RuntimeError(f"Could not connect to Modal app '{MODAL_APP_NAME}'. "
                          f"Make sure it's deployed: modal deploy modal_app.py. Error: {e}")


@mcp.tool()
async def list_models() -> str:
    """List available DDSP models on Modal.
    
    Returns:
        JSON string with available and downloaded models
    """
    try:
        import json
        
        # Get the Modal function
        f = modal.Function.lookup(MODAL_APP_NAME, "list_models")
        result = f.remote()
        
        return json.dumps(result, indent=2)
    except Exception as e:
        import json
        return json.dumps({
            "status": "error",
            "error": str(e),
            "hint": "Make sure Modal app is deployed: modal deploy modal_app.py"
        }, indent=2)


@mcp.tool()
async def download_model(model_name: str) -> str:
    """Download a pre-trained DDSP model to Modal's persistent storage.
    
    Args:
        model_name: Model name (violin, flute, tenor_sax, trumpet, flute2)
        
    Returns:
        Success message or error
    """
    try:
        f = modal.Function.lookup(MODAL_APP_NAME, "download_model")
        result = f.remote(model_name)
        
        if result["status"] == "success":
            return f"Model '{model_name}' downloaded successfully to Modal storage."
        elif result["status"] == "exists":
            return f"Model '{model_name}' is already cached on Modal."
        else:
            return f"Error: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        return f"Error downloading model: {str(e)}"


@mcp.tool()
async def timbre_transfer(
    input_path: str,
    output_path: str,
    model_name: str = "violin",
    pitch_shift: float = 0.0,
    loudness_db_shift: float = 0.0,
) -> str:
    """Apply timbre transfer to an audio file using Modal's GPU.
    
    Transforms the input audio to sound like a different instrument
    while preserving the original pitch and timing.
    
    Args:
        input_path: Path to local input audio file
        output_path: Path for local output file
        model_name: Target instrument (violin, flute, tenor_sax, trumpet)
        pitch_shift: Pitch shift in semitones (-12 to +12)
        loudness_db_shift: Loudness adjustment in dB (-20 to +20)
        
    Returns:
        Success message with output path
    """
    try:
        from pathlib import Path
        
        input_file = Path(input_path).expanduser().resolve()
        output_file = Path(output_path).expanduser().resolve()
        
        if not input_file.exists():
            return f"Error: Input file not found: {input_file}"
        
        # Read input file
        audio_bytes = input_file.read_bytes()
        
        # Validate size (Modal has payload limits)
        if len(audio_bytes) > 10 * 1024 * 1024:
            return "Error: File too large. Maximum 10MB allowed."
        
        # Call Modal function
        f = modal.Function.lookup(MODAL_APP_NAME, "timbre_transfer")
        result = f.remote(
            audio_data=audio_bytes,
            model_name=model_name,
            pitch_shift=pitch_shift,
            loudness_db_shift=loudness_db_shift,
        )
        
        if result["status"] == "error":
            return f"Error: {result.get('error', 'Unknown error')}"
        
        # Write output
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_bytes(result["output_audio"])
        
        return (f"Successfully applied timbre transfer ({model_name}).\n"
                f"Output: {output_file}\n"
                f"Duration: {result['duration_seconds']:.2f}s")
        
    except Exception as e:
        return f"Error during timbre transfer: {str(e)}"


@mcp.tool()
async def batch_transfer(
    input_dir: str,
    output_dir: str,
    model_name: str = "violin",
    file_pattern: str = "*.wav",
) -> str:
    """Batch process multiple audio files with timbre transfer.
    
    Args:
        input_dir: Directory containing input files
        output_dir: Directory for output files
        model_name: DDSP model to use
        file_pattern: File glob pattern (default: "*.wav")
        
    Returns:
        Summary of processed files
    """
    try:
        from pathlib import Path
        import json
        
        input_path = Path(input_dir).expanduser().resolve()
        output_path = Path(output_dir).expanduser().resolve()
        
        if not input_path.exists():
            return f"Error: Input directory not found: {input_path}"
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Find files
        files = list(input_path.glob(file_pattern))
        if not files:
            return f"No files matching '{file_pattern}' in {input_path}"
        
        results = []
        for input_file in files:
            output_file = output_path / f"{input_file.stem}_{model_name}{input_file.suffix}"
            
            result = await timbre_transfer(
                str(input_file),
                str(output_file),
                model_name
            )
            results.append(f"{input_file.name}: {result.split(chr(10))[0]}")
        
        return f"Processed {len(files)} files:\n" + "\n".join(results)
        
    except Exception as e:
        return f"Error in batch processing: {str(e)}"


@mcp.tool()
async def analyze_pitch(
    input_path: str,
) -> str:
    """Analyze pitch and loudness of an audio file.
    
    Args:
        input_path: Path to audio file
        
    Returns:
        JSON analysis results
    """
    try:
        from pathlib import Path
        import json
        
        input_file = Path(input_path).expanduser().resolve()
        
        if not input_file.exists():
            return json.dumps({"error": f"File not found: {input_file}"}, indent=2)
        
        audio_bytes = input_file.read_bytes()
        
        if len(audio_bytes) > 10 * 1024 * 1024:
            return json.dumps({"error": "File too large. Max 10MB."}, indent=2)
        
        f = modal.Function.lookup(MODAL_APP_NAME, "analyze_audio")
        result = f.remote(audio_bytes)
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        import json
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def get_api_endpoint() -> str:
    """Get the web API endpoint URL for direct HTTP access.
    
    Returns:
        The Modal web endpoint URL
    """
    try:
        # Try to get the web endpoint
        f = modal.Function.lookup(MODAL_APP_NAME, "api_timbre_transfer")
        # Note: Modal doesn't expose URL directly, but we can construct it
        # or the user can get it from: modal app show ddsp-timbre-transfer
        return ("API endpoint available. Run 'modal app show ddsp-timbre-transfer' "
                "to get the exact URL, or check your Modal dashboard.")
    except Exception as e:
        return f"Could not get API endpoint: {e}"


@mcp.tool()
async def check_modal_status() -> str:
    """Check if Modal app is deployed and accessible.
    
    Returns:
        Status message
    """
    try:
        result = await list_models()
        if "error" in result.lower() and "not found" in result.lower():
            return ("Modal app not deployed.\n"
                   "Run: modal deploy modal_app.py")
        return f"Modal app is online.\n{result}"
    except Exception as e:
        return f"Modal connection failed: {e}"


if __name__ == "__main__":
    print("Starting DDSP Modal MCP Bridge...")
    print("Make sure you have:")
    print("  1. Modal token configured (modal token new)")
    print("  2. Modal app deployed (modal deploy modal_app.py)")
    print("\nConnecting to Modal app:", MODAL_APP_NAME)
    
    try:
        import asyncio
        status = asyncio.run(check_modal_status())
        print(f"\nStatus: {status}")
    except Exception as e:
        print(f"\nWarning: Could not connect to Modal: {e}")
    
    print("\nStarting MCP server...")
    mcp.run(transport="stdio")
