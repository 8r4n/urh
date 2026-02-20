import os
import tempfile
import unittest

import numpy as np

from urh.signalprocessing.Signal import Signal


def _write_mat_file(filename, var_name, data):
    """Write a MATLAB v5 .mat file using scipy."""
    from scipy.io import savemat

    savemat(filename, {var_name: data})


class TestMatlabSupport(unittest.TestCase):
    """Tests for MATLAB .mat file format support."""

    def test_load_complex_iq(self):
        """Load a .mat file with complex IQ data."""
        iq = np.array([0.1 + 0.2j, 0.3 + 0.4j, -0.5 + 0.6j], dtype=np.complex64)

        with tempfile.NamedTemporaryFile(suffix=".mat", delete=False) as f:
            fname = f.name
        try:
            _write_mat_file(fname, "signal", iq)
            signal = Signal(fname, "")
            self.assertEqual(signal.num_samples, 3)
            np.testing.assert_allclose(
                signal.iq_array.real, iq.real.astype(np.float32), atol=1e-6
            )
            np.testing.assert_allclose(
                signal.iq_array.imag, iq.imag.astype(np.float32), atol=1e-6
            )
        finally:
            os.unlink(fname)

    def test_load_complex_double(self):
        """Load a .mat file with complex128 (double) IQ data."""
        iq = np.array([1.0 + 2.0j, 3.0 - 4.0j], dtype=np.complex128)

        with tempfile.NamedTemporaryFile(suffix=".mat", delete=False) as f:
            fname = f.name
        try:
            _write_mat_file(fname, "data", iq)
            signal = Signal(fname, "")
            self.assertEqual(signal.num_samples, 2)
            np.testing.assert_allclose(
                signal.iq_array.real, iq.real.astype(np.float32), atol=1e-6
            )
            np.testing.assert_allclose(
                signal.iq_array.imag, iq.imag.astype(np.float32), atol=1e-6
            )
        finally:
            os.unlink(fname)

    def test_load_real_signal(self):
        """Load a .mat file with real (non-complex) data → demodulated."""
        data = np.array([0.5, -0.5, 0.5, -0.5], dtype=np.float64)

        with tempfile.NamedTemporaryFile(suffix=".mat", delete=False) as f:
            fname = f.name
        try:
            _write_mat_file(fname, "signal", data)
            signal = Signal(fname, "")
            self.assertEqual(signal.num_samples, 4)
            self.assertTrue(signal.already_demodulated)
            np.testing.assert_allclose(
                signal.iq_array.real, data.astype(np.float32), atol=1e-6
            )
        finally:
            os.unlink(fname)

    def test_load_picks_first_numeric(self):
        """When multiple variables exist, a numeric one is used."""
        from scipy.io import savemat

        iq1 = np.array([0.1 + 0.2j, 0.3 + 0.4j], dtype=np.complex64)
        iq2 = np.array([9.0 + 8.0j], dtype=np.complex64)

        with tempfile.NamedTemporaryFile(suffix=".mat", delete=False) as f:
            fname = f.name
        try:
            savemat(fname, {"first_sig": iq1, "second_sig": iq2})
            signal = Signal(fname, "")
            # Should load one of the variables (both are valid numeric)
            self.assertIn(signal.num_samples, (2, 1))
        finally:
            os.unlink(fname)

    def test_no_numeric_raises(self):
        """A .mat file with no numeric arrays should raise ValueError."""
        from scipy.io import savemat

        with tempfile.NamedTemporaryFile(suffix=".mat", delete=False) as f:
            fname = f.name
        try:
            savemat(fname, {"text": np.array(["hello"], dtype=object)})
            with self.assertRaises(ValueError):
                Signal(fname, "")
        finally:
            os.unlink(fname)

    def test_agentic_analysis_with_matlab(self):
        """AgenticAnalysis.analyze_signal works on MATLAB .mat files."""
        from urh.ainterpretation.AgenticAnalysis import analyze_signal
        from tests.utils_testing import get_path_for_data_file

        fsk_data = np.fromfile(
            get_path_for_data_file("fsk.complex"),
            dtype=np.float32,
        )
        # Convert interleaved float32 I/Q to complex64
        iq_complex = fsk_data[0::2] + 1j * fsk_data[1::2]

        with tempfile.NamedTemporaryFile(suffix=".mat", delete=False) as f:
            fname = f.name
        try:
            _write_mat_file(fname, "iq_data", iq_complex.astype(np.complex64))
            result = analyze_signal(fname)
            self.assertIsNotNone(result["signal_parameters"])
            self.assertEqual(result["signal_parameters"]["modulation_type"], "FSK")
            self.assertGreater(result["num_messages"], 0)
        finally:
            os.unlink(fname)
