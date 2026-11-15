"""Keep cloud control commands plaintext on DTUs with encrypted data polling."""

import struct
import unittest
from unittest.mock import AsyncMock, patch

from crcmod import mkCrcFun

from hoymiles_wifi.const import (
    CMD_CLOUD_COMMAND_REQ_DTO,
    CMD_CLOUD_COMMAND_RES_DTO,
    CMD_COMMAND_RES_DTO,
    CMD_REAL_RES_DTO,
)
from hoymiles_wifi.crypt_util import crypt_data
from hoymiles_wifi.dtu import DTU, NetworkState
from hoymiles_wifi.protobuf import CommandPB_pb2

INVERTER_SERIAL = "1144A6B7C8D9"
KEY = bytes(range(16))


class CloudControlEncryptionTests(unittest.IsolatedAsyncioTestCase):
    """Exercise framing and response parsing without toggling shared encryption state."""

    async def test_cloud_controls_remain_plaintext(self):
        """Send all 0x2305 actions unencrypted, preserving their payloads and routing."""
        methods = (
            ("async_restart_dtu", (), 1),
            ("async_turn_on_inverter", (INVERTER_SERIAL,), 6),
            ("async_turn_off_inverter", (INVERTER_SERIAL,), 7),
            ("async_reboot_inverter", (INVERTER_SERIAL,), 8195),
            ("async_update_dtu_firmware", ("https://example.invalid/firmware.bin",), 2),
        )
        for encrypted in (False, True):
            for method, args, action in methods:
                with self.subTest(encrypted=encrypted, method=method):
                    dtu = DTU("test.invalid", is_encrypted=encrypted, enc_rand=KEY)
                    ack = CommandPB_pb2.CommandReqDTO(action=action)
                    dtu.async_send_request = AsyncMock(return_value=ack)
                    self.assertIs(await getattr(dtu, method)(*args), ack)
                    command, request, response_type = (
                        dtu.async_send_request.call_args.args
                    )
                    self.assertEqual(command, CMD_CLOUD_COMMAND_RES_DTO)
                    self.assertIs(response_type, CommandPB_pb2.CommandReqDTO)
                    with patch("hoymiles_wifi.dtu.crypt_data") as crypt:
                        frame = dtu.generate_message(command, request, False, 0, 0)
                        crypt.assert_not_called()
                    self.assertEqual(frame[:4], b"HM\x23\x05")
                    self.assertEqual(frame[10:], request.SerializeToString())
                    sequence, crc, length = struct.unpack(">HHH", frame[4:10])
                    self.assertEqual(sequence, 1)
                    self.assertEqual(length, len(frame))
                    expected_crc = mkCrcFun(
                        0x18005, rev=True, initCrc=0xFFFF, xorOut=0
                    )(frame[10:])
                    self.assertEqual(crc, expected_crc)
                    decoded = CommandPB_pb2.CommandResDTO.FromString(frame[10:])
                    self.assertEqual(decoded.action, action)
                    if args and method != "async_update_dtu_firmware":
                        self.assertEqual(
                            list(decoded.mi_to_sn), [int(INVERTER_SERIAL, 16)]
                        )
                    self.assertIs(dtu.is_encrypted, encrypted)
                    self.assertEqual(dtu.enc_rand, KEY)

    async def test_plaintext_cloud_acknowledgement(self):
        """Accept 0x2205 replies without expecting an AES tag or decrypting them."""
        for encrypted in (False, True):
            for error in (0, 1):
                with self.subTest(encrypted=encrypted, error=error):
                    dtu = DTU("test.invalid", is_encrypted=encrypted, enc_rand=KEY)
                    ack = CommandPB_pb2.CommandReqDTO(action=6, err_code=error)
                    payload = ack.SerializeToString()
                    crc = mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0)(payload)
                    frame = (
                        b"HM"
                        + CMD_CLOUD_COMMAND_REQ_DTO
                        + struct.pack(">HHH", 7, crc, len(payload) + 10)
                        + payload
                    )
                    with patch("hoymiles_wifi.dtu.crypt_data") as crypt:
                        parsed = dtu.parse_response(
                            frame, CommandPB_pb2.CommandReqDTO, False
                        )
                        crypt.assert_not_called()
                    self.assertEqual(parsed, ack)
                    self.assertIs(dtu.get_state(), NetworkState.Online)
                    self.assertIs(dtu.is_encrypted, encrypted)
                    self.assertEqual(dtu.enc_rand, KEY)

    async def test_data_and_local_commands_stay_encrypted_after_cloud_control(self):
        """A plaintext control must not disable encryption for subsequent requests."""
        dtu = DTU("test.invalid", is_encrypted=True, enc_rand=KEY)
        dtu.async_send_request = AsyncMock(return_value=None)
        await dtu.async_restart_dtu()
        command, request, _ = dtu.async_send_request.call_args.args
        dtu.generate_message(command, request, False, 0, 0)
        for method, args, expected_command in (
            ("async_get_real_data_new", (), CMD_REAL_RES_DTO),
            ("async_set_power_limit", (50,), CMD_COMMAND_RES_DTO),
            ("async_set_power_limit_temporary", (300,), CMD_COMMAND_RES_DTO),
        ):
            with self.subTest(method=method):
                await getattr(dtu, method)(*args)
                command, request, _ = dtu.async_send_request.call_args.args
                self.assertEqual(command, expected_command)
                frame = dtu.generate_message(command, request, False, 0, 0)
                tag, sequence = struct.unpack(">HH", frame[2:6])
                decrypted = crypt_data(False, KEY, tag, sequence, frame[10:])
                self.assertEqual(decrypted, request.SerializeToString())
                length = struct.unpack(">H", frame[8:10])[0]
                self.assertEqual(len(frame), length + 16)
                self.assertTrue(dtu.is_encrypted)
                self.assertEqual(dtu.enc_rand, KEY)
