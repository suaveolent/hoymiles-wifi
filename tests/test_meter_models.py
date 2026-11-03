"""Verify meter recognition and phase classification using synthetic serials."""

import unittest
from unittest.mock import patch

from hoymiles_wifi.hoymiles import (
    MeterType,
    get_meter_model_name,
    get_meter_model_type,
)


class MeterModelTests(unittest.TestCase):
    """Recognize three-phase meters without relying on live phase readings."""

    def test_4f05_is_recognized_without_unknown_meter_errors(self):
        """Recognize the reported prefix even when the exact model is unknown."""
        for serial in ("4F05B72C6D91", "4f05b72c6d91"):
            with (
                self.subTest(serial=serial),
                patch("hoymiles_wifi.hoymiles.logger.error") as error,
            ):
                model = get_meter_model_type(bytes.fromhex(serial))
                self.assertIs(model, MeterType.THREE_PHASE)
                self.assertTrue(model.is_three_phase)
                self.assertEqual(get_meter_model_name(serial), "Three-phase meter")
                error.assert_not_called()

    def test_existing_meter_names_and_phase_counts(self):
        """Preserve known model names and distinguish single-phase meters."""
        for serial, model, three_phase in [
            ("10C0B72C6D91", MeterType.DDSU666, False),
            ("37FFB72C6D91", MeterType.DTSU666, True),
        ]:
            with self.subTest(serial=serial):
                detected = get_meter_model_type(bytes.fromhex(serial))
                self.assertIs(detected, model)
                self.assertEqual(get_meter_model_name(serial), model.value)
                self.assertIs(detected.is_three_phase, three_phase)

    def test_unknown_prefix_is_not_assumed_three_phase(self):
        """Keep unsupported meters distinguishable from known three-phase meters."""
        with self.assertRaisesRegex(ValueError, "Unknown Meter"):
            get_meter_model_type(bytes.fromhex("FFFFB72C6D91"))
