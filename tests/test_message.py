import array
import unittest

from urh.signalprocessing.Message import Message
from urh.signalprocessing.MessageType import MessageType


class TestMessage(unittest.TestCase):
    """Tests for the Message class."""

    def _make_msg(self, bits_str="10101010", pause=0):
        return Message.from_plain_bits_str(bits_str, pause=pause)

    def test_create_message(self):
        msg = self._make_msg("1100")
        self.assertEqual(len(msg), 4)

    def test_plain_bits(self):
        msg = self._make_msg("1010")
        self.assertEqual(list(msg.plain_bits), [1, 0, 1, 0])

    def test_plain_bits_str(self):
        msg = self._make_msg("1010")
        self.assertEqual(msg.plain_bits_str, "1010")

    def test_str(self):
        msg = self._make_msg("1100")
        self.assertEqual(str(msg), "1100")

    def test_len(self):
        msg = self._make_msg("11001100")
        self.assertEqual(len(msg), 8)

    def test_getitem(self):
        msg = self._make_msg("1010")
        self.assertEqual(msg[0], 1)
        self.assertEqual(msg[1], 0)

    def test_setitem(self):
        msg = self._make_msg("1010")
        msg[0] = 0
        self.assertEqual(msg[0], 0)

    def test_delitem(self):
        msg = self._make_msg("11001100")
        del msg[0]
        self.assertEqual(len(msg), 7)

    def test_insert(self):
        msg = self._make_msg("1010")
        msg.insert(0, 0)
        self.assertEqual(len(msg), 5)
        self.assertEqual(msg[0], 0)

    def test_plain_hex_str(self):
        # 1010 1010 = 0xAA
        msg = self._make_msg("10101010")
        self.assertEqual(msg.plain_hex_str, "aa")

    def test_decoded_hex_str_default(self):
        # Default decoder is NRZ (no change)
        msg = self._make_msg("10101010")
        self.assertEqual(msg.decoded_hex_str, "aa")

    def test_decoded_bits_str_default(self):
        msg = self._make_msg("1100")
        self.assertEqual(msg.decoded_bits_str, "1100")

    def test_plain_ascii_str(self):
        # 01000001 = 'A' (65)
        msg = self._make_msg("01000001")
        self.assertEqual(msg.plain_ascii_str, "A")

    def test_decoded_ascii_str(self):
        msg = self._make_msg("01000001")
        self.assertEqual(msg.decoded_ascii_str, "A")

    def test_from_plain_bits_str(self):
        msg = Message.from_plain_bits_str("11110000")
        self.assertEqual(msg.plain_bits_str, "11110000")
        self.assertEqual(msg.pause, 0)

    def test_from_plain_bits_str_with_pause(self):
        msg = Message.from_plain_bits_str("1100", pause=500)
        self.assertEqual(msg.pause, 500)

    def test_from_plain_hex_str(self):
        msg = Message.from_plain_hex_str("aa")
        self.assertEqual(msg.plain_hex_str, "aa")

    def test_from_plain_hex_str_f0(self):
        msg = Message.from_plain_hex_str("f0")
        self.assertEqual(msg.plain_bits_str, "11110000")

    def test_bits2string(self):
        msg = self._make_msg()
        bits = array.array("B", [1, 0, 1, 1])
        self.assertEqual(msg.bits2string(bits), "1011")

    def test_pause(self):
        msg = self._make_msg("1010", pause=1000)
        self.assertEqual(msg.pause, 1000)

    def test_get_pause_str_with_sample_rate(self):
        msg = self._make_msg("1010", pause=1000)
        s = msg.get_pause_str(sample_rate=1e6)
        self.assertIn("Pause", s)

    def test_get_pause_str_without_sample_rate(self):
        msg = self._make_msg("1010", pause=1000)
        s = msg.get_pause_str(sample_rate=None)
        self.assertIn("1000 samples", s)

    def test_view_to_string_bits(self):
        msg = self._make_msg("10101010")
        s = msg.view_to_string(view=0, decoded=True, show_pauses=False)
        self.assertEqual(s, "10101010")

    def test_view_to_string_hex(self):
        msg = self._make_msg("10101010")
        s = msg.view_to_string(view=1, decoded=True, show_pauses=False)
        self.assertEqual(s, "aa")

    def test_view_to_string_ascii(self):
        msg = self._make_msg("01000001")
        s = msg.view_to_string(view=2, decoded=True, show_pauses=False)
        self.assertEqual(s, "A")

    def test_view_to_string_invalid_view(self):
        msg = self._make_msg("1010")
        self.assertIsNone(msg.view_to_string(view=99, decoded=True, show_pauses=False))

    def test_clear_decoded_bits(self):
        msg = self._make_msg("1010")
        _ = msg.decoded_bits  # cache
        msg.clear_decoded_bits()
        # Accessing again should recompute
        self.assertEqual(list(msg.decoded_bits), [1, 0, 1, 0])

    def test_clear_encoded_bits(self):
        msg = self._make_msg("1010")
        _ = msg.encoded_bits  # cache
        msg.clear_encoded_bits()
        # Accessing again should recompute
        self.assertEqual(list(msg.encoded_bits), [1, 0, 1, 0])

    def test_set_plain_bits_clears_cache(self):
        msg = self._make_msg("1010")
        _ = msg.decoded_bits
        msg.plain_bits = [0, 0, 1, 1]
        self.assertEqual(list(msg.decoded_bits), [0, 0, 1, 1])

    def test_timestamp_default(self):
        msg = self._make_msg("1010")
        self.assertGreater(msg.timestamp, 0)

    def test_timestamp_explicit(self):
        mt = MessageType("test")
        msg = Message([1, 0], pause=0, message_type=mt, timestamp=12345.0)
        self.assertEqual(msg.timestamp, 12345.0)

    def test_modulator_index(self):
        mt = MessageType("test")
        msg = Message([1, 0], pause=0, message_type=mt, modulator_index=3)
        self.assertEqual(msg.modulator_index, 3)

    def test_rssi(self):
        mt = MessageType("test")
        msg = Message([1, 0], pause=0, message_type=mt, rssi=42)
        self.assertEqual(msg.rssi, 42)

    def test_fuzz_created(self):
        mt = MessageType("test")
        msg = Message([1, 0], pause=0, message_type=mt, fuzz_created=True)
        self.assertTrue(msg.fuzz_created)

    def test_to_xml(self):
        msg = self._make_msg("1100")
        msg.modulator_index = 2
        msg.pause = 500
        tag = msg.to_xml(write_bits=True)
        self.assertEqual(tag.tag, "message")
        self.assertEqual(tag.get("pause"), "500")
        self.assertEqual(tag.get("modulator_index"), "2")
        self.assertEqual(tag.get("bits"), "1100")

    def test_convert_index_same_view(self):
        msg = self._make_msg("10101010")
        result = msg.convert_index(3, from_view=0, to_view=0, decoded=True)
        self.assertEqual(result, (3, 3))

    def test_encoded_bits_str(self):
        msg = self._make_msg("1100")
        self.assertEqual(msg.encoded_bits_str, "1100")

    def test_decoded_bits_buffer(self):
        msg = self._make_msg("1010")
        buf = msg.decoded_bits_buffer
        self.assertIsInstance(buf, bytes)

    def test_decoded_ascii_buffer(self):
        msg = self._make_msg("01000001")
        buf = msg.decoded_ascii_buffer
        self.assertIsInstance(buf, bytes)

    def test_add_messages(self):
        msg1 = self._make_msg("1100")
        msg2 = self._make_msg("0011")
        result = msg1 + msg2
        self.assertEqual(list(result), [1, 1, 0, 0, 0, 0, 1, 1])

    def test_delete_range(self):
        msg = self._make_msg("11001100")
        msg.delete_range_without_label_range_update(0, 4)
        self.assertEqual(msg.plain_bits_str, "1100")

    def test_get_byte_length(self):
        msg = self._make_msg("10101010" * 2)  # 16 bits
        byte_len = msg.get_byte_length(decoded=True)
        # get_byte_length converts to hex view (view 2=ASCII), so 16 bits / 8 = 2 bytes
        self.assertEqual(byte_len, 2)


if __name__ == "__main__":
    unittest.main()
