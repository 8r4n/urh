import unittest
import xml.etree.ElementTree as ET

from urh.signalprocessing.Message import Message
from urh.signalprocessing.MessageType import MessageType
from urh.signalprocessing.Ruleset import Mode, OPERATIONS, OPERATION_DESCRIPTION, Rule, Ruleset


class TestRule(unittest.TestCase):
    """Tests for the Rule class."""

    def _make_msg(self, bits_str):
        return Message.from_plain_bits_str(bits_str)

    def test_create_rule(self):
        r = Rule(start=0, end=3, operator="=", target_value="1010", value_type=0)
        self.assertEqual(r.start, 0)
        self.assertEqual(r.end, 4)  # end is incremented by 1 internally
        self.assertEqual(r.operator, "=")
        self.assertEqual(r.target_value, "1010")

    def test_start_setter(self):
        r = Rule(start=0, end=3, operator="=", target_value="", value_type=0)
        r.start = 5
        self.assertEqual(r.start, 5)

    def test_end_setter(self):
        r = Rule(start=0, end=3, operator="=", target_value="", value_type=0)
        r.end = 10
        self.assertEqual(r.end, 10)

    def test_value_type_setter(self):
        r = Rule(start=0, end=3, operator="=", target_value="", value_type=0)
        r.value_type = 1
        self.assertEqual(r.value_type, 1)

    def test_applies_equal(self):
        r = Rule(start=0, end=3, operator="=", target_value="1010", value_type=0)
        msg = self._make_msg("10101111")
        self.assertTrue(r.applies_for_message(msg))

    def test_applies_not_equal(self):
        r = Rule(start=0, end=3, operator="!=", target_value="0000", value_type=0)
        msg = self._make_msg("10101111")
        self.assertTrue(r.applies_for_message(msg))

    def test_applies_equal_fails(self):
        r = Rule(start=0, end=3, operator="=", target_value="0000", value_type=0)
        msg = self._make_msg("10101111")
        self.assertFalse(r.applies_for_message(msg))

    def test_operator_description(self):
        r = Rule(start=0, end=3, operator=">", target_value="", value_type=0)
        self.assertEqual(r.operator_description, "greater")

    def test_set_operator_description(self):
        r = Rule(start=0, end=3, operator="=", target_value="", value_type=0)
        r.operator_description = "lower"
        self.assertEqual(r.operator, "<")

    def test_to_xml(self):
        r = Rule(start=0, end=3, operator="=", target_value="test", value_type=0)
        tag = r.to_xml()
        self.assertEqual(tag.tag, "rule")

    def test_from_xml(self):
        r1 = Rule(start=0, end=3, operator="=", target_value="test", value_type=0)
        tag = r1.to_xml()
        r2 = Rule.from_xml(tag)
        self.assertEqual(str(r2.operator), str(r1.operator))

    def test_operations_dict(self):
        self.assertIn("=", OPERATIONS)
        self.assertIn("!=", OPERATIONS)
        self.assertIn(">", OPERATIONS)
        self.assertIn("<", OPERATIONS)
        self.assertIn(">=", OPERATIONS)
        self.assertIn("<=", OPERATIONS)

    def test_operation_description_dict(self):
        self.assertEqual(OPERATION_DESCRIPTION["="], "equal")
        self.assertEqual(OPERATION_DESCRIPTION["!="], "not equal")
        self.assertEqual(OPERATION_DESCRIPTION[">"], "greater")
        self.assertEqual(OPERATION_DESCRIPTION["<"], "lower")


