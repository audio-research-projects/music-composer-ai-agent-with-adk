"""MCP Server for FFmpeg audio/video processing tools.

Provides tools for:
- Transcoding between formats and codecs
- Light linear editing (trim, cut, concatenate, mix)
"""
from mcp.server.fastmcp import FastMCP
import ffmpeg
import os
from pathlib import Path
from typing import Optional

# Initialize FastMCP server
mcp = FastMCP("ffmpeg")


@mcp.tool()
async def transcode_media(
    input_path: str,
    output_path: str,
    video_codec: Optional[str] = None,
    audio_codec: Optional[str] = None,
    video_bitrate: Optional[str] = None,
    audio_bitrate: Optional[str] = None,
    resolution: Optional[str] = None,
    frame_rate: Optional[int] = None,
    audio_sample_rate: Optional[int] = None,
    audio_channels: Optional[int] = None,
) -> str:
    """Transcode media file to a different format or codec.

    Args:
        input_path: Path to input media file
        output_path: Path for output file (extension determines format)
        video_codec: Video codec (e.g., 'libx264', 'libx265', 'vp9', 'copy')
        audio_codec: Audio codec (e.g., 'aac', 'mp3', 'libopus', 'flac', 'copy')
        video_bitrate: Video bitrate (e.g., '1M', '500k')
        audio_bitrate: Audio bitrate (e.g., '128k', '192k')
        resolution: Output resolution (e.g., '1920x1080', '1280x720')
        frame_rate: Output frame rate (e.g., 30, 60)
        audio_sample_rate: Audio sample rate in Hz (e.g., 44100, 48000)
        audio_channels: Number of audio channels (e.g., 1, 2, 6)

    Returns:
        Success message with output file path
    """
    try:
        input_path = Path(input_path).expanduser().resolve()
        output_path = Path(output_path).expanduser().resolve()

        if not input_path.exists():
            return f"Error: Input file not found: {input_path}"

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        stream = ffmpeg.input(str(input_path))
        output_args = {"y": None}  # Overwrite output

        if video_codec:
            output_args["vcodec"] = video_codec
        if audio_codec:
            output_args["acodec"] = audio_codec
        if video_bitrate:
            output_args["video_bitrate"] = video_bitrate
        if audio_bitrate:
            output_args["audio_bitrate"] = audio_bitrate
        if resolution:
            output_args["vf"] = f"scale={resolution.replace('x', ':')}"
        if frame_rate:
            output_args["r"] = frame_rate
        if audio_sample_rate:
            output_args["ar"] = audio_sample_rate
        if audio_channels:
            output_args["ac"] = audio_channels

        stream = stream.output(str(output_path), **output_args)
        stream.run(quiet=True)

        return f"Successfully transcoded to: {output_path}"
    except ffmpeg.Error as e:
        stderr = e.stderr.decode() if e.stderr else str(e)
        return f"FFmpeg error: {stderr}"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def trim_media(
    input_path: str,
    output_path: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    duration: Optional[str] = None,
) -> str:
    """Trim media file by specifying start/end times or duration.

    Args:
        input_path: Path to input media file
        output_path: Path for output file
        start_time: Start time (e.g., '00:00:10', '10', '00:01:30.500')
        end_time: End time (e.g., '00:00:30', '30')
        duration: Duration from start (e.g., '00:00:20', '20', alternative to end_time)

    Returns:
        Success message with output file path
    """
    try:
        input_path = Path(input_path).expanduser().resolve()
        output_path = Path(output_path).expanduser().resolve()

        if not input_path.exists():
            return f"Error: Input file not found: {input_path}"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        input_args = {}
        if start_time:
            input_args["ss"] = start_time
        if end_time:
            input_args["to"] = end_time
        if duration and not end_time:
            input_args["t"] = duration

        stream = ffmpeg.input(str(input_path), **input_args)
        stream = stream.output(str(output_path), y=None, c="copy")
        stream.run(quiet=True)

        return f"Successfully trimmed to: {output_path}"
    except ffmpeg.Error as e:
        stderr = e.stderr.decode() if e.stderr else str(e)
        return f"FFmpeg error: {stderr}"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def concatenate_media(
    file_list: list[str],
    output_path: str,
    file_with_list: Optional[str] = None,
) -> str:
    """Concatenate multiple media files into one.

    Args:
        file_list: List of input file paths to concatenate
        output_path: Path for output concatenated file
        file_with_list: Optional path to a text file containing list of files (one per line)

    Returns:
        Success message with output file path
    """
    try:
        output_path = Path(output_path).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # If a file list is provided, read it
        if file_with_list:
            list_path = Path(file_with_list).expanduser().resolve()
            with open(list_path, "r") as f:
                file_list = [line.strip() for line in f if line.strip()]

        # Resolve all input paths
        resolved_files = []
        for f in file_list:
            p = Path(f).expanduser().resolve()
            if not p.exists():
                return f"Error: Input file not found: {p}"
            resolved_files.append(str(p))

        # Create concat demuxer file list
        concat_list_path = output_path.parent / "_concat_list_.txt"
        with open(concat_list_path, "w") as f:
            for file_path in resolved_files:
                f.write(f"file '{file_path}'\n")

        try:
            stream = ffmpeg.input(str(concat_list_path), f="concat", safe=0)
            stream = stream.output(str(output_path), c="copy", y=None)
            stream.run(quiet=True)
        finally:
            # Clean up temp file
            if concat_list_path.exists():
                concat_list_path.unlink()

        return f"Successfully concatenated to: {output_path}"
    except ffmpeg.Error as e:
        stderr = e.stderr.decode() if e.stderr else str(e)
        return f"FFmpeg error: {stderr}"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def mix_audio_tracks(
    input_paths: list[str],
    output_path: str,
    normalize: bool = False,
) -> str:
    """Mix multiple audio files into one (overlay/mix).

    Args:
        input_paths: List of audio file paths to mix
        output_path: Path for output mixed file
        normalize: Whether to normalize audio levels

    Returns:
        Success message with output file path
    """
    try:
        output_path = Path(output_path).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        inputs = []
        for input_path in input_paths:
            p = Path(input_path).expanduser().resolve()
            if not p.exists():
                return f"Error: Input file not found: {p}"
            inputs.append(ffmpeg.input(str(p)))

        # Mix all inputs
        mixed = ffmpeg.filter(inputs, "amix", inputs=len(inputs), duration="first")

        if normalize:
            mixed = ffmpeg.filter(mixed, "loudnorm")

        stream = mixed.output(str(output_path), y=None)
        stream.run(quiet=True)

        return f"Successfully mixed to: {output_path}"
    except ffmpeg.Error as e:
        stderr = e.stderr.decode() if e.stderr else str(e)
        return f"FFmpeg error: {stderr}"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def extract_audio(
    video_path: str,
    output_path: str,
    audio_codec: str = "flac",
    sample_rate: int = 44100,
    channels: int = 2,
) -> str:
    """Extract audio track from video file.

    Args:
        video_path: Path to input video file
        output_path: Path for output audio file
        audio_codec: Audio codec (e.g., 'flac', 'wav', 'mp3', 'aac')
        sample_rate: Output sample rate in Hz
        channels: Number of audio channels

    Returns:
        Success message with output file path
    """
    try:
        video_path = Path(video_path).expanduser().resolve()
        output_path = Path(output_path).expanduser().resolve()

        if not video_path.exists():
            return f"Error: Input file not found: {video_path}"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        stream = ffmpeg.input(str(video_path))
        stream = stream.output(
            str(output_path),
            vn=None,  # No video
            acodec=audio_codec,
            ar=sample_rate,
            ac=channels,
            y=None,
        )
        stream.run(quiet=True)

        return f"Successfully extracted audio to: {output_path}"
    except ffmpeg.Error as e:
        stderr = e.stderr.decode() if e.stderr else str(e)
        return f"FFmpeg error: {stderr}"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def get_media_info(file_path: str) -> str:
    """Get information about a media file (duration, codecs, bitrate, etc.).

    Args:
        file_path: Path to media file

    Returns:
        JSON string with media information
    """
    try:
        file_path = Path(file_path).expanduser().resolve()

        if not file_path.exists():
            return f"Error: File not found: {file_path}"

        probe = ffmpeg.probe(str(file_path))

        # Extract key information
        format_info = probe.get("format", {})
        streams = probe.get("streams", [])

        info = {
            "filename": format_info.get("filename"),
            "duration": float(format_info.get("duration", 0)),
            "size": int(format_info.get("size", 0)),
            "bitrate": int(format_info.get("bit_rate", 0)),
            "format_name": format_info.get("format_name"),
            "streams": [],
        }

        for stream in streams:
            stream_info = {
                "index": stream.get("index"),
                "codec_type": stream.get("codec_type"),
                "codec_name": stream.get("codec_name"),
            }

            if stream.get("codec_type") == "video":
                stream_info.update({
                    "width": stream.get("width"),
                    "height": stream.get("height"),
                    "fps": eval(stream.get("r_frame_rate", "0/1")),  # Convert fraction to float
                })
            elif stream.get("codec_type") == "audio":
                stream_info.update({
                    "sample_rate": int(stream.get("sample_rate", 0)),
                    "channels": stream.get("channels"),
                    "channel_layout": stream.get("channel_layout"),
                })

            info["streams"].append(stream_info)

        import json
        return json.dumps(info, indent=2)
    except ffmpeg.Error as e:
        stderr = e.stderr.decode() if e.stderr else str(e)
        return f"FFmpeg error: {stderr}"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def adjust_volume(
    input_path: str,
    output_path: str,
    volume_db: float = 0.0,
    normalize: bool = False,
) -> str:
    """Adjust volume of an audio file.

    Args:
        input_path: Path to input audio file
        output_path: Path for output file
        volume_db: Volume adjustment in dB (positive or negative, e.g., -6.0, 3.0)
        normalize: Normalize audio to standard loudness (EBU R128)

    Returns:
        Success message with output file path
    """
    try:
        input_path = Path(input_path).expanduser().resolve()
        output_path = Path(output_path).expanduser().resolve()

        if not input_path.exists():
            return f"Error: Input file not found: {input_path}"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        stream = ffmpeg.input(str(input_path))

        if normalize:
            stream = stream.filter("loudnorm")
        elif volume_db != 0.0:
            volume_multiplier = 10 ** (volume_db / 20)
            stream = stream.filter("volume", volume_multiplier)

        stream = stream.output(str(output_path), y=None)
        stream.run(quiet=True)

        return f"Successfully adjusted volume to: {output_path}"
    except ffmpeg.Error as e:
        stderr = e.stderr.decode() if e.stderr else str(e)
        return f"FFmpeg error: {stderr}"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def fade_audio(
    input_path: str,
    output_path: str,
    fade_in_duration: Optional[str] = None,
    fade_out_duration: Optional[str] = None,
    fade_out_start: Optional[str] = None,
) -> str:
    """Apply fade in/out to audio file.

    Args:
        input_path: Path to input audio file
        output_path: Path for output file
        fade_in_duration: Fade in duration (e.g., '3', '00:00:03')
        fade_out_duration: Fade out duration (e.g., '3', '00:00:03')
        fade_out_start: When to start fade out (e.g., '00:01:00', auto-calculated if not set)

    Returns:
        Success message with output file path
    """
    try:
        input_path = Path(input_path).expanduser().resolve()
        output_path = Path(output_path).expanduser().resolve()

        if not input_path.exists():
            return f"Error: Input file not found: {input_path}"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Get duration first
        probe = ffmpeg.probe(str(input_path))
        duration = float(probe["format"]["duration"])

        stream = ffmpeg.input(str(input_path))

        if fade_in_duration:
            # Convert to seconds if in time format
            if ":" in fade_in_duration:
                parts = fade_in_duration.split(":")
                fade_in_sec = sum(float(x) * 60 ** i for i, x in enumerate(reversed(parts)))
            else:
                fade_in_sec = float(fade_in_duration)
            stream = stream.filter("afade", type="in", start_time=0, duration=fade_in_sec)

        if fade_out_duration:
            # Convert to seconds if in time format
            if ":" in fade_out_duration:
                parts = fade_out_duration.split(":")
                fade_out_sec = sum(float(x) * 60 ** i for i, x in enumerate(reversed(parts)))
            else:
                fade_out_sec = float(fade_out_duration)

            if fade_out_start:
                if ":" in fade_out_start:
                    parts = fade_out_start.split(":")
                    start_sec = sum(float(x) * 60 ** i for i, x in enumerate(reversed(parts)))
                else:
                    start_sec = float(fade_out_start)
            else:
                start_sec = duration - fade_out_sec

            stream = stream.filter("afade", type="out", start_time=start_sec, duration=fade_out_sec)

        stream = stream.output(str(output_path), y=None)
        stream.run(quiet=True)

        return f"Successfully applied fades to: {output_path}"
    except ffmpeg.Error as e:
        stderr = e.stderr.decode() if e.stderr else str(e)
        return f"FFmpeg error: {stderr}"
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
