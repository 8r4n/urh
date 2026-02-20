"""
Agentic Signal Analysis module for Universal Radio Hacker.

Provides an automated end-to-end pipeline that chains together URH's
existing signal processing capabilities:

    load signal → auto-detect parameters → demodulate → extract protocol
    messages → auto-infer protocol fields → produce structured results

This enables fully headless / non-interactive signal analysis without
requiring manual parameter tuning in the GUI.
"""

import numpy as np

from urh.ainterpretation import AutoInterpretation
from urh.awre.FormatFinder import FormatFinder
from urh.signalprocessing.IQArray import IQArray
from urh.signalprocessing.Message import Message
from urh.signalprocessing.ProtocolAnalyzer import ProtocolAnalyzer
from urh.signalprocessing.Signal import Signal


def analyze_signal(
    signal_path: str,
    sample_rate: float = 1e6,
) -> dict:
    """Run the full agentic analysis pipeline on a signal file.

    Parameters
    ----------
    signal_path : str
        Path to a signal file (complex, complex16s, complex32s, coco, wav …).
    sample_rate : float, optional
        Sample rate in Hz.  Only used for timing information; detection
        algorithms are sample-rate agnostic.  Default is 1 MHz.

    Returns
    -------
    dict
        ``signal_parameters`` – detected modulation parameters.
        ``messages``          – list of per-message dicts (hex, bits, ascii).
        ``protocol_fields``   – list of auto-inferred field descriptors.
        ``num_messages``      – total messages found.
    """
    signal = Signal(signal_path, "", sample_rate=sample_rate)

    # --- Step 1: Auto-detect signal parameters ---------------------------
    estimated = AutoInterpretation.estimate(signal.iq_array)
    if estimated is None:
        return {
            "signal_parameters": None,
            "messages": [],
            "protocol_fields": [],
            "num_messages": 0,
        }

    signal.noise_threshold = estimated["noise"]
    signal.modulation_type = estimated["modulation_type"]
    signal.center = estimated["center"]
    signal.tolerance = estimated["tolerance"]
    signal.samples_per_symbol = estimated["bit_length"]

    # --- Step 2: Demodulate and extract protocol messages -----------------
    protocol_analyzer = ProtocolAnalyzer(signal)
    protocol_analyzer.get_protocol_from_signal()

    messages_out = []
    for msg in protocol_analyzer.messages:
        messages_out.append(
            {
                "bits": msg.decoded_bits_str,
                "hex": msg.decoded_hex_str,
                "ascii": msg.decoded_ascii_str,
                "pause": msg.pause,
            }
        )

    # --- Step 3: Auto-infer protocol fields (AWRE) -----------------------
    protocol_fields = []
    if len(protocol_analyzer.messages) >= 2:
        format_finder = FormatFinder(protocol_analyzer.messages)
        format_finder.run()

        for msg_type in format_finder.message_types:
            for label in msg_type:
                protocol_fields.append(
                    {
                        "name": label.name,
                        "start": label.start,
                        "end": label.end,
                        "message_type": msg_type.name,
                    }
                )

    return {
        "signal_parameters": estimated,
        "messages": messages_out,
        "protocol_fields": protocol_fields,
        "num_messages": len(messages_out),
    }


def analyze_iq_array(
    iq_array,
    noise: float = None,
    modulation: str = None,
) -> dict:
    """Run the agentic analysis pipeline on an in-memory IQ array.

    Parameters
    ----------
    iq_array : numpy.ndarray or IQArray
        Raw IQ samples.
    noise : float, optional
        Pre-known noise threshold.  Detected automatically if *None*.
    modulation : str, optional
        Pre-known modulation type (``"ASK"``, ``"FSK"``, ``"PSK"``).
        Detected automatically if *None*.

    Returns
    -------
    dict
        Same structure as :func:`analyze_signal`.
    """
    estimated = AutoInterpretation.estimate(iq_array, noise=noise, modulation=modulation)
    if estimated is None:
        return {
            "signal_parameters": None,
            "messages": [],
            "protocol_fields": [],
            "num_messages": 0,
        }

    signal = Signal("", "")
    if isinstance(iq_array, IQArray):
        signal.iq_array = iq_array
    else:
        if iq_array.dtype == np.complex64:
            signal.iq_array = IQArray(iq_array.view(np.float32))
        else:
            signal.iq_array = IQArray(iq_array)

    signal.noise_threshold = estimated["noise"]
    signal.modulation_type = estimated["modulation_type"]
    signal.center = estimated["center"]
    signal.tolerance = estimated["tolerance"]
    signal.samples_per_symbol = estimated["bit_length"]

    protocol_analyzer = ProtocolAnalyzer(signal)
    protocol_analyzer.get_protocol_from_signal()

    messages_out = []
    for msg in protocol_analyzer.messages:
        messages_out.append(
            {
                "bits": msg.decoded_bits_str,
                "hex": msg.decoded_hex_str,
                "ascii": msg.decoded_ascii_str,
                "pause": msg.pause,
            }
        )

    protocol_fields = []
    if len(protocol_analyzer.messages) >= 2:
        format_finder = FormatFinder(protocol_analyzer.messages)
        format_finder.run()

        for msg_type in format_finder.message_types:
            for label in msg_type:
                protocol_fields.append(
                    {
                        "name": label.name,
                        "start": label.start,
                        "end": label.end,
                        "message_type": msg_type.name,
                    }
                )

    return {
        "signal_parameters": estimated,
        "messages": messages_out,
        "protocol_fields": protocol_fields,
        "num_messages": len(messages_out),
    }