class TestRuleset(unittest.TestCase):
    """Tests for the Ruleset class."""

    def _make_msg(self, bits_str):
        return Message.from_plain_bits_str(bits_str)

    def test_create_empty_ruleset(self):
        rs = Ruleset()
        self.assertEqual(len(rs), 0)
        self.assertEqual(rs.mode, Mode.all_apply)

    def test_create_with_mode(self):
        rs = Ruleset(mode=Mode.atleast_one_applies)
        self.assertEqual(rs.mode, Mode.atleast_one_applies)

    def test_create_with_rules(self):
        r = Rule(start=0, end=3, operator="=", target_value="1010", value_type=0)
        rs = Ruleset(rules=[r])
        self.assertEqual(len(rs), 1)

    def test_all_apply_mode(self):
        r1 = Rule(start=0, end=3, operator="=", target_value="1010", value_type=0)
        r2 = Rule(start=4, end=7, operator="=", target_value="1111", value_type=0)
        rs = Ruleset(mode=Mode.all_apply, rules=[r1, r2])

        msg = self._make_msg("10101111")
        self.assertTrue(rs.applies_for_message(msg))

    def test_all_apply_mode_fails(self):
        r1 = Rule(start=0, end=3, operator="=", target_value="1010", value_type=0)
        r2 = Rule(start=4, end=7, operator="=", target_value="0000", value_type=0)
        rs = Ruleset(mode=Mode.all_apply, rules=[r1, r2])

        msg = self._make_msg("10101111")
        self.assertFalse(rs.applies_for_message(msg))

    def test_atleast_one_applies_mode(self):
        r1 = Rule(start=0, end=3, operator="=", target_value="0000", value_type=0)
        r2 = Rule(start=4, end=7, operator="=", target_value="1111", value_type=0)
        rs = Ruleset(mode=Mode.atleast_one_applies, rules=[r1, r2])

        msg = self._make_msg("10101111")
        self.assertTrue(rs.applies_for_message(msg))  # r2 applies

    def test_none_applies_mode(self):
        r1 = Rule(start=0, end=3, operator="=", target_value="0000", value_type=0)
        rs = Ruleset(mode=Mode.none_applies, rules=[r1])

        msg = self._make_msg("10101111")
        self.assertTrue(rs.applies_for_message(msg))  # no rules match

    def test_none_applies_mode_fails(self):
        r1 = Rule(start=0, end=3, operator="=", target_value="1010", value_type=0)
        rs = Ruleset(mode=Mode.none_applies, rules=[r1])

        msg = self._make_msg("10101111")
        self.assertFalse(rs.applies_for_message(msg))  # r1 matches

    def test_to_xml(self):
        r = Rule(start=0, end=3, operator="=", target_value="test", value_type=0)
        rs = Ruleset(mode=Mode.all_apply, rules=[r])
        tag = rs.to_xml()
        self.assertEqual(tag.tag, "ruleset")
        self.assertEqual(tag.get("mode"), "0")
        self.assertEqual(len(tag.findall("rule")), 1)

    def test_from_xml(self):
        r = Rule(start=0, end=3, operator="=", target_value="test", value_type=0)
        rs = Ruleset(mode=Mode.atleast_one_applies, rules=[r])
        tag = rs.to_xml()
        rs2 = Ruleset.from_xml(tag)
        self.assertEqual(rs2.mode, Mode.atleast_one_applies)
        self.assertEqual(len(rs2), 1)

    def test_from_xml_none(self):
        rs = Ruleset.from_xml(None)
        self.assertEqual(rs.mode, Mode.all_apply)
        self.assertEqual(len(rs), 0)

    def test_mode_enum(self):
        self.assertEqual(Mode.all_apply.value, 0)
        self.assertEqual(Mode.atleast_one_applies.value, 1)
        self.assertEqual(Mode.none_applies.value, 2)

    def test_empty_ruleset_all_apply(self):
        """Empty ruleset in all_apply mode should apply (0 == 0)."""
        rs = Ruleset(mode=Mode.all_apply)
        msg = self._make_msg("1010")
        self.assertTrue(rs.applies_for_message(msg))

    def test_empty_ruleset_atleast_one(self):
        """Empty ruleset in atleast_one mode should not apply (0 > 0 is false)."""
        rs = Ruleset(mode=Mode.atleast_one_applies)
        msg = self._make_msg("1010")
        self.assertFalse(rs.applies_for_message(msg))

    def test_empty_ruleset_none_applies(self):
        """Empty ruleset in none_applies mode should apply (0 == 0)."""
        rs = Ruleset(mode=Mode.none_applies)
        msg = self._make_msg("1010")
        self.assertTrue(rs.applies_for_message(msg))


if __name__ == "__main__":
    unittest.main()
