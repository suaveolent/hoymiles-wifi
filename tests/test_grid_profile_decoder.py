"""Check grid-profile decoding against local and cloud payloads."""

import unittest
from dataclasses import asdict

from hoymiles_wifi.grid_profile import (
    decode_grid_profile,
    get_grid_profile_name,
    get_grid_profile_version,
)

LOCAL_DATA = bytes.fromhex(
    "0c012000000b08fc0730000f09f90001023f00320a55000809f9"
    "10001388128e0001141e0001200000013003025809cb07a31392128e"
    "400007d0001050000001139c019000326004000109e20a10087e"
    "800000010844012c08a0096f09b4012c90000000005f"
    "b000000001f4005f700200012710a002000000000000"
)


class GridProfileDecoderTests(unittest.TestCase):
    """Verify units, byte order, signed settings, and incomplete layouts."""

    def test_app_info_identifiers(self):
        """Decode the confirmed Austrian Q(U) code without guessing other variants."""
        self.assertEqual(get_grid_profile_name(3073), "AT_TOR_Erzeuger_Q(U)")
        self.assertIsNone(get_grid_profile_name(768))
        self.assertIsNone(get_grid_profile_name(41509))
        self.assertEqual(get_grid_profile_version(8192), "2.0.0")
        self.assertEqual(get_grid_profile_version(0x2103), "2.1.3")

    def test_local_configuration(self):
        """Decode the hardware reply into scaled, named sections."""
        profile = decode_grid_profile(LOCAL_DATA, 3073, 8192)
        self.assertEqual(profile.byte_order, "big")
        self.assertEqual(profile.version, "2.0.0")
        sections = {section.name: section for section in profile.sections}
        self.assertEqual(len(sections), 12)
        voltage = {value.name: value for value in sections["voltage"].values}
        self.assertEqual(voltage["nominal_voltage"].value, 230)
        self.assertEqual(voltage["low_voltage_1"].value, 184)
        self.assertEqual(voltage["low_voltage_1_trip_time"].value, 1.5)
        self.assertEqual(voltage["nominal_voltage"].unit, "V")
        frequency = sections["frequency"].values
        self.assertEqual(frequency[0].value, 50)
        self.assertEqual(frequency[1].value, 47.5)
        self.assertEqual(sections["reconnection"].values[0].value, 60)
        self.assertEqual(sections["volt_var"].values[0].value, 1)
        self.assertEqual(profile.undecoded_hex, "0000")
        self.assertIsInstance(asdict(profile)["sections"], list)

    def test_cloud_word_order(self):
        """Word-swapped cloud data decodes to the same settings."""
        swapped = b"".join(
            LOCAL_DATA[i : i + 2][::-1] for i in range(0, len(LOCAL_DATA), 2)
        )
        local = decode_grid_profile(LOCAL_DATA, 3073, 8192)
        cloud = decode_grid_profile(swapped, 3073, 8192)
        self.assertEqual(cloud.byte_order, "little")
        self.assertEqual(cloud.sections, local.sections)
        self.assertEqual(cloud.version, local.version)

    def test_signed_values(self):
        """Negative power factors retain their sign and their raw wire value."""
        data = bytes.fromhex("0c01200090000001ffa1")
        value = decode_grid_profile(data, 3073, 8192).sections[0].values[1]
        self.assertEqual(value.value, -0.95)
        self.assertEqual(value.raw_value, 65441)

    def test_unknown_and_truncated_sections(self):
        """Preserve unrecognized bytes without inventing values or offsets."""
        for tail in ("00ff08fc", "000b08fc", "ff", "6005", ""):
            with self.subTest(tail=tail):
                data = bytes.fromhex("0c012000" + tail)
                profile = decode_grid_profile(data, 3073, 8192)
                self.assertEqual(profile.sections, [])
                self.assertEqual(profile.undecoded_hex, tail)
        for data in (b"", b"\x00", bytes.fromhex("00002000")):
            self.assertIsNone(decode_grid_profile(data, 3073, 8192))
