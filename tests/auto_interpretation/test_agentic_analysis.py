import unittest

import numpy as np

from tests.utils_testing import get_path_for_data_file
from urh.ainterpretation.AgenticAnalysis import analyze_signal, analyze_iq_array
from urh.signalprocessing.Signal import Signal


class TestAgenticAnalysis(unittest.TestCase):
    """Tests for the agentic (automated) signal analysis pipeline."""

    def test_analyze_signal_fsk(self):
        result = analyze_signal(get_path_for_data_file("fsk.complex"))

        self.assertIsNotNone(result["signal_parameters"])
        self.assertEqual(result["signal_parameters"]["modulation_type"], "FSK")
        self.assertEqual(result["signal_parameters"]["bit_length"], 100)
        self.assertGreater(result["num_messages"], 0)
        self.assertEqual(result["messages"][0]["hex"], "aaaaaaaac626c626f4dc1d98eef7a427999cd239d3f18")

    def test_analyze_signal_ask(self):
        result = analyze_signal(get_path_for_data_file("ask.complex"))

        self.assertIsNotNone(result["signal_parameters"])
        self.assertEqual(result["signal_parameters"]["modulation_type"], "ASK")
        self.assertEqual(result["signal_parameters"]["bit_length"], 300)
        self.assertGreater(result["num_messages"], 0)
        self.assertEqual(result["messages"][0]["hex"], "b25b6db6c80")

    def test_analyze_iq_array_fsk(self):
        fsk_data = np.fromfile(
            get_path_for_data_file("fsk.complex"), dtype=np.float32
        )
        result = analyze_iq_array(fsk_data)

        self.assertIsNotNone(result["signal_parameters"])
        self.assertEqual(result["signal_parameters"]["modulation_type"], "FSK")
        self.assertEqual(result["signal_parameters"]["bit_length"], 100)
        self.assertGreater(result["num_messages"], 0)
        self.assertEqual(result["messages"][0]["hex"], "aaaaaaaac626c626f4dc1d98eef7a427999cd239d3f18")

    def test_analyze_signal_homematic(self):
        result = analyze_signal(get_path_for_data_file("homematic.complex32s"))

        self.assertIsNotNone(result["signal_parameters"])
        self.assertEqual(result["signal_parameters"]["modulation_type"], "FSK")
        self.assertEqual(result["signal_parameters"]["bit_length"], 100)
        self.assertEqual(result["num_messages"], 2)
        for msg in result["messages"]:
            self.assertTrue(msg["hex"].startswith("aaaaaaaa"))

    def test_analyze_signal_elektromaten(self):
        result = analyze_signal(get_path_for_data_file("elektromaten.complex16s"))

        self.assertIsNotNone(result["signal_parameters"])
        self.assertEqual(result["signal_parameters"]["modulation_type"], "ASK")
        self.assertEqual(result["signal_parameters"]["bit_length"], 600)
        self.assertEqual(result["num_messages"], 11)

    def test_analyze_returns_protocol_fields(self):
        """When multiple messages exist, AWRE should infer protocol fields."""
        result = analyze_signal(get_path_for_data_file("homematic.complex32s"))

        # The homematic signal has 2 messages so AWRE can run
        self.assertGreaterEqual(result["num_messages"], 2)
        # protocol_fields is a list; it may or may not find fields depending
        # on the signal, but the key must exist and be a list
        self.assertIsInstance(result["protocol_fields"], list)

    def test_analyze_result_structure(self):
        """Every result dict must have the expected keys."""
        result = analyze_signal(get_path_for_data_file("fsk.complex"))

        self.assertIn("signal_parameters", result)
        self.assertIn("messages", result)
        self.assertIn("protocol_fields", result)
        self.assertIn("num_messages", result)

        params = result["signal_parameters"]
        self.assertIn("modulation_type", params)
        self.assertIn("bit_length", params)
        self.assertIn("center", params)
        self.assertIn("tolerance", params)
        self.assertIn("noise", params)

        msg = result["messages"][0]
        self.assertIn("bits", msg)
        self.assertIn("hex", msg)
        self.assertIn("ascii", msg)
        self.assertIn("pause", msg)

    def test_analyze_iq_array_with_known_params(self):
        """Passing known noise / modulation skips detection for those."""
        fsk_data = np.fromfile(
            get_path_for_data_file("fsk.complex"), dtype=np.float32
        )
        result = analyze_iq_array(fsk_data, noise=0.01, modulation="FSK")

        self.assertIsNotNone(result["signal_parameters"])
        self.assertEqual(result["signal_parameters"]["modulation_type"], "FSK")
        self.assertGreater(result["num_messages"], 0)

    def test_analyze_signal_returns_empty_on_noise_only(self):
        """A pure-noise array should return an empty result, not crash."""
        noise = np.random.normal(0, 0.001, 1000).astype(np.float32)
        result = analyze_iq_array(noise)

        self.assertEqual(result["num_messages"], 0)
        self.assertEqual(result["messages"], [])
