import base64
import json
import os
import unittest

import numpy as np

from tests.utils_testing import get_path_for_data_file
from urh.mcp_server import (
    analyze_iq_data,
    analyze_signal_file,
    list_signal_files,
    list_supported_formats,
)


class TestMCPServerTools(unittest.TestCase):
    """Tests for the URH MCP server tool functions."""

    def test_analyze_signal_file_fsk(self):
        """analyze_signal_file returns valid JSON with FSK detection."""
        result_json = analyze_signal_file(get_path_for_data_file("fsk.complex"))
        result = json.loads(result_json)

        self.assertNotIn("error", result)
        self.assertIsNotNone(result["signal_parameters"])
        self.assertEqual(result["signal_parameters"]["modulation_type"], "FSK")
        self.assertEqual(result["signal_parameters"]["bit_length"], 100)
        self.assertGreater(result["num_messages"], 0)

    def test_analyze_signal_file_ask(self):
        """analyze_signal_file detects ASK modulation."""
        result_json = analyze_signal_file(get_path_for_data_file("ask.complex"))
        result = json.loads(result_json)

        self.assertNotIn("error", result)
        self.assertEqual(result["signal_parameters"]["modulation_type"], "ASK")
        self.assertGreater(result["num_messages"], 0)

    def test_analyze_signal_file_not_found(self):
        """analyze_signal_file returns an error for missing files."""
        result_json = analyze_signal_file("/nonexistent/path.complex")
        result = json.loads(result_json)

        self.assertIn("error", result)
        self.assertIn("not found", result["error"].lower())

    def test_analyze_signal_file_json_serializable(self):
        """All values in the result must be JSON-serializable (no numpy types)."""
        result_json = analyze_signal_file(get_path_for_data_file("fsk.complex"))
        # json.loads would fail if any numpy types leaked through
        result = json.loads(result_json)
        # Re-serialize to confirm round-trip works
        json.dumps(result)

    def test_analyze_iq_data_fsk(self):
        """analyze_iq_data decodes base64 float32 IQ data correctly."""
        fsk_data = np.fromfile(
            get_path_for_data_file("fsk.complex"), dtype=np.float32
        )
        b64 = base64.b64encode(fsk_data.tobytes()).decode()
        result_json = analyze_iq_data(b64, dtype="float32")
        result = json.loads(result_json)

        self.assertNotIn("error", result)
        self.assertEqual(result["signal_parameters"]["modulation_type"], "FSK")
        self.assertGreater(result["num_messages"], 0)

    def test_analyze_iq_data_invalid_base64(self):
        """analyze_iq_data returns error for bad base64 input."""
        result_json = analyze_iq_data("not-valid-base64!!!")
        result = json.loads(result_json)

        self.assertIn("error", result)

    def test_analyze_iq_data_unsupported_dtype(self):
        """analyze_iq_data returns error for unsupported dtype."""
        b64 = base64.b64encode(b"\x00" * 16).decode()
        result_json = analyze_iq_data(b64, dtype="float128")
        result = json.loads(result_json)

        self.assertIn("error", result)
        self.assertIn("Unsupported dtype", result["error"])

    def test_analyze_iq_data_with_known_params(self):
        """analyze_iq_data accepts pre-known noise and modulation."""
        fsk_data = np.fromfile(
            get_path_for_data_file("fsk.complex"), dtype=np.float32
        )
        b64 = base64.b64encode(fsk_data.tobytes()).decode()
        result_json = analyze_iq_data(b64, noise=0.01, modulation="FSK")
        result = json.loads(result_json)

        self.assertNotIn("error", result)
        self.assertEqual(result["signal_parameters"]["modulation_type"], "FSK")

    def test_list_supported_formats(self):
        """list_supported_formats returns a dict of extensions."""
        result_json = list_supported_formats()
        result = json.loads(result_json)

        self.assertIn(".complex", result)
        self.assertIn(".wav", result)
        self.assertIn(".blu", result)
        self.assertIn(".mat", result)

    def test_list_signal_files(self):
        """list_signal_files discovers signal files in the test data dir."""
        data_dir = os.path.dirname(get_path_for_data_file("fsk.complex"))
        result_json = list_signal_files(data_dir)
        result = json.loads(result_json)

        self.assertNotIn("error", result)
        self.assertGreater(result["count"], 0)
        # Check that known test files appear
        names = [f["name"] for f in result["files"]]
        self.assertIn("fsk.complex", names)

    def test_list_signal_files_bad_dir(self):
        """list_signal_files returns error for missing directory."""
        result_json = list_signal_files("/nonexistent/dir")
        result = json.loads(result_json)

        self.assertIn("error", result)
