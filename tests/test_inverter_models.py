"""Verify inverter model names derived from serial prefixes."""

import unittest

from hoymiles_wifi.hoymiles import get_inverter_model_name


class InverterModelTests(unittest.TestCase):
    """Map serial prefixes to model names."""

    def test_known_prefixes(self):
        """Resolve reported prefixes without falling back to Unknown."""
        for serial, model in [
            ("114600000001", "HMS-600/700/800/900/1000-2T"),
            ("114400000001", "HMS-1000-2T"),
            ("114100000001", "HM-600/700/800-2T"),
        ]:
            with self.subTest(serial=serial):
                self.assertEqual(get_inverter_model_name(serial), model)
