"""MCP Server for SoX audio processing tools.

Provides tools for:
- Audio effects (reverb, chorus, flanger, pitch, tempo, etc.)
- Audio analysis (statistics, spectrograms)
- High-quality resampling and filtering
- Music production utilities
"""
from mcp.server.fastmcp import FastMCP
import subprocess
import os
from pathlib import Path
from typing import Optional, Literal
import json

# Initialize FastMCP server
mcp = FastMCP("sox")


def _run_sox(args: list[str]) -> tuple[bool, str]:
    """Run SoX command and return success status and output/error message."""
    try:
        result = subprocess.run(
            ["sox"] + args,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout or "Success"
    except subprocess.CalledProcessError as e:
        return False, f"SoX error: {e.stderr or e.stdout or str(e)}"
    except FileNotFoundError:
        return False, "SoX not found. Please install SoX: https://sox.sourceforge.net/"


@mcp.tool()
async def apply_reverb(
    input_path: str,
    output_path: str,
    reverberance: int = 50,
    room_scale: int = 100,
    pre_delay: int = 0,
    stereo_depth: int = 100,
) -> str:
    """Apply reverb effect to audio file.

    Args:
        input_path: Path to input audio file
        output_path: Path for output file
        reverberance: Percentage of reverberance (0-100)
        room_scale: Room scale percentage (0-100)
        pre_delay: Pre-delay in milliseconds (0-100)
        stereo_depth: Stereo depth percentage (0-100)

    Returns:
        Success message with output file path
    """
    try:
        input_path = Path(input_path).expanduser().resolve()
        output_path = Path(output_path).expanduser().resolve()

        if not input_path.exists():
            return f"Error: Input file not found: {input_path}"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        args = [
            str(input_path),
            str(output_path),
            "reverb",
            str(reverberance),
            str(room_scale),
            str(pre_delay),
            str(stereo_depth),
        ]

        success, msg = _run_sox(args)
        if success:
            return f"Successfully applied reverb to: {output_path}"
        return msg
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def apply_chorus(
    input_path: str,
    output_path: str,
    gain_in: float = 0.7,
    gain_out: float = 0.9,
    delays: str = "20 30 40",
    decays: str = "0.3 0.3 0.3",
    speeds: str = "0.4 0.5 0.6",
    depths: str = "2 2.5 3",
) -> str:
    """Apply chorus effect to audio file.

    Args:
        input_path: Path to input audio file
        output_path: Path for output file
        gain_in: Input gain (0.0-1.0)
        gain_out: Output gain (0.0-1.0)
        delays: Space-separated delay times in ms (e.g., "20 30 40")
        decays: Space-separated decay factors (e.g., "0.3 0.3 0.3")
        speeds: Space-separated modulation speeds in Hz (e.g., "0.4 0.5 0.6")
        depths: Space-separated modulation depths in ms (e.g., "2 2.5 3")

    Returns:
        Success message with output file path
    """
    try:
        input_path = Path(input_path).expanduser().resolve()
        output_path = Path(output_path).expanduser().resolve()

        if not input_path.exists():
            return f"Error: Input file not found: {input_path}"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        args = [
            str(input_path),
            str(output_path),
            "chorus",
            str(gain_in),
            str(gain_out),
        ]
        # Add voice parameters
        delays_list = delays.split()
        decays_list = decays.split()
        speeds_list = speeds.split()
        depths_list = depths.split()

        for i in range(len(delays_list)):
            args.extend([
                delays_list[i],
                decays_list[min(i, len(decays_list)-1)],
                speeds_list[min(i, len(speeds_list)-1)],
                depths_list[min(i, len(depths_list)-1)],
                "-s",  # Sine modulation
            ])

        success, msg = _run_sox(args)
        if success:
            return f"Successfully applied chorus to: {output_path}"
        return msg
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def apply_flanger(
    input_path: str,
    output_path: str,
    gain_in: float = 0.8,
    gain_out: float = 0.8,
    delay: float = 0,
    depth: float = 2,
    regen: float = 0.5,
    width: float = 0.5,
    speed: float = 0.5,
    shape: Literal["sine", "triangle"] = "sine",
    phase: float = 25,
) -> str:
    """Apply flanger effect to audio file.

    Args:
        input_path: Path to input audio file
        output_path: Path for output file
        gain_in: Input gain (0.0-1.0)
        gain_out: Output gain (0.0-1.0)
        delay: Base delay in ms (0-30)
        depth: Modulation depth in ms (0-30)
        regen: Regeneration percentage (-95 to 95)
        width: Delay line width percentage (0-100)
        speed: Modulation speed in Hz (0.1-10)
        shape: Modulation shape ('sine' or 'triangle')
        phase: Phase shift percentage (0-100)

    Returns:
        Success message with output file path
    """
    try:
        input_path = Path(input_path).expanduser().resolve()
        output_path = Path(output_path).expanduser().resolve()

        if not input_path.exists():
            return f"Error: Input file not found: {input_path}"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        args = [
            str(input_path),
            str(output_path),
            "flanger",
            str(gain_in),
            str(gain_out),
            str(delay),
            str(depth),
            str(regen),
            str(width),
            str(speed),
            shape,
            str(phase),
        ]

        success, msg = _run_sox(args)
        if success:
            return f"Successfully applied flanger to: {output_path}"
        return msg
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def change_pitch(
    input_path: str,
    output_path: str,
    cents: int = 0,
) -> str:
    """Change pitch of audio without affecting tempo.

    Args:
        input_path: Path to input audio file
        output_path: Path for output file
        cents: Pitch shift in cents (-1200 to +1200, where 100 cents = 1 semitone)

    Returns:
        Success message with output file path
    """
    try:
        input_path = Path(input_path).expanduser().resolve()
        output_path = Path(output_path).expanduser().resolve()

        if not input_path.exists():
            return f"Error: Input file not found: {input_path}"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        args = [
            str(input_path),
            str(output_path),
            "pitch",
            str(cents),
        ]

        success, msg = _run_sox(args)
        if success:
            return f"Successfully changed pitch to: {output_path}"
        return msg
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def change_tempo(
    input_path: str,
    output_path: str,
    factor: float = 1.0,
) -> str:
    """Change tempo of audio without affecting pitch.

    Args:
        input_path: Path to input audio file
        output_path: Path for output file
        factor: Tempo factor (0.5 = half speed, 2.0 = double speed)

    Returns:
        Success message with output file path
    """
    try:
        input_path = Path(input_path).expanduser().resolve()
        output_path = Path(output_path).expanduser().resolve()

        if not input_path.exists():
            return f"Error: Input file not found: {input_path}"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        args = [
            str(input_path),
            str(output_path),
            "tempo",
            str(factor),
        ]

        success, msg = _run_sox(args)
        if success:
            return f"Successfully changed tempo to: {output_path}"
        return msg
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def apply_compression(
    input_path: str,
    output_path: str,
    attack: float = 0.2,
    decay: float = 1.0,
    soft_knee_db: float = 2.0,
    threshold_db: float = -20.0,
    ratio: float = 2.0,
    gain_db: float = 0.0,
) -> str:
    """Apply dynamic range compression (compand) to audio.

    Args:
        input_path: Path to input audio file
        output_path: Path for output file
        attack: Attack time in seconds
        decay: Decay time in seconds
        soft_knee_db: Soft knee in dB
        threshold_db: Threshold in dB
        ratio: Compression ratio (e.g., 2.0 = 2:1)
        gain_db: Makeup gain in dB

    Returns:
        Success message with output file path
    """
    try:
        input_path = Path(input_path).expanduser().resolve()
        output_path = Path(output_path).expanduser().resolve()

        if not input_path.exists():
            return f"Error: Input file not found: {input_path}"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build transfer function
        # Format: attack,decay {threshold},{knee} {ratio} {gain}
        transfer = f"{attack},{decay} {threshold_db},{soft_knee_db} {ratio} {gain_db}"

        args = [
            str(input_path),
            str(output_path),
            "compand",
            transfer,
        ]

        success, msg = _run_sox(args)
        if success:
            return f"Successfully applied compression to: {output_path}"
        return msg
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def apply_filter(
    input_path: str,
    output_path: str,
    filter_type: Literal["lowpass", "highpass", "bandpass", "bandreject", "band", "treble", "bass"],
    frequency: float,
    width_q: float = 0.707,
    gain_db: Optional[float] = None,
) -> str:
    """Apply frequency filter to audio.

    Args:
        input_path: Path to input audio file
        output_path: Path for output file
        filter_type: Type of filter ('lowpass', 'highpass', 'bandpass', 'bandreject', 'band', 'treble', 'bass')
        frequency: Filter frequency in Hz
        width_q: Filter width in Q (bandwidth/center_freq, default 0.707)
        gain_db: Gain in dB (for 'treble' and 'bass' filters)

    Returns:
        Success message with output file path
    """
    try:
        input_path = Path(input_path).expanduser().resolve()
        output_path = Path(output_path).expanduser().resolve()

        if not input_path.exists():
            return f"Error: Input file not found: {input_path}"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        args = [
            str(input_path),
            str(output_path),
            filter_type,
            str(frequency),
        ]

        # Add gain for shelf filters
        if filter_type in ("treble", "bass") and gain_db is not None:
            args.append(str(gain_db))

        args.append(str(width_q))

        success, msg = _run_sox(args)
        if success:
            return f"Successfully applied {filter_type} filter to: {output_path}"
        return msg
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def add_silence(
    output_path: str,
    duration: float,
    sample_rate: int = 44100,
    channels: int = 2,
    bits: int = 16,
) -> str:
    """Generate a silent audio file.

    Args:
        output_path: Path for output file
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        channels: Number of channels (1 or 2)
        bits: Bit depth (8, 16, 24, 32)

    Returns:
        Success message with output file path
    """
    try:
        output_path = Path(output_path).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        args = [
            "-n",  # Null input (generate audio)
            "-r", str(sample_rate),
            "-c", str(channels),
            "-b", str(bits),
            str(output_path),
            "trim",
            "0.0",
            str(duration),
        ]

        success, msg = _run_sox(args)
        if success:
            return f"Successfully generated silence: {output_path}"
        return msg
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def pad_audio(
    input_path: str,
    output_path: str,
    start_pad: float = 0.0,
    end_pad: float = 0.0,
) -> str:
    """Add silence padding to beginning and/or end of audio.

    Args:
        input_path: Path to input audio file
        output_path: Path for output file
        start_pad: Seconds of silence to add at start
        end_pad: Seconds of silence to add at end

    Returns:
        Success message with output file path
    """
    try:
        input_path = Path(input_path).expanduser().resolve()
        output_path = Path(output_path).expanduser().resolve()

        if not input_path.exists():
            return f"Error: Input file not found: {input_path}"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        args = [
            str(input_path),
            str(output_path),
            "pad",
            str(start_pad),
            str(end_pad),
        ]

        success, msg = _run_sox(args)
        if success:
            return f"Successfully padded audio: {output_path}"
        return msg
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def resample_audio(
    input_path: str,
    output_path: str,
    sample_rate: int = 44100,
    quality: Literal["quick", "low", "medium", "high", "very high"] = "high",
) -> str:
    """Resample audio to a different sample rate with high quality.

    Args:
        input_path: Path to input audio file
        output_path: Path for output file
        sample_rate: Target sample rate in Hz
        quality: Resampling quality ('quick', 'low', 'medium', 'high', 'very high')

    Returns:
        Success message with output file path
    """
    try:
        input_path = Path(input_path).expanduser().resolve()
        output_path = Path(output_path).expanduser().resolve()

        if not input_path.exists():
            return f"Error: Input file not found: {input_path}"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        quality_flags = {
            "quick": "-q",
            "low": "-l",
            "medium": "-m",
            "high": "-h",
            "very high": "-v",
        }

        args = [
            str(input_path),
            "-r", str(sample_rate),
            quality_flags.get(quality, "-h"),
            str(output_path),
        ]

        success, msg = _run_sox(args)
        if success:
            return f"Successfully resampled to {sample_rate}Hz: {output_path}"
        return msg
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def reverse_audio(
    input_path: str,
    output_path: str,
) -> str:
    """Reverse audio file (play backwards).

    Args:
        input_path: Path to input audio file
        output_path: Path for output file

    Returns:
        Success message with output file path
    """
    try:
        input_path = Path(input_path).expanduser().resolve()
        output_path = Path(output_path).expanduser().resolve()

        if not input_path.exists():
            return f"Error: Input file not found: {input_path}"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        args = [
            str(input_path),
            str(output_path),
            "reverse",
        ]

        success, msg = _run_sox(args)
        if success:
            return f"Successfully reversed audio: {output_path}"
        return msg
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def get_audio_stats(
    file_path: str,
) -> str:
    """Get detailed statistics about an audio file.

    Args:
        file_path: Path to audio file

    Returns:
        JSON string with audio statistics
    """
    try:
        file_path = Path(file_path).expanduser().resolve()

        if not file_path.exists():
            return f"Error: File not found: {file_path}"

        # Run sox stat
        args = [
            str(file_path),
            "-n",
            "stat",
        ]

        success, msg = _run_sox(args)
        if not success:
            return msg

        # Parse stat output
        stats = {}
        for line in msg.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()
                try:
                    # Try to convert to number
                    if "." in value:
                        stats[key] = float(value)
                    else:
                        stats[key] = int(value)
                except ValueError:
                    stats[key] = value

        # Also get format info
        info_args = [
            "--info",
            str(file_path),
        ]
        info_success, info_msg = _run_sox(info_args)

        result = {
            "statistics": stats,
            "format_info": info_msg if info_success else None,
        }

        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def generate_spectrogram(
    input_path: str,
    output_path: str,
    width: int = 800,
    height: int = 300,
    window: Literal["Hann", "Hamming", "Bartlett", "Rectangular", "Kaiser"] = "Hann",
) -> str:
    """Generate spectrogram image from audio file.

    Args:
        input_path: Path to input audio file
        output_path: Path for output PNG image
        width: Image width in pixels
        height: Image height in pixels
        window: Window function for FFT

    Returns:
        Success message with output file path
    """
    try:
        input_path = Path(input_path).expanduser().resolve()
        output_path = Path(output_path).expanduser().resolve()

        if not input_path.exists():
            return f"Error: Input file not found: {input_path}"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure output has .png extension
        if not str(output_path).lower().endswith(".png"):
            output_path = output_path.with_suffix(".png")

        args = [
            str(input_path),
            "-n",
            "spectrogram",
            "-x", str(width),
            "-y", str(height),
            "-w", window,
            "-o", str(output_path),
        ]

        success, msg = _run_sox(args)
        if success:
            return f"Successfully generated spectrogram: {output_path}"
        return msg
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def normalize_audio(
    input_path: str,
    output_path: str,
    level: float = -0.1,
) -> str:
    """Normalize audio to a specified level (prevent clipping).

    Args:
        input_path: Path to input audio file
        output_path: Path for output file
        level: Target peak level in dB (e.g., -0.1 for -0.1dB, negative values prevent clipping)

    Returns:
        Success message with output file path
    """
    try:
        input_path = Path(input_path).expanduser().resolve()
        output_path = Path(output_path).expanduser().resolve()

        if not input_path.exists():
            return f"Error: Input file not found: {input_path}"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        args = [
            str(input_path),
            str(output_path),
            "gain",
            "-n",  # Normalize
            str(level),
        ]

        success, msg = _run_sox(args)
        if success:
            return f"Successfully normalized audio: {output_path}"
        return msg
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def remove_silence(
    input_path: str,
    output_path: str,
    threshold: float = 1.0,
    min_silence_duration: float = 0.5,
    keep_silence_duration: float = 0.0,
) -> str:
    """Remove silence from audio file.

    Args:
        input_path: Path to input audio file
        output_path: Path for output file
        threshold: Silence threshold in percentage (0-100)
        min_silence_duration: Minimum silence duration to remove in seconds
        keep_silence_duration: Amount of silence to keep at start/end of removed sections

    Returns:
        Success message with output file path
    """
    try:
        input_path = Path(input_path).expanduser().resolve()
        output_path = Path(output_path).expanduser().resolve()

        if not input_path.exists():
            return f"Error: Input file not found: {input_path}"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        args = [
            str(input_path),
            str(output_path),
            "silence",
            "1",  # Remove from beginning
            str(min_silence_duration),
            str(threshold) + "%",
            "-1",  # Remove from end
            str(min_silence_duration),
            str(threshold) + "%",
        ]

        success, msg = _run_sox(args)
        if success:
            return f"Successfully removed silence: {output_path}"
        return msg
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def concatenate_audio(
    file_list: list[str],
    output_path: str,
    crossfade: Optional[float] = None,
) -> str:
    """Concatenate multiple audio files with optional crossfade.

    Args:
        file_list: List of input file paths to concatenate
        output_path: Path for output file
        crossfade: Crossfade duration in seconds (optional)

    Returns:
        Success message with output file path
    """
    try:
        output_path = Path(output_path).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Resolve all input paths
        resolved_files = []
        for f in file_list:
            p = Path(f).expanduser().resolve()
            if not p.exists():
                return f"Error: Input file not found: {p}"
            resolved_files.append(str(p))

        if crossfade and len(resolved_files) > 1:
            # Use crossfade for smooth transitions
            # This requires a more complex approach with splice
            args = resolved_files[0:1] + [str(output_path)]
            for f in resolved_files[1:]:
                args.extend([f, "splice", f"-{crossfade}"])
        else:
            # Simple concatenation
            args = resolved_files + [str(output_path)]

        success, msg = _run_sox(args)
        if success:
            return f"Successfully concatenated to: {output_path}"
        return msg
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def convert_format(
    input_path: str,
    output_path: str,
    encoding: Optional[str] = None,
    bits: Optional[int] = None,
) -> str:
    """Convert audio file format with SoX (high quality).

    Args:
        input_path: Path to input audio file
        output_path: Path for output file
        encoding: Encoding type (e.g., 'signed-integer', 'floating-point', 'mu-law', 'a-law')
        bits: Bit depth (8, 16, 24, 32, 64)

    Returns:
        Success message with output file path
    """
    try:
        input_path = Path(input_path).expanduser().resolve()
        output_path = Path(output_path).expanduser().resolve()

        if not input_path.exists():
            return f"Error: Input file not found: {input_path}"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        args = [str(input_path)]

        if encoding:
            args.extend(["-e", encoding])
        if bits:
            args.extend(["-b", str(bits)])

        args.append(str(output_path))

        success, msg = _run_sox(args)
        if success:
            return f"Successfully converted to: {output_path}"
        return msg
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
