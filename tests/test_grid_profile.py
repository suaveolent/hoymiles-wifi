"""Verify read-only grid-profile retrieval using sanitized packet captures."""

import json
import unittest
from dataclasses import asdict
from pathlib import Path
from unittest.mock import AsyncMock, patch

from crcmod import mkCrcFun
from google.protobuf.json_format import MessageToDict
from google.protobuf.message import Message

from hoymiles_wifi.__main__ import main
from hoymiles_wifi.const import (
    CMD_COMMAND_RES_DTO,
    CMD_DEV_CONFIG_FETCH_RES_DTO,
)
from hoymiles_wifi.crypt_util import crypt_data
from hoymiles_wifi.dtu import DTU
from hoymiles_wifi.protobuf import APPInfomationData_pb2, CommandPB_pb2, DevConfig_pb2

DTU_SERIAL = "4143A6B7C8D9"
INVERTER_SERIAL = "1412E5F607AB"
HOST_TIME = 1706514105
FIXTURE = json.loads((Path(__file__).parent / "fixtures/grid_profile.json").read_text())
CRC16 = mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)


def capture_response():
    """Decode the sanitized binary reply, including its non-UTF-8 configuration."""
    return DevConfig_pb2.DevConfigFetchReqDTO.FromString(
        bytes.fromhex(FIXTURE["fetch_response"])[10:]
    )


def responding_dtu():
    """Provide synthetic discovery and the captured read acknowledgement."""
    dtu = DTU("unused")
    info = APPInfomationData_pb2.APPInfoDataReqDTO(dtu_serial_number=DTU_SERIAL)
    info.pv_info.add(
        pv_serial_number=int(INVERTER_SERIAL, 16),
        pv_grid_profile_code=3073,
        pv_grid_profile=8192,
    )
    dtu.async_app_information_data = AsyncMock(return_value=info)
    ack = CommandPB_pb2.CommandReqDTO.FromString(
        bytes.fromhex(FIXTURE["read_acknowledgement"])[10:]
    )
    dtu.async_send_request = AsyncMock(side_effect=[ack, capture_response()])
    return dtu


