import array
import unittest
import xml.etree.ElementTree as ET

from urh.util import util
from urh.util.WSPChecksum import WSPChecksum


class TestWSPChecksum(unittest.TestCase):
    """Tests for the WSPChecksum class."""

    def test_create_auto_mode(self):
        wsp = WSPChecksum()
        self.assertEqual(wsp.mode, WSPChecksum.ChecksumMode.auto)

    def test_create_checksum4_mode(self):
        wsp = WSPChecksum(mode=WSPChecksum.ChecksumMode.checksum4)
        self.assertEqual(wsp.mode, WSPChecksum.ChecksumMode.checksum4)

    def test_create_checksum8_mode(self):
        wsp = WSPChecksum(mode=WSPChecksum.ChecksumMode.checksum8)
        self.assertEqual(wsp.mode, WSPChecksum.ChecksumMode.checksum8)

    def test_create_crc8_mode(self):
        wsp = WSPChecksum(mode=WSPChecksum.ChecksumMode.crc8)
        self.assertEqual(wsp.mode, WSPChecksum.ChecksumMode.crc8)

    def test_equality(self):
        wsp1 = WSPChecksum(mode=WSPChecksum.ChecksumMode.auto)
        wsp2 = WSPChecksum(mode=WSPChecksum.ChecksumMode.auto)
        self.assertEqual(wsp1, wsp2)

    def test_inequality(self):
        wsp1 = WSPChecksum(mode=WSPChecksum.ChecksumMode.auto)
        wsp2 = WSPChecksum(mode=WSPChecksum.ChecksumMode.crc8)
        self.assertNotEqual(wsp1, wsp2)

    def test_inequality_with_non_wsp(self):
        wsp = WSPChecksum()
        self.assertNotEqual(wsp, "not a WSPChecksum")

    def test_hash(self):
        wsp1 = WSPChecksum(mode=WSPChecksum.ChecksumMode.auto)
        wsp2 = WSPChecksum(mode=WSPChecksum.ChecksumMode.auto)
        self.assertEqual(hash(wsp1), hash(wsp2))

    def test_checksum4(self):
        # Create a simple message with known content
        bits = array.array("B", [0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        result = WSPChecksum.checksum4(bits)
        self.assertIsInstance(result, array.array)
        self.assertEqual(len(result), 4)

    def test_checksum8(self):
        bits = array.array("B", [1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        result = WSPChecksum.checksum8(bits)
        self.assertIsInstance(result, array.array)
        self.assertEqual(len(result), 8)

    def test_crc8(self):
        bits = array.array("B", [1, 0, 1, 0, 1, 0, 1, 0])
        result = WSPChecksum.crc8(bits)
        self.assertIsInstance(result, array.array)
        self.assertEqual(len(result), 8)

    def test_checksum8_known_value(self):
        # 0xAA (10101010) as 8 bits + 8 trailing bits for result
        msg = array.array("B", [1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        result = WSPChecksum.checksum8(msg)
        # checksum8 sums all bytes except last 8 bits: 0xAA = 170
        expected = array.array("B", list(map(int, "{0:08b}".format(170))))
        self.assertEqual(list(result), list(expected))

    def test_calculate_checksum4_mode(self):
        wsp = WSPChecksum(mode=WSPChecksum.ChecksumMode.checksum4)
        bits = array.array("B", [0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        result = wsp.calculate(bits)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 4)

    def test_calculate_checksum8_mode(self):
        wsp = WSPChecksum(mode=WSPChecksum.ChecksumMode.checksum8)
        bits = array.array("B", [1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        result = wsp.calculate(bits)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 8)

    def test_calculate_crc8_mode(self):
        wsp = WSPChecksum(mode=WSPChecksum.ChecksumMode.crc8)
        bits = array.array("B", [1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        result = wsp.calculate(bits)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 8)

    def test_calculate_auto_switch_telegram(self):
        """Auto mode with RORG=5 should use checksum4."""
        wsp = WSPChecksum(mode=WSPChecksum.ChecksumMode.auto)
        # RORG=5 = 0101 prefix => switch telegram
        bits = array.array("B", [0, 1, 0, 1] + [0] * 12)
        result = wsp.calculate(bits)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 4)

    def test_calculate_auto_switch_telegram_rorg6(self):
        """Auto mode with RORG=6 should use checksum4."""
        wsp = WSPChecksum(mode=WSPChecksum.ChecksumMode.auto)
        bits = array.array("B", [0, 1, 1, 0] + [0] * 12)
        result = wsp.calculate(bits)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 4)

    def test_calculate_returns_none_on_index_error(self):
        wsp = WSPChecksum(mode=WSPChecksum.ChecksumMode.auto)
        result = wsp.calculate(array.array("B", []))
        self.assertIsNone(result)

    def test_to_xml(self):
        wsp = WSPChecksum(mode=WSPChecksum.ChecksumMode.crc8)
        tag = wsp.to_xml()
        self.assertEqual(tag.tag, "wsp_checksum")
        self.assertEqual(tag.get("mode"), "crc8")

    def test_from_xml(self):
        tag = ET.Element("wsp_checksum", attrib={"mode": "checksum8"})
        wsp = WSPChecksum.from_xml(tag)
        self.assertEqual(wsp.mode, WSPChecksum.ChecksumMode.checksum8)

    def test_xml_roundtrip(self):
        wsp = WSPChecksum(mode=WSPChecksum.ChecksumMode.crc8)
        tag = wsp.to_xml()
        wsp2 = WSPChecksum.from_xml(tag)
        self.assertEqual(wsp, wsp2)

    def test_checksum_mode_enum(self):
        self.assertEqual(WSPChecksum.ChecksumMode.auto.value, 0)
        self.assertEqual(WSPChecksum.ChecksumMode.checksum4.value, 1)
        self.assertEqual(WSPChecksum.ChecksumMode.checksum8.value, 2)
        self.assertEqual(WSPChecksum.ChecksumMode.crc8.value, 3)

    def test_crc8_polynomial(self):
        expected = array.array("B", [1, 0, 0, 0, 0, 0, 1, 1, 1])
        self.assertEqual(list(WSPChecksum.CRC_8_POLYNOMIAL), list(expected))


if __name__ == "__main__":
    unittest.main()
