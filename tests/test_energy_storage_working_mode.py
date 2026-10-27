"""Verify working-mode readback using captures with randomized synthetic serials."""

import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from crcmod import mkCrcFun
from hoymiles_wifi.__main__ import async_get_energy_storage_working_mode, main
from hoymiles_wifi.const import CMD_ES_CONFIG_FETCH_RES_DTO
from hoymiles_wifi.dtu import DTU
from hoymiles_wifi.protobuf import CommDevCfg_pb2, ESParaSet_pb2

GATEWAY_SERIAL = 0x4301a79efc3c
INVERTER_SERIAL = 0x21003cef1a8a
FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures/energy_storage_working_mode.json").read_text()
)
CRC16 = mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)


def make_page(payload, page=0, pages=1):
    """Wrap one configuration fragment in the captured length/CRC format."""
    data = len(payload).to_bytes(2, "big") + payload
    return CommDevCfg_pb2.CommDevCfgFetchReqDTO(
        data=data,
        crc=CRC16(data),
        sn=INVERTER_SERIAL,
        cp=page,
        ap=pages,
        type=2,
        data_type=5,
    )


class EnergyStorageWorkingModeTests(unittest.IsolatedAsyncioTestCase):
    """Exercise captured traffic, page assembly, validation, and CLI dispatch."""

    async def test_captured_readback_and_request(self):
        """Decode sanitized self-use/backup captures and reproduce app requests."""
        dtu = DTU("unused")
        requests = [r for r in FIXTURES if r["tag"] == "c3fe"]
        responses = [r for r in FIXTURES if r["tag"] == "c2fe"]
        for request_record, response_record, expected_mode in zip(
            requests, responses, (1, 1, 3), strict=True
        ):
            with self.subTest(capture=response_record["file"], mode=expected_mode):
                request_frame = bytes.fromhex(request_record["frame"])
                response_frame = bytes.fromhex(response_record["frame"])
                response = dtu.parse_response(
                    response_frame, CommDevCfg_pb2.CommDevCfgFetchReqDTO, True
                )
                self.assertIsNotNone(response)
                dtu.async_send_request = AsyncMock(return_value=response)
                request = CommDevCfg_pb2.CommDevCfgFetchResDTO.FromString(
                    request_frame[24:]
                )
                with patch("hoymiles_wifi.dtu.time.time", return_value=request.time):
                    configuration = await dtu.async_get_energy_storage_working_mode(
                        GATEWAY_SERIAL, INVERTER_SERIAL
                    )
                self.assertEqual(configuration.emspara.mode, expected_mode)
                self.assertEqual(configuration.emspara.selfu.rev_soc, 10)
                self.assertEqual(configuration.emspara.chrg_m.max_p, 430)
                self.assertEqual(len(configuration.emspara.date.ts), 1)
                self.assertEqual(configuration.emspara.tou.trs[0].max_soc, 80)
                args, kwargs = dtu.async_send_request.call_args
                self.assertEqual(args[0], CMD_ES_CONFIG_FETCH_RES_DTO)
                self.assertEqual(args[1].SerializeToString(), request_frame[24:])
                self.assertIs(args[2], CommDevCfg_pb2.CommDevCfgFetchReqDTO)
                self.assertEqual(
                    kwargs,
                    {
                        "is_extended_format": True,
                        "dtu_serial_number": GATEWAY_SERIAL,
                        "number": 1,
                    },
                )
                dtu.sequence = int.from_bytes(request_frame[4:6], "big") - 1
                frame = dtu.generate_message(args[0], args[1], True, GATEWAY_SERIAL, 1)
                self.assertEqual(frame, request_frame)

    async def test_multiple_pages(self):
        """Strip every page prefix and assemble before protobuf decoding."""
        configuration = ESParaSet_pb2.ESParaSetBO()
        configuration.emspara.mode = 8
        configuration.emspara.tou.rev_soc = 0
        configuration.emspara.tou.trs.add(max_soc=80, min_soc=10)
        payload = configuration.SerializeToString()
        dtu = DTU("unused")
        dtu.async_send_request = AsyncMock(
            side_effect=[
                make_page(payload[:3], 0, 2),
                make_page(payload[3:], 1, 2),
            ]
        )
        self.assertEqual(
            await dtu.async_get_energy_storage_working_mode(
                GATEWAY_SERIAL, INVERTER_SERIAL
            ),
            configuration,
        )
        self.assertEqual(
            [c.args[1].cp for c in dtu.async_send_request.call_args_list], [0, 1]
        )

    async def test_invalid_pages(self):
        """Reject wrong targets, corrupt pages, and inconsistent pagination."""
        for changes in [
            {"sn": 99},
            {"cp": 1},
            {"ap": 0},
            {"ap": 257},
            {"data": b""},
            {"data": b"\x00\x05\x0a"},
            {"crc": 0},
            {"type": 1},
            {"data_type": 4},
        ]:
            with self.subTest(changes=changes):
                response = make_page(b"\x0a\x02\x08\x01")
                for name, value in changes.items():
                    setattr(response, name, value)
                dtu = DTU("unused")
                dtu.async_send_request = AsyncMock(return_value=response)
                self.assertIsNone(
                    await dtu.async_get_energy_storage_working_mode(
                        GATEWAY_SERIAL, INVERTER_SERIAL
                    )
                )
                dtu.async_send_request.assert_awaited_once()

    async def test_missing_or_inconsistent_later_page(self):
        """Never return partial settings after a timeout or changed page count."""
        for second in [
            None,
            make_page(b"\x08\x01", 1, 3),
            make_page(b"\x08\x01", 0, 2),
        ]:
            dtu = DTU("unused")
            dtu.async_send_request = AsyncMock(
                side_effect=[
                    make_page(b"\x0a\x02", 0, 2),
                    second,
                ]
            )
            self.assertIsNone(
                await dtu.async_get_energy_storage_working_mode(
                    GATEWAY_SERIAL, INVERTER_SERIAL
                )
            )
            self.assertEqual(dtu.async_send_request.await_count, 2)

    async def test_missing_response(self):
        """Return no reading when the device does not support the request."""
        dtu = DTU("unused")
        dtu.async_send_request = AsyncMock(return_value=None)
        self.assertIsNone(
            await dtu.async_get_energy_storage_working_mode(
                GATEWAY_SERIAL, INVERTER_SERIAL
            )
        )

    async def test_invalid_or_missing_mode_payload(self):
        """Do not interpret malformed or unrelated configurations as self-use."""
        for payload in [b"\xff", b"\x12\x00", b"\x0a\x00"]:
            dtu = DTU("unused")
            dtu.async_send_request = AsyncMock(return_value=make_page(payload))
            self.assertIsNone(
                await dtu.async_get_energy_storage_working_mode(
                    GATEWAY_SERIAL, INVERTER_SERIAL
                )
            )

    async def test_unknown_future_mode_is_preserved(self):
        """Preserve new firmware modes and legitimate zero reserve settings."""
        configuration = ESParaSet_pb2.ESParaSetBO()
        configuration.emspara.mode = 99
        configuration.emspara.selfu.rev_soc = 0
        dtu = DTU("unused")
        dtu.async_send_request = AsyncMock(
            return_value=make_page(configuration.SerializeToString())
        )
        self.assertEqual(
            await dtu.async_get_energy_storage_working_mode(
                GATEWAY_SERIAL, INVERTER_SERIAL
            ),
            configuration,
        )

    async def test_cli_discovery_and_json(self):
        """Associate readback with inverter serials and keep output JSON serializable."""
        dtu = DTU("unused")
        dtu.async_get_gateway_info = AsyncMock(
            return_value=SimpleNamespace(serial_number=GATEWAY_SERIAL)
        )
        dtu.async_get_energy_storage_registry = AsyncMock(
            return_value=SimpleNamespace(
                inverters=[SimpleNamespace(serial_number=INVERTER_SERIAL)]
            )
        )
        configuration = ESParaSet_pb2.ESParaSetBO()
        configuration.emspara.mode = 1
        configuration.emspara.selfu.rev_soc = 10
        dtu.async_get_energy_storage_working_mode = AsyncMock(
            return_value=configuration
        )
        response = await async_get_energy_storage_working_mode(dtu)
        self.assertEqual(
            json.loads(json.dumps(response))[str(INVERTER_SERIAL)]["emspara"]["mode"], 1
        )
        dtu.async_get_energy_storage_working_mode.assert_awaited_once_with(
            dtu_serial_number=GATEWAY_SERIAL, inverter_serial_number=INVERTER_SERIAL
        )

    async def test_cli_missing_discovery(self):
        """Stop cleanly when gateway or registry discovery fails."""
        dtu = DTU("unused")
        dtu.async_get_gateway_info = AsyncMock(return_value=None)
        dtu.async_get_energy_storage_registry = AsyncMock(return_value=None)
        self.assertIsNone(await async_get_energy_storage_working_mode(dtu))
        dtu.async_get_energy_storage_registry.assert_not_awaited()
        dtu.async_get_gateway_info.return_value = SimpleNamespace(
            serial_number=GATEWAY_SERIAL
        )
        self.assertIsNone(await async_get_energy_storage_working_mode(dtu))

    async def test_cli_dispatch(self):
        """Expose readback as a CLI command without sending any settings."""
        arguments = [
            "hoymiles-wifi",
            "--host",
            "unused",
            "--as-json",
            "get-energy-storage-working-mode",
        ]
        with (
            patch("sys.argv", arguments),
            patch(
                "hoymiles_wifi.__main__.async_get_energy_storage_working_mode",
                new_callable=AsyncMock,
            ) as getter,
            patch("builtins.print"),
        ):
            getter.return_value = {"inverter": {"emspara": {"mode": 1}}}
            await main()
        getter.assert_awaited_once()