class GridProfileTests(unittest.IsolatedAsyncioTestCase):
    """Check read-only wire commands, complete results, and failure handling."""

    async def test_sanitized_capture_and_wire_requests(self):
        """Use local headers with captured payloads and preserve complete binary data."""
        dtu = responding_dtu()
        response = dtu.parse_response(
            bytes.fromhex(FIXTURE["fetch_response"]),
            DevConfig_pb2.DevConfigFetchReqDTO,
            False,
        )
        self.assertIsNotNone(response)
        with patch(
            "hoymiles_wifi.dtu.time.time",
            side_effect=[HOST_TIME, HOST_TIME, HOST_TIME + 7],
        ):
            result = await dtu.async_get_grid_profile(INVERTER_SERIAL.lower())
        self.assertIsInstance(result, DevConfig_pb2.DevConfigFetchReqDTO)
        self.assertEqual(result, response)
        self.assertEqual(result.dev_sn, INVERTER_SERIAL)
        self.assertEqual(result.data, response.data)
        self.assertEqual(len(result.data), 122)
        self.assertEqual(result.cfg_data, b"")
        for call, fixture_name in zip(
            dtu.async_send_request.call_args_list,
            ["read_request", "fetch_request"],
            strict=True,
        ):
            command, request, _ = call.args
            expected = bytes.fromhex(FIXTURE[fixture_name])
            self.assertEqual(request.SerializeToString(), expected[10:])
            expected = b"HM" + command + expected[4:]
            dtu.sequence = int.from_bytes(expected[4:6], "big") - 1
            self.assertEqual(
                dtu.generate_message(command, request, False, 0, 0), expected
            )
        self.assertEqual(dtu.async_send_request.call_args_list[0].args[0], b"\xa3\x05")
        self.assertEqual(dtu.async_send_request.call_args_list[1].args[0], b"\xa3\x07")
        self.assertEqual(dtu.async_send_request.call_args_list[0].args[1].action, 41)
        self.assertEqual(
            [c.args[0] for c in dtu.async_send_request.call_args_list],
            [CMD_COMMAND_RES_DTO, CMD_DEV_CONFIG_FETCH_RES_DTO],
        )

    async def test_rejected_or_missing_acknowledgement(self):
        """Stop before fetching when the read command is not acknowledged."""
        ack = CommandPB_pb2.CommandReqDTO(action=41, tid=HOST_TIME, dtu_sn=DTU_SERIAL)
        failures = [None]
        for field, value in [
            ("err_code", 1),
            ("action", 14),
            ("tid", 99),
            ("dtu_sn", "other"),
        ]:
            bad = CommandPB_pb2.CommandReqDTO()
            bad.CopyFrom(ack)
            setattr(bad, field, value)
            failures.append(bad)
        for response in failures:
            with self.subTest(response=response):
                dtu = responding_dtu()
                dtu.async_send_request = AsyncMock(return_value=response)
                with patch("hoymiles_wifi.dtu.time.time", return_value=HOST_TIME):
                    self.assertIsNone(await dtu.async_get_grid_profile(INVERTER_SERIAL))
                dtu.async_send_request.assert_awaited_once()

    async def test_wrong_target_and_invalid_configuration(self):
        """Reject stale transactions, different devices, corrupt data, and invalid pages."""
        for field, value in [
            ("transaction_id", 99),
            ("dtu_sn", "other"),
            ("dev_sn", "other"),
            ("rule_type", 2),
            ("current_package", 1),
            ("total_packages", 0),
            ("total_packages", 257),
            ("data", b""),
            ("crc", 0),
        ]:
            with self.subTest(field=field, value=value):
                dtu = responding_dtu()
                bad = capture_response()
                setattr(bad, field, value)
                ack = CommandPB_pb2.CommandReqDTO(
                    action=41, tid=HOST_TIME, dtu_sn=DTU_SERIAL
                )
                dtu.async_send_request = AsyncMock(side_effect=[ack, bad])
                with patch("hoymiles_wifi.dtu.time.time", return_value=HOST_TIME):
                    self.assertIsNone(await dtu.async_get_grid_profile(INVERTER_SERIAL))

    async def test_multiple_pages_and_configuration_crc(self):
        """Assemble binary data and configuration bytes before checking their CRCs."""
        original = capture_response()
        pages = []
        for index, data in enumerate([original.data[:61], original.data[61:]]):
            page = capture_response()
            page.data = data
            page.total_packages = 2
            page.current_package = index
            page.cfg_data = [b"\xff", b"\x80"][index]
            page.cfg_crc = CRC16(b"\xff\x80")
            pages.append(page)
        dtu = responding_dtu()
        ack = CommandPB_pb2.CommandReqDTO(action=41, tid=HOST_TIME, dtu_sn=DTU_SERIAL)
        dtu.async_send_request = AsyncMock(side_effect=[ack, *pages])
        with patch("hoymiles_wifi.dtu.time.time", return_value=HOST_TIME):
            result = await dtu.async_get_grid_profile(INVERTER_SERIAL)
        self.assertEqual(result.data, original.data)
        self.assertEqual(result.cfg_data, b"\xff\x80")
        self.assertEqual(
            [
                c.args[1].current_package
                for c in dtu.async_send_request.call_args_list[1:]
            ],
            [0, 1],
        )
        pages[-1].cfg_data = b"\x81"
        dtu.async_send_request = AsyncMock(side_effect=[ack, *pages])
        with patch("hoymiles_wifi.dtu.time.time", return_value=HOST_TIME):
            self.assertIsNone(await dtu.async_get_grid_profile(INVERTER_SERIAL))

    async def test_missing_or_inconsistent_later_page(self):
        """Never return partial data when the remaining pages cannot be validated."""
        first = capture_response()
        first.total_packages = 2
        second = capture_response()
        second.total_packages = 3
        second.current_package = 1
        for later in [None, second]:
            dtu = responding_dtu()
            ack = CommandPB_pb2.CommandReqDTO(
                action=41, tid=HOST_TIME, dtu_sn=DTU_SERIAL
            )
            dtu.async_send_request = AsyncMock(side_effect=[ack, first, later])
            with patch("hoymiles_wifi.dtu.time.time", return_value=HOST_TIME):
                self.assertIsNone(await dtu.async_get_grid_profile(INVERTER_SERIAL))
            self.assertEqual(dtu.async_send_request.await_count, 3)

    async def test_initial_fetch_waits_for_inverter_read(self):
        """Retry only the readback query, without repeating the inverter command."""
        dtu = responding_dtu()
        ack = CommandPB_pb2.CommandReqDTO(action=41, tid=HOST_TIME, dtu_sn=DTU_SERIAL)
        dtu.async_send_request = AsyncMock(side_effect=[ack, None, capture_response()])
        with (
            patch("hoymiles_wifi.dtu.time.time", return_value=HOST_TIME),
            patch("hoymiles_wifi.dtu.asyncio.sleep", new_callable=AsyncMock) as sleep,
        ):
            self.assertIsNotNone(await dtu.async_get_grid_profile(INVERTER_SERIAL))
        sleep.assert_awaited_once_with(2)
        self.assertEqual(
            sum(
                c.args[0] == CMD_COMMAND_RES_DTO
                for c in dtu.async_send_request.call_args_list
            ),
            1,
        )

    async def test_readback_timeout_is_bounded(self):
        """Return no result after three unsuccessful initial fetches."""
        dtu = responding_dtu()
        ack = CommandPB_pb2.CommandReqDTO(action=41, tid=HOST_TIME, dtu_sn=DTU_SERIAL)
        dtu.async_send_request = AsyncMock(side_effect=[ack, None, None, None])
        with (
            patch("hoymiles_wifi.dtu.time.time", return_value=HOST_TIME),
            patch("hoymiles_wifi.dtu.asyncio.sleep", new_callable=AsyncMock) as sleep,
        ):
            self.assertIsNone(await dtu.async_get_grid_profile(INVERTER_SERIAL))
        self.assertEqual(sleep.await_count, 2)
        self.assertEqual(dtu.async_send_request.await_count, 4)

    async def test_missing_discovery_or_inverter(self):
        """Do not send grid commands without confirming the target inverter."""
        for info in [
            None,
            APPInfomationData_pb2.APPInfoDataReqDTO(),
            APPInfomationData_pb2.APPInfoDataReqDTO(dtu_serial_number=DTU_SERIAL),
        ]:
            dtu = responding_dtu()
            dtu.async_app_information_data.return_value = info
            with patch("hoymiles_wifi.dtu.time.time", return_value=HOST_TIME):
                self.assertIsNone(await dtu.async_get_grid_profile(INVERTER_SERIAL))
            dtu.async_send_request.assert_not_awaited()

    async def test_clock_offset_and_encrypted_transport(self):
        """Adjust device timestamps while preserving transaction IDs and AES routing."""
        dtu = responding_dtu()
        dtu.dtu_time_offset = -120
        dtu.is_encrypted = True
        dtu.enc_rand = bytes(range(16))
        with patch("hoymiles_wifi.dtu.time.time", return_value=HOST_TIME):
            self.assertIsNotNone(await dtu.async_get_grid_profile(INVERTER_SERIAL))
        for call in dtu.async_send_request.call_args_list:
            command, request, _ = call.args
            time_field = "time" if command == CMD_COMMAND_RES_DTO else "response_time"
            tid_field = "tid" if command == CMD_COMMAND_RES_DTO else "transaction_id"
            self.assertEqual(getattr(request, time_field), HOST_TIME - 120)
            self.assertEqual(getattr(request, tid_field), HOST_TIME)
            frame = dtu.generate_message(command, request, False, 0, 0)
            payload = crypt_data(
                False,
                dtu.enc_rand,
                int.from_bytes(command, "big"),
                int.from_bytes(frame[4:6], "big"),
                frame[10:],
            )
            self.assertEqual(payload, request.SerializeToString())

    async def test_cli_json_and_missing_serial(self):
        """Both commands require a serial and expose their distinct JSON results."""
        for command, method in (
            ("get-grid-profile", "async_get_grid_profile"),
            ("get-grid-profile-decoded", "async_get_grid_profile_decoded"),
        ):
            with self.subTest(command=command):
                dtu = responding_dtu()
                with patch("hoymiles_wifi.dtu.time.time", return_value=HOST_TIME):
                    result = await getattr(dtu, method)(INVERTER_SERIAL)
                arguments = [
                    "hoymiles-wifi",
                    "--host",
                    "unused",
                    "--inverter-serial",
                    INVERTER_SERIAL,
                    "--as-json",
                    command,
                ]
                with (
                    patch("sys.argv", arguments),
                    patch.object(
                        DTU, method, new_callable=AsyncMock, return_value=result
                    ) as getter,
                    patch("builtins.print") as output,
                ):
                    await main()
                getter.assert_awaited_once_with(INVERTER_SERIAL)
                self.assertEqual(
                    json.loads(output.call_args.args[0]),
                    MessageToDict(result)
                    if isinstance(result, Message)
                    else asdict(result),
                )
                with (
                    patch("sys.argv", ["hoymiles-wifi", "--host", "unused", command]),
                    patch("sys.stderr"),
                    self.assertRaises(SystemExit) as error,
                ):
                    await main()
                self.assertEqual(error.exception.code, 2)

    async def test_explicit_decoded_readback(self):
        """Interpret the raw result only through the decoded readback method."""
        dtu = responding_dtu()
        response = capture_response()
        response.data = b"".join(
            response.data[index : index + 2][::-1]
            for index in range(0, len(response.data), 2)
        )
        dtu.async_get_grid_profile = AsyncMock(return_value=response)
        result = await dtu.async_get_grid_profile_decoded(INVERTER_SERIAL)
        dtu.async_get_grid_profile.assert_awaited_once_with(INVERTER_SERIAL)
        self.assertEqual(result.grid_profile_name, "AT_TOR_Erzeuger_Q(U)")
        self.assertEqual(result.grid_profile_version, "2.0.0")
        self.assertEqual(result.decoded.byte_order, "big")
        self.assertEqual(result.decoded.sections[0].name, "voltage")
        dtu.async_get_grid_profile = AsyncMock(return_value=None)
        self.assertIsNone(await dtu.async_get_grid_profile_decoded(INVERTER_SERIAL))
