"""Verify meter recognition using synthetic serials."""

import unittest
from unittest.mock import patch

from hoymiles_wifi.hoymiles import (
    MeterType,
    get_meter_model_name,
    get_meter_model_type,
)


class MeterModelTests(unittest.TestCase):
    """Recognize supported meter prefixes and preserve known model names."""

    def test_4f05_is_recognized_without_unknown_meter_errors(self):
        """Recognize the reported prefix even when the exact model is unknown."""
        for serial in ("4F05B72C6D91", "4f05b72c6d91"):
            with (
                self.subTest(serial=serial),
                patch("hoymiles_wifi.hoymiles.logger.error") as error,
            ):
                model = get_meter_model_type(bytes.fromhex(serial))
                self.assertIs(model, MeterType.THREE_PHASE)
                self.assertEqual(get_meter_model_name(serial), "Three-phase meter")
                error.assert_not_called()

    def test_existing_meter_names(self):
        """Preserve known model names."""
        for serial, model in [
            ("10C0B72C6D91", MeterType.DDSU666),
            ("37FFB72C6D91", MeterType.DTSU666),
        ]:
            with self.subTest(serial=serial):
                detected = get_meter_model_type(bytes.fromhex(serial))
                self.assertIs(detected, model)
                self.assertEqual(get_meter_model_name(serial), model.value)

    def test_unknown_prefix_is_rejected(self):
        """Keep unsupported meters distinguishable from known three-phase meters."""
        with self.assertRaisesRegex(ValueError, "Unknown Meter"):
            get_meter_model_type(bytes.fromhex("FFFFB72C6D91"))

    def test_unknown_model_name(self):
        """Use the meter enum fallback while keeping type lookups strict."""
        self.assertEqual(get_meter_model_name("FFFFA6B7C8D9"), MeterType.UNKNOWN.value)
