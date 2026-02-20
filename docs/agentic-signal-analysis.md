# Agentic Signal Analysis

URH's **Agentic Signal Analysis** module provides a fully automated, headless
pipeline for radio signal reverse-engineering.  It chains together URH's core
capabilities—parameter detection, demodulation, message extraction, and protocol
field inference—into a single function call so that the entire workflow from raw
IQ capture to documented protocol specification can be scripted without the GUI.

---

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [API Reference](#api-reference)
4. [Supported File Formats](#supported-file-formats)
5. [End-to-End Examples](#end-to-end-examples)
   - [Example 1 – FSK Signal from a Complex File](#example-1--fsk-signal-from-a-complex-file)
   - [Example 2 – ASK/OOK Signal from a WAV Recording](#example-2--askook-signal-from-a-wav-recording)
   - [Example 3 – In-Memory IQ Samples](#example-3--in-memory-iq-samples)
   - [Example 4 – MATLAB .mat File](#example-4--matlab-mat-file)
   - [Example 5 – X-Midas BLUE File](#example-5--x-midas-blue-file)
   - [Example 6 – Multi-Message Protocol with Field Inference](#example-6--multi-message-protocol-with-field-inference)
   - [Example 7 – Building a Protocol Specification Document](#example-7--building-a-protocol-specification-document)
6. [Pipeline Architecture](#pipeline-architecture)
7. [Result Dictionary Reference](#result-dictionary-reference)
8. [Troubleshooting](#troubleshooting)

---

## Installation

```bash
# Core installation
pip install urh

# Optional: for MATLAB .mat file support
pip install scipy
```

URH requires Python 3.8+ and a working C compiler for the Cython extensions.
On headless Linux, you also need Qt runtime libraries:

```bash
sudo apt-get install libegl1 libgl1
```

---

## Quick Start

```python
from urh.ainterpretation.AgenticAnalysis import analyze_signal

# Point at any supported signal file
result = analyze_signal("capture.complex")

# What modulation was detected?
print(result["signal_parameters"]["modulation_type"])  # e.g. "FSK"

# How many messages were found?
print(result["num_messages"])  # e.g. 2

# Print each message in hex
for msg in result["messages"]:
    print(msg["hex"])
```

That's it—one function call takes you from raw IQ samples to decoded protocol
messages and (when enough messages are present) automatically inferred protocol
field boundaries.

---

## API Reference

### `analyze_signal(signal_path, sample_rate=1e6) → dict`

Loads a signal file from disk and runs the full analysis pipeline.

| Parameter     | Type    | Default | Description |
|---------------|---------|---------|-------------|
| `signal_path` | `str`   | —       | Path to a signal file (`.complex`, `.complex16s`, `.complex32s`, `.wav`, `.coco`, `.blu`, `.blue`, `.mat`, etc.) |
| `sample_rate` | `float` | `1e6`   | Sample rate in Hz.  Used for timing calculations; detection algorithms are sample-rate agnostic. |

**Returns** a [result dictionary](#result-dictionary-reference).

---

### `analyze_iq_array(iq_array, noise=None, modulation=None) → dict`

Runs the analysis pipeline on IQ data already loaded in memory.

| Parameter    | Type                          | Default | Description |
|--------------|-------------------------------|---------|-------------|
| `iq_array`   | `numpy.ndarray` or `IQArray`  | —       | Raw IQ samples as a 1-D float32 array (interleaved I, Q, I, Q, …) or as complex64 / IQArray. |
| `noise`      | `float` or `None`             | `None`  | Known noise threshold.  Auto-detected when `None`. |
| `modulation` | `str` or `None`               | `None`  | Known modulation type: `"ASK"`, `"FSK"`, or `"PSK"`.  Auto-detected when `None`. |

**Returns** a [result dictionary](#result-dictionary-reference).

---

## Supported File Formats

| Extension(s)                   | Format                     | Notes |
|--------------------------------|----------------------------|-------|
| `.complex`                     | Raw float32 IQ pairs       | URH native format |
| `.complex16s`, `.cs8`          | Signed 8-bit IQ pairs      | RTL-SDR / HackRF convention |
| `.complex16u`, `.cu8`          | Unsigned 8-bit IQ pairs    | RTL-SDR convention |
| `.complex32s`, `.cs16`         | Signed 16-bit IQ pairs     | LimeSDR / PlutoSDR |
| `.complex32u`, `.cu16`         | Unsigned 16-bit IQ pairs   | — |
| `.wav`, `.wave`                | PCM waveform audio         | 1-channel = demodulated; 2-channel = IQ |
| `.coco`                        | Compressed complex          | tar.bz2-wrapped .complex file |
| `.sub`                         | Flipper Zero SubGHz RAW    | OOK delta-encoded |
| `.blu`, `.blue`                | X-Midas BLUE               | 512-byte header; CF/SF/CI/SI/… format codes |
| `.mat`                         | MATLAB Level 5             | Requires `scipy`; complex → IQ, real → demodulated |

---

## End-to-End Examples

### Example 1 – FSK Signal from a Complex File

This example takes a raw FSK recording, detects all parameters automatically,
demodulates, and prints every message in hex and binary.

```python
from urh.ainterpretation.AgenticAnalysis import analyze_signal

# Step 1: Run the full pipeline
result = analyze_signal("fsk_capture.complex")

# Step 2: Inspect detected signal parameters
params = result["signal_parameters"]
print(f"Modulation : {params['modulation_type']}")  # FSK
print(f"Bit length : {params['bit_length']} samples")
print(f"Center     : {params['center']:.4f}")
print(f"Tolerance  : {params['tolerance']}")
print(f"Noise      : {params['noise']:.6f}")

# Step 3: Iterate over demodulated messages
print(f"\n{result['num_messages']} message(s) found:\n")
for i, msg in enumerate(result["messages"]):
    print(f"--- Message {i+1} ---")
    print(f"  Hex   : {msg['hex']}")
    print(f"  Bits  : {msg['bits']}")
    print(f"  ASCII : {msg['ascii']}")
    print(f"  Pause : {msg['pause']} samples after message")

# Step 4: Show automatically inferred protocol fields
if result["protocol_fields"]:
    print("\nInferred protocol fields:")
    for field in result["protocol_fields"]:
        print(f"  {field['name']:20s}  bits [{field['start']}:{field['end']}]"
              f"  (message type: {field['message_type']})")
```

**Expected output** (trimmed):

```
Modulation : FSK
Bit length : 100 samples
Center     : -0.0058
Tolerance  : 5
Noise      : 0.009861

1 message(s) found:

--- Message 1 ---
  Hex   : aaaaaaaac626c626f4dc1d98eef7a427999cd239d3f18
  Bits  : 10101010101010101010101010101010...
  ASCII : ......&.&..........'.......
  Pause : 0 samples after message
```

---

### Example 2 – ASK/OOK Signal from a WAV Recording

```python
from urh.ainterpretation.AgenticAnalysis import analyze_signal

result = analyze_signal("ook_remote.wav")

params = result["signal_parameters"]
print(f"Modulation: {params['modulation_type']}")  # ASK
print(f"Bit length: {params['bit_length']} samples")

for i, msg in enumerate(result["messages"]):
    print(f"Message {i+1}: {msg['hex']}")
```

---

### Example 3 – In-Memory IQ Samples

When you already have samples loaded (e.g. from GNU Radio, an SDR API, or a
custom capture script), use `analyze_iq_array`:

```python
import numpy as np
from urh.ainterpretation.AgenticAnalysis import analyze_iq_array

# Suppose you receive samples as complex64 from your SDR
raw_samples = np.fromfile("capture.raw", dtype=np.complex64)

# Option A: Fully automatic
result = analyze_iq_array(raw_samples)

# Option B: You already know the modulation type
result = analyze_iq_array(raw_samples, modulation="FSK")

# Option C: You know both modulation and noise floor
result = analyze_iq_array(raw_samples, noise=0.01, modulation="FSK")

print(f"Found {result['num_messages']} messages")
for msg in result["messages"]:
    print(msg["hex"])
```

You can also pass a plain float32 array with interleaved I/Q samples:

```python
# Interleaved float32: [I0, Q0, I1, Q1, ...]
iq_interleaved = np.fromfile("capture.complex", dtype=np.float32)
result = analyze_iq_array(iq_interleaved)
```

---

### Example 4 – MATLAB .mat File

If your IQ data is saved from MATLAB or Octave, load it directly:

```python
from urh.ainterpretation.AgenticAnalysis import analyze_signal

# The .mat file should contain a numeric array variable.
# Complex arrays → IQ data.  Real arrays → treated as demodulated.
result = analyze_signal("matlab_capture.mat")

print(f"Modulation: {result['signal_parameters']['modulation_type']}")
for msg in result["messages"]:
    print(msg["hex"])
```

MATLAB files are loaded with `scipy.io.loadmat`. The first numeric array
variable found in the file is used.  Complex arrays (complex64, complex128)
are treated as IQ pairs; real-valued arrays are treated as already-demodulated
signals.

> **Note:** `scipy` must be installed (`pip install scipy`).  It is only
> imported when a `.mat` file is actually loaded.

---

### Example 5 – X-Midas BLUE File

X-Midas BLUE files (common in defense/SIGINT workflows) are supported natively:

```python
from urh.ainterpretation.AgenticAnalysis import analyze_signal

result = analyze_signal("recording.blu")

print(f"Modulation: {result['signal_parameters']['modulation_type']}")
print(f"Messages:   {result['num_messages']}")
for msg in result["messages"]:
    print(msg["hex"])
```

The parser reads the 512-byte BLUE header to determine:

- **Data format:** CF (complex float), SF (scalar float), CI (complex int16),
  SI (scalar int16), CB/SB (int8), CD/SD (float64), CL/SL (int32)
- **Byte order:** big-endian or little-endian
- **Sample rate:** derived from `1 / xdelta`
- **Data offset and size**

Scalar (real-only) formats are treated as already-demodulated signals.

---

### Example 6 – Multi-Message Protocol with Field Inference

When a recording contains multiple messages, URH's AWRE engine can
automatically infer protocol field boundaries such as preamble, sync word,
length fields, addresses, sequence numbers, and checksums.

```python
from urh.ainterpretation.AgenticAnalysis import analyze_signal

# A Homematic recording contains two FSK messages
result = analyze_signal("homematic.complex32s")

# Print detected parameters
params = result["signal_parameters"]
print(f"Modulation: {params['modulation_type']} | "
      f"Bit length: {params['bit_length']} samples")

# Print messages
for i, msg in enumerate(result["messages"]):
    print(f"\nMessage {i+1}:")
    print(f"  Hex: {msg['hex']}")

# Print inferred protocol fields
if result["protocol_fields"]:
    print("\n--- Inferred Protocol Specification ---")
    for field in result["protocol_fields"]:
        bit_width = field["end"] - field["start"]
        print(f"  Field: {field['name']:20s}  "
              f"Bits: [{field['start']:3d} : {field['end']:3d}]  "
              f"Width: {bit_width:3d} bits  "
              f"Type: {field['message_type']}")
```

**Expected output** (example):

```
Modulation: FSK | Bit length: 100 samples

Message 1:
  Hex: aaaaaaaa...

Message 2:
  Hex: aaaaaaaa...

--- Inferred Protocol Specification ---
  Field: preamble              Bits: [  0 :  32]  Width:  32 bits  Type: Default
  Field: sync                  Bits: [ 32 :  64]  Width:  32 bits  Type: Default
  Field: length                Bits: [ 64 :  72]  Width:   8 bits  Type: Default
  Field: address               Bits: [ 72 : 104]  Width:  32 bits  Type: Default
  Field: sequence number       Bits: [104 : 112]  Width:   8 bits  Type: Default
  Field: data                  Bits: [112 : 160]  Width:  48 bits  Type: Default
  Field: checksum              Bits: [160 : 176]  Width:  16 bits  Type: Default
```

> **Note:** Field inference requires at least 2 messages.  The more messages
> available (and the more variance between them), the better the results.

---

### Example 7 – Building a Protocol Specification Document

This example shows a complete workflow: analyze a signal, then generate a
human-readable protocol specification that could be saved to a file or used
as the basis for further implementation.

```python
import json
from urh.ainterpretation.AgenticAnalysis import analyze_signal


def generate_protocol_spec(signal_path: str) -> str:
    """Analyze a signal and produce a protocol specification document."""
    result = analyze_signal(signal_path)

    if result["signal_parameters"] is None:
        return "ERROR: Could not detect any signal in the file."

    params = result["signal_parameters"]
    lines = []

    # --- Header ---
    lines.append("=" * 60)
    lines.append("PROTOCOL SPECIFICATION")
    lines.append(f"Source file: {signal_path}")
    lines.append("=" * 60)

    # --- Physical Layer ---
    lines.append("\n## Physical Layer\n")
    lines.append(f"  Modulation type   : {params['modulation_type']}")
    lines.append(f"  Samples per symbol: {params['bit_length']}")
    lines.append(f"  Center frequency  : {params['center']:.6f}")
    lines.append(f"  Noise threshold   : {params['noise']:.6f}")
    lines.append(f"  Tolerance         : {params['tolerance']}")

    # --- Messages ---
    lines.append(f"\n## Messages ({result['num_messages']} found)\n")
    for i, msg in enumerate(result["messages"]):
        lines.append(f"  Message {i+1}:")
        lines.append(f"    Hex  : {msg['hex']}")
        lines.append(f"    Bits : {msg['bits'][:64]}{'...' if len(msg['bits']) > 64 else ''}")
        lines.append(f"    Pause: {msg['pause']} samples")
        lines.append("")

    # --- Protocol Fields ---
    if result["protocol_fields"]:
        lines.append("## Protocol Fields (auto-inferred)\n")
        lines.append(f"  {'Field':<20s}  {'Bit Range':<14s}  {'Width':>5s}  {'Message Type'}")
        lines.append(f"  {'-'*20}  {'-'*14}  {'-'*5}  {'-'*15}")
        for field in result["protocol_fields"]:
            w = field["end"] - field["start"]
            rng = f"[{field['start']:3d}:{field['end']:3d}]"
            lines.append(
                f"  {field['name']:<20s}  {rng:<14s}  {w:>5d}  {field['message_type']}"
            )
    else:
        lines.append("## Protocol Fields\n")
        lines.append("  (Not enough messages for automatic field inference.)")

    # --- Machine-Readable JSON ---
    lines.append("\n## Raw JSON\n")
    lines.append("```json")
    lines.append(json.dumps(result, indent=2, default=str))
    lines.append("```")

    return "\n".join(lines)


# --- Usage ---
spec = generate_protocol_spec("homematic.complex32s")
print(spec)

# Save to file
with open("protocol_spec.txt", "w") as f:
    f.write(spec)
```

This produces a complete, self-contained protocol specification that documents
the physical-layer parameters, all decoded messages, and the inferred protocol
structure—ready for implementation of a detector or decoder.

---

## Pipeline Architecture

The agentic analysis pipeline chains four stages built on existing URH subsystems:

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Signal Load │────▶│ AutoInterpret.   │────▶│  Protocol    │
│              │     │  estimate()      │     │  Analyzer    │
│  .complex    │     │                  │     │              │
│  .wav        │     │  Detects:        │     │  Demodulates │
│  .blu/.blue  │     │  • modulation    │     │  signal and  │
│  .mat        │     │  • bit length    │     │  extracts    │
│  .sub        │     │  • center        │     │  messages    │
│  etc.        │     │  • noise         │     │              │
└──────────────┘     │  • tolerance     │     └──────┬───────┘
                     └──────────────────┘            │
                                                     ▼
                                              ┌──────────────┐
                                              │  Format      │
                                              │  Finder      │
                                              │  (AWRE)      │
                                              │              │
                                              │  Infers:     │
                                              │  • preamble  │
                                              │  • sync      │
                                              │  • length    │
                                              │  • address   │
                                              │  • seq num   │
                                              │  • checksum  │
                                              └──────────────┘
```

### Stage 1: Signal Loading

The `Signal` class reads IQ data from any supported file format and stores it
as an `IQArray` (an N×2 float32 array of I/Q sample pairs).

### Stage 2: Parameter Estimation (`AutoInterpretation.estimate()`)

Detects the modulation parameters automatically:

| Parameter          | Description |
|--------------------|-------------|
| `modulation_type`  | `"ASK"`, `"FSK"`, or `"PSK"` |
| `bit_length`       | Number of samples per symbol |
| `center`           | Decision threshold between 0 and 1 levels |
| `noise`            | Noise floor threshold |
| `tolerance`        | Allowed deviation in symbol timing |

### Stage 3: Demodulation (`ProtocolAnalyzer.get_protocol_from_signal()`)

Applies the detected parameters to demodulate the signal and extract
individual messages.  Each message is output with:

- `bits` – binary string of demodulated bits
- `hex` – hexadecimal representation
- `ascii` – ASCII-printable representation
- `pause` – number of silence samples after the message

### Stage 4: Protocol Field Inference (`FormatFinder.run()`)

When 2 or more messages are available, URH's AWRE (Automatic Wireless
Reverse Engineering) engine compares messages to identify common patterns
and infer protocol field boundaries.  It can recognize:

- **Preamble** – repeating bit pattern at the start
- **Sync word** – fixed synchronization sequence
- **Length field** – byte indicating payload length
- **Address fields** – source/destination identifiers
- **Sequence numbers** – incrementing counters
- **Checksums** – CRC or sum-based integrity fields

---

## Result Dictionary Reference

Both `analyze_signal()` and `analyze_iq_array()` return a dictionary with
four keys:

```python
{
    "signal_parameters": {
        "modulation_type": str,   # "ASK", "FSK", or "PSK"
        "bit_length": int,        # samples per symbol
        "center": float,          # decision threshold
        "noise": float,           # noise floor
        "tolerance": int,         # timing tolerance
    },
    "messages": [
        {
            "bits": str,          # "10101010..."
            "hex": str,           # "aabb01..."
            "ascii": str,         # printable representation
            "pause": int,         # silence samples after message
        },
        # ... one dict per message
    ],
    "protocol_fields": [
        {
            "name": str,          # e.g. "preamble", "checksum"
            "start": int,         # start bit index
            "end": int,           # end bit index (exclusive)
            "message_type": str,  # message type name
        },
        # ... one dict per inferred field
    ],
    "num_messages": int,          # total number of messages
}
```

If no signal is detected (e.g. the input is pure noise), the result is:

```python
{
    "signal_parameters": None,
    "messages": [],
    "protocol_fields": [],
    "num_messages": 0,
}
```

---

## Troubleshooting

### No messages detected

- **Low SNR:** The noise threshold might be too high.  Try
  `analyze_iq_array(data, noise=0.001)` with a lower noise value.
- **Wrong sample format:** Make sure the file extension matches the actual
  data format (e.g. `.complex16s` for signed 8-bit samples).

### scipy ImportError when loading .mat files

```
ImportError: scipy is required to load MATLAB .mat files.
```

Install scipy: `pip install scipy`.  It is only imported when loading `.mat`
files and is not required for other formats.

### No protocol fields inferred

The AWRE engine needs at least 2 messages to find patterns.  A single-message
recording will return `protocol_fields: []`.  For best results, capture
multiple transmissions of the same protocol.

### Empty result on a valid signal

If `analyze_signal()` returns `signal_parameters: None`, the
`AutoInterpretation.estimate()` step could not find a meaningful signal above
the noise floor.  Verify the file contains actual signal data (not just noise)
by opening it in the URH GUI or plotting it.
