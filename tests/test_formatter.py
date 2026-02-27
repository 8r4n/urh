import locale
import unittest

from urh.util.Formatter import Formatter


class TestFormatter(unittest.TestCase):
    """Tests for the Formatter utility class."""

    def test_science_time_nanoseconds(self):
        result = Formatter.science_time(0.5e-9)
        self.assertIn("n", result)
        self.assertIn("s", result)

    def test_science_time_microseconds(self):
        result = Formatter.science_time(5e-6)
        self.assertIn("µ", result)
        self.assertIn("s", result)

    def test_science_time_milliseconds(self):
        result = Formatter.science_time(5e-3)
        self.assertIn("m", result)
        self.assertIn("s", result)

    def test_science_time_seconds(self):
        result = Formatter.science_time(2.5)
        self.assertIn("s", result)
        self.assertNotIn("m", result.replace("ms", ""))

    def test_science_time_no_append_seconds(self):
        result = Formatter.science_time(1.0, append_seconds=False)
        self.assertFalse(result.endswith("s"))

    def test_science_time_decimals(self):
        result = Formatter.science_time(1.23456, decimals=4)
        self.assertIn("s", result)

    def test_science_time_remove_spaces(self):
        result = Formatter.science_time(1.0, remove_spaces=True)
        self.assertNotIn(" ", result)

    def test_big_value_giga(self):
        result = Formatter.big_value_with_suffix(2.4e9)
        self.assertIn("G", result)

    def test_big_value_mega(self):
        result = Formatter.big_value_with_suffix(433.92e6)
        self.assertIn("M", result)

    def test_big_value_kilo(self):
        result = Formatter.big_value_with_suffix(10e3)
        self.assertIn("K", result)

    def test_big_value_small(self):
        result = Formatter.big_value_with_suffix(42.0)
        self.assertNotIn("G", result)
        self.assertNotIn("M", result)
        self.assertNotIn("K", result)

    def test_big_value_negative(self):
        result = Formatter.big_value_with_suffix(-1e6)
        self.assertIn("M", result)

    def test_big_value_strip_zeros(self):
        result = Formatter.big_value_with_suffix(1e6, strip_zeros=True)
        self.assertIn("M", result)

    def test_big_value_no_strip_zeros(self):
        result = Formatter.big_value_with_suffix(1e6, decimals=3, strip_zeros=False)
        self.assertIn("M", result)

    def test_str2val_int(self):
        self.assertEqual(Formatter.str2val("42", int), 42)

    def test_str2val_float(self):
        self.assertAlmostEqual(Formatter.str2val("3.14", float), 3.14)

    def test_str2val_invalid_returns_default(self):
        self.assertEqual(Formatter.str2val("abc", int, default=0), 0)

    def test_str2val_none_returns_default(self):
        self.assertEqual(Formatter.str2val(None, int, default=-1), -1)

    def test_str2val_empty_returns_default(self):
        self.assertEqual(Formatter.str2val("", int, default=99), 99)

    def test_local_decimal_separator(self):
        sep = Formatter.local_decimal_seperator()
        self.assertIsInstance(sep, str)
        self.assertIn(sep, [".", ","])


if __name__ == "__main__":
    unittest.main()
