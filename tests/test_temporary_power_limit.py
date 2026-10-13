"""Verify runtime power-limit encoding and transport without contacting hardware."""

import struct
import unittest
from unittest.mock import AsyncMock, patch

from hoymiles_wifi.__main__ import async_set_power_limit_temporary, main
from hoymiles_wifi.const import CMD_COMMAND_RES_DTO
from hoymiles_wifi.crypt_util import crypt_data
from hoymiles_wifi.dtu import DTU
from hoymiles_wifi.protobuf import CommandPB_pb2


class TemporaryPowerLimitTests(unittest.IsolatedAsyncioTestCase):
    """Check the upstream wire contract and failure behavior."""

    async def test_wire_payload_and_rounding(self):
        """Encode watt values as tenths, rounding half upwards."""
        dtu = DTU("unused")
        ack = CommandPB_pb2.CommandReqDTO(action=211, err_code=0)
        dtu.async_send_request = AsyncMock(return_value=ack)
        for watts, expected in [(0.1, 1), (10, 100), (300, 3000),
                                (12.34, 123), (12.35, 124), (3276.7, 32767)]:
            with self.subTest(watts=watts), patch("hoymiles_wifi.dtu.time.time", return_value=1234):
                self.assertIs(await dtu.async_set_power_limit_temporary(watts), ack)
                command, request, response_type = dtu.async_send_request.call_args.args
                self.assertEqual(command, CMD_COMMAND_RES_DTO)
                self.assertIs(response_type, CommandPB_pb2.CommandReqDTO)
                decoded = CommandPB_pb2.CommandResDTO.FromString(request.SerializeToString())
                self.assertEqual(decoded.action, 211)
                self.assertEqual(decoded.package_nub, 1)
                self.assertEqual(decoded.time, 1234)
                self.assertEqual(decoded.tid, 1234)
                self.assertEqual(decoded.data, f"S:1,P:{expected}\r")

    async def test_invalid_values_do_not_send(self):
        """Reject inputs that cannot produce a valid runtime command."""
        dtu = DTU("unused")
        dtu.async_send_request = AsyncMock()
        for value in [None, "300", True, False, -1, 0, 0.09, 3276.8,
                      float("nan"), float("inf"), float("-inf")]:
            with self.subTest(value=value):
                self.assertIsNone(await dtu.async_set_power_limit_temporary(value))
        dtu.async_send_request.assert_not_awaited()

    async def test_transport_result_is_preserved(self):
        """Preserve both DTU errors and missing responses without fallback."""
        dtu = DTU("unused")
        for result in [None, CommandPB_pb2.CommandReqDTO(action=211, err_code=1)]:
            dtu.async_send_request = AsyncMock(return_value=result)
            self.assertIs(await dtu.async_set_power_limit_temporary(300), result)
            dtu.async_send_request.assert_awaited_once()

    async def test_plain_and_encrypted_frames(self):
        """Route action 211 through the existing AES-GCM command transport."""
        for encrypted in [False, True]:
            with self.subTest(encrypted=encrypted):
                dtu = DTU("unused", is_encrypted=encrypted, enc_rand=bytes(range(16)))
                dtu.async_send_request = AsyncMock()
                await dtu.async_set_power_limit_temporary(300)
                command, request, _ = dtu.async_send_request.call_args.args
                frame = dtu.generate_message(command, request, False, 0, 0)
                self.assertEqual(frame[:4], b"HM\xa3\x05")
                payload = frame[10:]
                if encrypted:
                    payload = crypt_data(False, dtu.enc_rand, 0xA305,
                                         struct.unpack(">H", frame[4:6])[0], payload)
                self.assertEqual(payload, request.SerializeToString())

    async def test_persistent_setter_still_uses_action_8(self):
        """Keep the existing percentage command independent of runtime watts."""
        dtu = DTU("unused")
        dtu.async_send_request = AsyncMock()
        await dtu.async_set_power_limit(50)
        request = dtu.async_send_request.call_args.args[1]
        self.assertEqual(request.action, 8)
        self.assertEqual(request.data, "A:500,B:0,C:0\r")

    async def test_cli_wrapper(self):
        """Pass CLI watts unchanged and skip missing noninteractive input."""
        dtu = DTU("unused")
        dtu.async_set_power_limit_temporary = AsyncMock()
        await async_set_power_limit_temporary(dtu, 300, interactive_mode=False)
        dtu.async_set_power_limit_temporary.assert_awaited_once_with(300)
        dtu.async_set_power_limit_temporary.reset_mock()
        with patch("builtins.print"):
            self.assertIsNone(await async_set_power_limit_temporary(dtu, interactive_mode=False))
        dtu.async_set_power_limit_temporary.assert_not_awaited()

    async def test_cli_dispatch(self):
        """Parse the new command and watt argument without contacting a DTU."""
        arguments = [
            "hoymiles-wifi", "--host", "unused", "--disable-interactive",
            "--power-limit-watts", "123.4", "set-power-limit-temporary",
        ]
        with (
            patch("sys.argv", arguments),
            patch.object(DTU, "async_set_power_limit_temporary", new_callable=AsyncMock) as setter,
            patch("builtins.print"),
        ):
            await main()
        setter.assert_awaited_once_with(123.4)
