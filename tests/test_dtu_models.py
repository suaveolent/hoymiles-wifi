"""Verify DTU recognition using synthetic serial numbers."""

import unittest

from hoymiles_wifi.hoymiles import (
    DTUType,
    get_dtu_model_name,
    get_dtu_model_type,
    type_mapping,
)


class DTUModelTests(unittest.TestCase):
    """Identify DTUs without requiring hexadecimal serial suffixes."""

    def test_existing_prefixes(self):
        """Preserve all supported model mappings and trailing J serials."""
        for prefix, model in type_mapping.items():
            for suffix in ("A6B7C8D9", "a6b7c8d9", "A6B7C8D9J", "987ZX"):
                serial = f"{prefix:04x}{suffix}"
                with self.subTest(serial=serial):
                    self.assertEqual(get_dtu_model_name(serial), model.value)

    def test_unknown_and_invalid_serials(self):
        """Return Unknown for unrecognized prefixes and malformed serials."""
        for serial in ("FFFFA6B7C8D9", "ZZZZ12345", "", "4", "41", "414"):
            with self.subTest(serial=serial):
                self.assertEqual(get_dtu_model_name(serial), DTUType.UNKNOWN.value)

    def test_binary_model_type_api(self):
        """Keep byte-based type identification compatible with existing callers."""
        self.assertIs(get_dtu_model_type(bytes.fromhex("4143A6B7C8D9")), DTUType.DTUBI)
        with self.assertRaisesRegex(ValueError, "Unknown DTU"):
            get_dtu_model_type(bytes.fromhex("FFFFA6B7C8D9"))

    def test_solenso_slt_v2(self):
        """Recognize the Solenso prefix without decoding its alphanumeric suffix."""
        for serial in ("D010987ZX", "d010987zx"):
            with self.subTest(serial=serial):
                self.assertEqual(
                    get_dtu_model_name(serial), DTUType.SOLENSO_SLT_V2.value
                )
        self.assertIs(get_dtu_model_type(bytes.fromhex("D010")), DTUType.SOLENSO_SLT_V2)
