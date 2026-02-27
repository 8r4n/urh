import unittest
import xml.etree.ElementTree as ET

from urh.signalprocessing.Participant import Participant


class TestParticipant(unittest.TestCase):
    """Tests for the Participant class."""

    def test_create_participant(self):
        p = Participant("Alice", shortname="A", address_hex="DEAD")
        self.assertEqual(p.name, "Alice")
        self.assertEqual(p.shortname, "A")
        self.assertEqual(p.address_hex, "DEAD")

    def test_default_shortname(self):
        p = Participant("Bob")
        self.assertEqual(p.shortname, "B")

    def test_default_address_hex(self):
        p = Participant("Carol")
        self.assertEqual(p.address_hex, "")

    def test_empty_name_defaults(self):
        p = Participant("")
        self.assertEqual(p.name, "unknown")
        self.assertEqual(p.shortname, "X")

    def test_none_name_defaults(self):
        """None name is treated as falsy and replaced with 'unknown'."""
        p = Participant(None, shortname="X")
        self.assertEqual(p.name, "unknown")

    def test_color_index(self):
        p = Participant("Eve", color_index=3)
        self.assertEqual(p.color_index, 3)

    def test_show_default(self):
        p = Participant("Test")
        self.assertTrue(p.show)

    def test_simulate_default(self):
        p = Participant("Test")
        self.assertFalse(p.simulate)

    def test_simulate_true(self):
        p = Participant("Test", simulate=True)
        self.assertTrue(p.simulate)

    def test_relative_rssi(self):
        p = Participant("Test", relative_rssi=5)
        self.assertEqual(p.relative_rssi, 5)

    def test_id_auto_generated(self):
        p = Participant("Test")
        self.assertIsNotNone(p.id)
        self.assertGreater(len(p.id), 0)

    def test_id_explicit(self):
        p = Participant("Test", id="custom-id-123")
        self.assertEqual(p.id, "custom-id-123")

    def test_equality(self):
        p1 = Participant("Alice", id="same-id")
        p2 = Participant("Bob", id="same-id")
        self.assertEqual(p1, p2)

    def test_inequality(self):
        p1 = Participant("Alice")
        p2 = Participant("Bob")
        self.assertNotEqual(p1, p2)

    def test_inequality_with_non_participant(self):
        p = Participant("Alice")
        self.assertNotEqual(p, "not a participant")

    def test_id_match(self):
        p = Participant("Test", id="test-id")
        self.assertTrue(p.id_match("test-id"))
        self.assertFalse(p.id_match("other-id"))

    def test_hash(self):
        p1 = Participant("Alice", id="id1")
        p2 = Participant("Bob", id="id2")
        # Different participants should have different hashes (usually)
        self.assertIsInstance(hash(p1), int)
        self.assertIsInstance(hash(p2), int)

    def test_lt_comparison(self):
        p1 = Participant("Alice", shortname="A")
        p2 = Participant("Bob", shortname="B")
        self.assertTrue(p1 < p2)
        self.assertFalse(p2 < p1)

    def test_lt_with_non_participant(self):
        p = Participant("Alice")
        self.assertFalse(p < "string")

    def test_repr_with_address(self):
        p = Participant("Alice", shortname="A", address_hex="DEAD")
        r = repr(p)
        self.assertIn("Alice", r)
        self.assertIn("A", r)
        self.assertIn("DEAD", r)

    def test_repr_without_address(self):
        p = Participant("Alice", shortname="A")
        r = repr(p)
        self.assertIn("Alice", r)
        self.assertIn("A", r)

    def test_str_delegates_to_repr(self):
        p = Participant("Alice", shortname="A")
        self.assertEqual(str(p), repr(p))

    def test_find_matching(self):
        p1 = Participant("Alice", id="id1")
        p2 = Participant("Bob", id="id2")
        participants = [p1, p2]
        self.assertEqual(Participant.find_matching("id1", participants), p1)
        self.assertEqual(Participant.find_matching("id2", participants), p2)
        self.assertIsNone(Participant.find_matching("id3", participants))

    def test_to_xml(self):
        p = Participant("Alice", shortname="A", address_hex="FF", color_index=2, id="test-id")
        tag = p.to_xml()
        self.assertEqual(tag.tag, "participant")
        self.assertEqual(tag.get("name"), "Alice")
        self.assertEqual(tag.get("shortname"), "A")
        self.assertEqual(tag.get("address_hex"), "FF")
        self.assertEqual(tag.get("color_index"), "2")
        self.assertEqual(tag.get("id"), "test-id")

    def test_from_xml(self):
        tag = ET.Element(
            "participant",
            attrib={
                "name": "Bob",
                "shortname": "B",
                "address_hex": "AB",
                "color_index": "1",
                "id": "xml-id",
                "relative_rssi": "3",
                "simulate": "1",
            },
        )
        p = Participant.from_xml(tag)
        self.assertEqual(p.name, "Bob")
        self.assertEqual(p.shortname, "B")
        self.assertEqual(p.address_hex, "AB")
        self.assertEqual(p.color_index, 1)
        self.assertEqual(p.id, "xml-id")
        self.assertEqual(p.relative_rssi, 3)
        self.assertTrue(p.simulate)

    def test_from_xml_negative_color_index(self):
        tag = ET.Element(
            "participant",
            attrib={"name": "Test", "id": "t", "color_index": "-1"},
        )
        p = Participant.from_xml(tag)
        self.assertEqual(p.color_index, 0)

    def test_xml_roundtrip(self):
        p = Participant("Carol", shortname="C", address_hex="CAFE", color_index=5, id="rt-id")
        tag = p.to_xml()
        p2 = Participant.from_xml(tag)
        self.assertEqual(p, p2)
        self.assertEqual(p.name, p2.name)
        self.assertEqual(p.shortname, p2.shortname)
        self.assertEqual(p.address_hex, p2.address_hex)

    def test_participants_to_xml_tag(self):
        p1 = Participant("Alice", id="id1")
        p2 = Participant("Bob", id="id2")
        tag = Participant.participants_to_xml_tag([p1, p2])
        self.assertEqual(tag.tag, "participants")
        self.assertEqual(len(tag.findall("participant")), 2)

    def test_read_participants_from_xml_tag(self):
        p1 = Participant("Alice", id="id1")
        p2 = Participant("Bob", id="id2")
        tag = Participant.participants_to_xml_tag([p1, p2])
        participants = Participant.read_participants_from_xml_tag(tag)
        self.assertEqual(len(participants), 2)
        self.assertEqual(participants[0].name, "Alice")
        self.assertEqual(participants[1].name, "Bob")

    def test_read_participants_from_none(self):
        self.assertEqual(Participant.read_participants_from_xml_tag(None), [])

    def test_read_participants_from_wrapper_tag(self):
        """read_participants_from_xml_tag can find <participants> inside a wrapper."""
        root = ET.Element("project")
        p = Participant("Dave", id="d1")
        root.append(Participant.participants_to_xml_tag([p]))
        participants = Participant.read_participants_from_xml_tag(root)
        self.assertEqual(len(participants), 1)
        self.assertEqual(participants[0].name, "Dave")


if __name__ == "__main__":
    unittest.main()
