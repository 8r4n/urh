"""
Model Context Protocol (MCP) server for Universal Radio Hacker.

Exposes URH's agentic signal analysis capabilities as MCP tools,
allowing LLM-based applications to analyze radio signals, detect
modulation parameters, demodulate messages, and infer protocol fields.

Usage::

    # stdio transport (default, for IDE/agent integration)
    urh_mcp

    # or run directly
    python -m urh.mcp_server
"""

import base64
import json
import os
import tempfile

import numpy as np
from mcp.server.fastmcp import FastMCP

from urh.ainterpretation.AgenticAnalysis import analyze_iq_array, analyze_signal

mcp = FastMCP(
    "URH Signal Analyzer",
    instructions=(
        "Universal Radio Hacker (URH) signal analysis server. "
        "Use the provided tools to analyze radio signal recordings, "
        "detect modulation parameters, demodulate messages, and infer "
        "protocol field boundaries."
    ),
)

SUPPORTED_FORMATS = {
    ".complex": "Raw float32 IQ pairs (URH native)",
    ".complex16s": "Signed 8-bit IQ pairs (RTL-SDR / HackRF)",
    ".complex16u": "Unsigned 8-bit IQ pairs (RTL-SDR)",
    ".complex32s": "Signed 16-bit IQ pairs (LimeSDR / PlutoSDR)",
    ".complex32u": "Unsigned 16-bit IQ pairs",
    ".cs8": "Signed 8-bit IQ pairs",
    ".cu8": "Unsigned 8-bit IQ pairs",
    ".cs16": "Signed 16-bit IQ pairs",
    ".cu16": "Unsigned 16-bit IQ pairs",
    ".wav": "PCM waveform audio (1-ch demodulated, 2-ch IQ)",
    ".coco": "Compressed complex (tar-wrapped .complex)",
    ".sub": "Flipper Zero SubGHz RAW (OOK)",
    ".blu": "X-Midas BLUE (512-byte header)",
    ".blue": "X-Midas BLUE (512-byte header)",
    ".mat": "MATLAB Level 5 (requires scipy)",
}


def _convert_numpy(value):
    """Convert numpy scalars to native Python types for JSON serialization."""
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, dict):
        return {k: _convert_numpy(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_convert_numpy(v) for v in value]
    return value


def _serialize_result(result: dict) -> dict:
    """Ensure all values in the analysis result are JSON-serializable."""
    return _convert_numpy(result)


@mcp.tool()
def analyze_signal_file(
    signal_path: str,
    sample_rate: float = 1e6,
) -> str:
    """Analyze a radio signal file to detect modulation, demodulate messages, and infer protocol fields.

    Runs the full URH agentic analysis pipeline on a signal file:
    auto-detect modulation parameters → demodulate → extract messages →
    infer protocol field boundaries (when ≥2 messages are found).

    Args:
        signal_path: Absolute path to a signal file. Supported formats include
            .complex, .complex16s, .complex32s, .wav, .coco, .blu, .blue, .mat, .sub, and more.
        sample_rate: Sample rate in Hz (default 1 MHz). Used for timing calculations;
            modulation detection is sample-rate agnostic.

    Returns:
        JSON string with detected signal_parameters (modulation_type, bit_length,
        center, noise, tolerance), decoded messages (hex, bits, ascii, pause),
        protocol_fields (name, start, end, message_type), and num_messages.
    """
    if not os.path.isfile(signal_path):
        return json.dumps({"error": f"File not found: {signal_path}"})

    result = analyze_signal(signal_path, sample_rate=sample_rate)
    return json.dumps(_serialize_result(result), indent=2)


@mcp.tool()
def analyze_iq_data(
    iq_base64: str,
    dtype: str = "float32",
    noise: float | None = None,
    modulation: str | None = None,
) -> str:
    """Analyze raw IQ samples provided as base64-encoded binary data.

    Use this when you have IQ data in memory rather than in a file.
    The data should be base64-encoded raw binary samples.

    Args:
        iq_base64: Base64-encoded IQ samples as raw binary.
            For float32: interleaved I,Q,I,Q,... values (4 bytes each).
            For complex64: complex samples (8 bytes each, real+imag float32 pairs).
        dtype: NumPy dtype of the encoded data. Options: "float32" (default),
            "complex64", "int16", "int8".
        noise: Known noise threshold (auto-detected if not provided).
        modulation: Known modulation type ("ASK", "FSK", or "PSK";
            auto-detected if not provided).

    Returns:
        JSON string with the same structure as analyze_signal_file.
    """
    try:
        raw_bytes = base64.b64decode(iq_base64)
    except Exception as e:
        return json.dumps({"error": f"Invalid base64 data: {e}"})

    dtype_map = {
        "float32": np.float32,
        "complex64": np.complex64,
        "int16": np.int16,
        "int8": np.int8,
    }
    if dtype not in dtype_map:
        return json.dumps(
            {"error": f"Unsupported dtype '{dtype}'. Use: {list(dtype_map.keys())}"}
        )

    try:
        iq_array = np.frombuffer(raw_bytes, dtype=dtype_map[dtype]).copy()
    except Exception as e:
        return json.dumps({"error": f"Failed to parse IQ data: {e}"})

    if iq_array.size == 0:
        return json.dumps({"error": "IQ data is empty"})

    if iq_array.dtype == np.complex64:
        iq_array = iq_array.view(np.float32)

    result = analyze_iq_array(iq_array, noise=noise, modulation=modulation)
    return json.dumps(_serialize_result(result), indent=2)


@mcp.tool()
def list_supported_formats() -> str:
    """List all signal file formats supported by URH.

    Returns:
        JSON object mapping file extensions to format descriptions.
    """
    return json.dumps(SUPPORTED_FORMATS, indent=2)


@mcp.tool()
def list_signal_files(directory: str) -> str:
    """List signal files in a directory that URH can analyze.

    Scans the given directory for files with supported signal extensions.

    Args:
        directory: Absolute path to directory to scan.

    Returns:
        JSON object with the list of signal files found, each with its
        path, size in bytes, and format description.
    """
    if not os.path.isdir(directory):
        return json.dumps({"error": f"Directory not found: {directory}"})

    supported_exts = set(SUPPORTED_FORMATS.keys())
    files = []
    for entry in sorted(os.listdir(directory)):
        full_path = os.path.join(directory, entry)
        if not os.path.isfile(full_path):
            continue
        _, ext = os.path.splitext(entry)
        ext_lower = ext.lower()
        if ext_lower in supported_exts:
            files.append(
                {
                    "path": full_path,
                    "name": entry,
                    "size_bytes": os.path.getsize(full_path),
                    "format": SUPPORTED_FORMATS.get(ext_lower, "Unknown"),
                }
            )

    return json.dumps({"directory": directory, "files": files, "count": len(files)}, indent=2)


def main():
    """Run the URH MCP server with stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
