import os
import struct
import tempfile
import unittest

import numpy as np

from urh.signalprocessing.Signal import Signal


def _write_xmidas_blue(
    filename,
    data,
    fmt_code="CF",
    xdelta=1e-6,
    head_endian="<",
    data_endian="<",
):
    """Write a minimal X-Midas BLUE file for testing."""
    header = bytearray(512)

    # version (offset 0) – "BLUE"
    header[0:4] = b"BLUE"

    # head_rep (offset 4)
    if head_endian == ">":
        header[4:8] = b"EEEI"
    else:
        header[4:8] = b"ILLI"

    # data_rep (offset 8)
    if data_endian == ">":
        header[8:12] = b"EEEI"
    else:
        header[8:12] = b"ILLI"

    data_bytes = data.tobytes()
    data_start = 512.0
    data_size = float(len(data_bytes))

    # data_start (offset 32, real_8)
    struct.pack_into(head_endian + "d", header, 32, data_start)
    # data_size (offset 40, real_8)
    struct.pack_into(head_endian + "d", header, 40, data_size)
    # type_code (offset 48, int_4) – 1000 for vector
    struct.pack_into(head_endian + "i", header, 48, 1000)
    # format (offset 52, 2 chars)
    header[52:54] = fmt_code.encode("ascii")

    # adjunct xstart (offset 256, real_8)
    struct.pack_into(head_endian + "d", header, 256, 0.0)
    # adjunct xdelta (offset 264, real_8)
    struct.pack_into(head_endian + "d", header, 264, xdelta)

    with open(filename, "wb") as f:
        f.write(header)
        f.write(data_bytes)


class TestXmidasSupport(unittest.TestCase):
    """Tests for X-Midas BLUE file format support."""

    def test_load_complex_float_le(self):
        """Load a little-endian CF (complex float) BLUE file."""
        iq = np.array([0.1, 0.2, 0.3, 0.4, -0.5, 0.6], dtype=np.float32)

        with tempfile.NamedTemporaryFile(suffix=".blu", delete=False) as f:
            fname = f.name
        try:
            _write_xmidas_blue(fname, iq, fmt_code="CF", xdelta=1e-6)
            signal = Signal(fname, "")
            self.assertEqual(signal.num_samples, 3)
            np.testing.assert_allclose(
                signal.iq_array.real, iq[0::2], atol=1e-6
            )
            np.testing.assert_allclose(
                signal.iq_array.imag, iq[1::2], atol=1e-6
            )
            self.assertAlmostEqual(signal.sample_rate, 1e6, places=0)
        finally:
            os.unlink(fname)

    def test_load_complex_float_be(self):
        """Load a big-endian CF BLUE file."""
        iq = np.array([0.1, 0.2, -0.3, 0.4], dtype=np.float32)
        iq_be = iq.astype(iq.dtype.newbyteorder(">"))

        with tempfile.NamedTemporaryFile(suffix=".blue", delete=False) as f:
            fname = f.name
        try:
            _write_xmidas_blue(
                fname, iq_be, fmt_code="CF", xdelta=1e-6,
                head_endian=">", data_endian=">",
            )
            signal = Signal(fname, "")
            self.assertEqual(signal.num_samples, 2)
            np.testing.assert_allclose(
                signal.iq_array.real, iq[0::2], atol=1e-6
            )
            np.testing.assert_allclose(
                signal.iq_array.imag, iq[1::2], atol=1e-6
            )
        finally:
            os.unlink(fname)

    def test_load_scalar_float(self):
        """Load scalar-float (SF) BLUE file → treated as demodulated."""
        data = np.array([0.5, -0.5, 0.5, -0.5], dtype=np.float32)

        with tempfile.NamedTemporaryFile(suffix=".blu", delete=False) as f:
            fname = f.name
        try:
            _write_xmidas_blue(fname, data, fmt_code="SF", xdelta=1e-6)
            signal = Signal(fname, "")
            self.assertEqual(signal.num_samples, 4)
            self.assertTrue(signal.already_demodulated)
        finally:
            os.unlink(fname)

    def test_load_complex_int16(self):
        """Load a CI (complex int16) BLUE file."""
        iq = np.array([100, -200, 300, -400], dtype=np.int16)

        with tempfile.NamedTemporaryFile(suffix=".blu", delete=False) as f:
            fname = f.name
        try:
            _write_xmidas_blue(fname, iq, fmt_code="CI", xdelta=5e-7)
            signal = Signal(fname, "")
            self.assertEqual(signal.num_samples, 2)
            self.assertAlmostEqual(signal.sample_rate, 2e6, places=0)
        finally:
            os.unlink(fname)

    def test_sample_rate_from_xdelta(self):
        """xdelta = 1/sample_rate → sample_rate correctly extracted."""
        iq = np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float32)

        with tempfile.NamedTemporaryFile(suffix=".blu", delete=False) as f:
            fname = f.name
        try:
            _write_xmidas_blue(fname, iq, fmt_code="CF", xdelta=2.5e-7)
            signal = Signal(fname, "")
            self.assertAlmostEqual(signal.sample_rate, 4e6, places=0)
        finally:
            os.unlink(fname)

    def test_unsupported_format_raises(self):
        """An unknown format code should raise ValueError."""
        iq = np.array([0.0, 0.0], dtype=np.float32)

        with tempfile.NamedTemporaryFile(suffix=".blu", delete=False) as f:
            fname = f.name
        try:
            _write_xmidas_blue(fname, iq, fmt_code="XX", xdelta=1e-6)
            with self.assertRaises(ValueError):
                Signal(fname, "")
        finally:
            os.unlink(fname)

    def test_file_too_small_raises(self):
        """A file smaller than 512 bytes should raise ValueError."""
        with tempfile.NamedTemporaryFile(suffix=".blu", delete=False) as f:
            fname = f.name
            f.write(b"\x00" * 100)
        try:
            with self.assertRaises(ValueError):
                Signal(fname, "")
        finally:
            os.unlink(fname)

    def test_negative_data_size_raises(self):
        """A header with negative data_size should raise ValueError."""
        header = bytearray(512)
        header[0:4] = b"BLUE"
        header[4:8] = b"ILLI"
        header[8:12] = b"ILLI"
        struct.pack_into("<d", header, 32, 512.0)  # data_start
        struct.pack_into("<d", header, 40, -1.0)   # negative data_size
        header[52:54] = b"CF"
        struct.pack_into("<d", header, 264, 1e-6)

        with tempfile.NamedTemporaryFile(suffix=".blu", delete=False) as f:
            fname = f.name
            f.write(header)
        try:
            with self.assertRaises(ValueError):
                Signal(fname, "")
        finally:
            os.unlink(fname)

    def test_agentic_analysis_with_xmidas(self):
        """AgenticAnalysis.analyze_signal works on xmidas BLUE files."""
        from urh.ainterpretation.AgenticAnalysis import analyze_signal
        from tests.utils_testing import get_path_for_data_file

        fsk_data = np.fromfile(
            get_path_for_data_file("fsk.complex"),
            dtype=np.float32,
        )

        with tempfile.NamedTemporaryFile(suffix=".blu", delete=False) as f:
            fname = f.name
        try:
            _write_xmidas_blue(fname, fsk_data, fmt_code="CF", xdelta=1e-6)
            result = analyze_signal(fname)
            self.assertIsNotNone(result["signal_parameters"])
            self.assertEqual(result["signal_parameters"]["modulation_type"], "FSK")
            self.assertGreater(result["num_messages"], 0)
        finally:
            os.unlink(fname)
