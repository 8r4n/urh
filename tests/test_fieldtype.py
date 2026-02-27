import unittest
import xml.etree.ElementTree as ET

from urh.signalprocessing.FieldType import FieldType


class TestFieldType(unittest.TestCase):
    """Tests for the FieldType class."""

    def test_create_field_type(self):
        ft = FieldType("preamble", FieldType.Function.PREAMBLE)
        self.assertEqual(ft.caption, "preamble")
        self.assertEqual(ft.function, FieldType.Function.PREAMBLE)

    def test_default_display_format_preamble(self):
        ft = FieldType("preamble", FieldType.Function.PREAMBLE)
        self.assertEqual(ft.display_format_index, 0)

    def test_default_display_format_sync(self):
        ft = FieldType("sync", FieldType.Function.SYNC)
        self.assertEqual(ft.display_format_index, 0)

    def test_default_display_format_address(self):
        ft = FieldType("src", FieldType.Function.SRC_ADDRESS)
        self.assertEqual(ft.display_format_index, 1)

    def test_default_display_format_dst_address(self):
        ft = FieldType("dst", FieldType.Function.DST_ADDRESS)
        self.assertEqual(ft.display_format_index, 1)

    def test_default_display_format_checksum(self):
        ft = FieldType("crc", FieldType.Function.CHECKSUM)
        self.assertEqual(ft.display_format_index, 1)

    def test_default_display_format_sequence_number(self):
        ft = FieldType("seq", FieldType.Function.SEQUENCE_NUMBER)
        self.assertEqual(ft.display_format_index, 3)

    def test_default_display_format_length(self):
        ft = FieldType("len", FieldType.Function.LENGTH)
        self.assertEqual(ft.display_format_index, 3)

    def test_default_display_format_data(self):
        ft = FieldType("payload", FieldType.Function.DATA)
        self.assertEqual(ft.display_format_index, 0)

    def test_custom_display_format_index(self):
        ft = FieldType("custom", FieldType.Function.CUSTOM, display_format_index=5)
        self.assertEqual(ft.display_format_index, 5)

    def test_equality(self):
        ft1 = FieldType("preamble", FieldType.Function.PREAMBLE)
        ft2 = FieldType("preamble", FieldType.Function.PREAMBLE)
        self.assertEqual(ft1, ft2)

    def test_inequality_different_caption(self):
        ft1 = FieldType("preamble", FieldType.Function.PREAMBLE)
        ft2 = FieldType("other", FieldType.Function.PREAMBLE)
        self.assertNotEqual(ft1, ft2)

    def test_inequality_different_function(self):
        ft1 = FieldType("test", FieldType.Function.PREAMBLE)
        ft2 = FieldType("test", FieldType.Function.SYNC)
        self.assertNotEqual(ft1, ft2)

    def test_inequality_with_non_fieldtype(self):
        ft = FieldType("test", FieldType.Function.PREAMBLE)
        self.assertNotEqual(ft, "not a field type")

    def test_repr(self):
        ft = FieldType("preamble", FieldType.Function.PREAMBLE, display_format_index=0)
        r = repr(ft)
        self.assertIn("PREAMBLE", r)
        self.assertIn("preamble", r)

    def test_from_caption_valid(self):
        ft = FieldType.from_caption("preamble")
        self.assertIsNotNone(ft)
        self.assertEqual(ft.function, FieldType.Function.PREAMBLE)

    def test_from_caption_data(self):
        ft = FieldType.from_caption("data")
        self.assertIsNotNone(ft)
        self.assertEqual(ft.function, FieldType.Function.DATA)

    def test_from_caption_invalid(self):
        ft = FieldType.from_caption("nonexistent_function")
        self.assertIsNone(ft)

    def test_default_field_types(self):
        defaults = FieldType.default_field_types()
        self.assertIsInstance(defaults, list)
        self.assertEqual(len(defaults), len(FieldType.Function))
        functions = {ft.function for ft in defaults}
        for f in FieldType.Function:
            self.assertIn(f, functions)

    def test_to_xml(self):
        ft = FieldType("preamble", FieldType.Function.PREAMBLE, display_format_index=0)
        tag = ft.to_xml()
        self.assertEqual(tag.tag, "field_type")
        self.assertEqual(tag.get("caption"), "preamble")
        self.assertEqual(tag.get("function"), "PREAMBLE")
        self.assertEqual(tag.get("display_format_index"), "0")

    def test_from_xml(self):
        tag = ET.Element(
            "field_type",
            attrib={
                "caption": "sync",
                "function": "SYNC",
                "display_format_index": "0",
            },
        )
        ft = FieldType.from_xml(tag)
        self.assertEqual(ft.caption, "sync")
        self.assertEqual(ft.function, FieldType.Function.SYNC)
        self.assertEqual(ft.display_format_index, 0)

    def test_from_xml_legacy_crc(self):
        """Legacy XML used 'CRC' instead of 'CHECKSUM'."""
        tag = ET.Element(
            "field_type",
            attrib={"caption": "checksum", "function": "CRC"},
        )
        ft = FieldType.from_xml(tag)
        self.assertEqual(ft.function, FieldType.Function.CHECKSUM)

    def test_from_xml_unknown_function(self):
        tag = ET.Element(
            "field_type",
            attrib={"caption": "unknown", "function": "TOTALLY_UNKNOWN"},
        )
        ft = FieldType.from_xml(tag)
        self.assertEqual(ft.function, FieldType.Function.CUSTOM)

    def test_from_xml_missing_display_format(self):
        tag = ET.Element(
            "field_type",
            attrib={"caption": "test", "function": "DATA"},
        )
        ft = FieldType.from_xml(tag)
        # display_format_index defaults based on function when None
        self.assertEqual(ft.display_format_index, 0)

    def test_xml_roundtrip(self):
        ft = FieldType("checksum", FieldType.Function.CHECKSUM, display_format_index=1)
        tag = ft.to_xml()
        ft2 = FieldType.from_xml(tag)
        self.assertEqual(ft, ft2)
        self.assertEqual(ft.display_format_index, ft2.display_format_index)

    def test_function_enum_values(self):
        """Verify all Function enum members exist."""
        expected = {
            "PREAMBLE", "SYNC", "LENGTH", "SRC_ADDRESS", "DST_ADDRESS",
            "SEQUENCE_NUMBER", "TYPE", "DATA", "CHECKSUM", "CUSTOM",
        }
        actual = {f.name for f in FieldType.Function}
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
