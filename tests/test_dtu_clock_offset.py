"""Verify clock offsets across requests, pagination, and CLI argument parsing."""

import unittest
from unittest.mock import AsyncMock, patch

from hoymiles_wifi.__main__ import async_is_encrypted, main
from hoymiles_wifi.dtu import DTU
from hoymiles_wifi.hoymiles import BMSWorkingMode
from hoymiles_wifi.protobuf import (
    APPInfomationData_pb2,
    GetConfig_pb2,
)

HOST_TIME = 1800000000
GATEWAY_SERIAL = 0x4301AB23CD45
INVERTER_SERIAL = 0x2100EF6789AB


class DTUClockOffsetTests(unittest.IsolatedAsyncioTestCase):
    """Keep timestamp corrections separate from transactions and transport timing."""

    async def test_timestamped_requests(self):
        """Apply positive, negative, and default offsets to reads and controls."""
        requests = [
            ("async_get_real_data", (), {}, "time"),
            ("async_get_real_data_new", (), {}, "time"),
            ("async_get_config", (), {}, "time"),
            ("async_network_info", (), {}, "time"),
            ("async_app_get_hist_power", (), {}, "requested_time"),
            ("async_set_power_limit", (50,), {}, "time"),
            ("async_set_power_limit_temporary", (300,), {}, "time"),
            ("async_set_wifi", ("test-ssid", "test-password"), {}, "time"),
            ("async_get_information_data", (), {}, "time"),
            ("async_heartbeat", (), {}, "time"),
            ("async_enable_performance_data_mode", (), {}, "time"),
            ("async_get_gateway_info", (), {}, "time"),
            ("async_get_gateway_network_info", (GATEWAY_SERIAL,), {}, "time"),
            ("async_get_energy_storage_registry", (GATEWAY_SERIAL,), {}, "time"),
            (
                "async_get_energy_storage_data",
                (GATEWAY_SERIAL, INVERTER_SERIAL),
                {},
                "time",
            ),
            (
                "async_get_energy_storage_working_mode",
                (GATEWAY_SERIAL, INVERTER_SERIAL),
                {},
                "time",
            ),
            (
                "async_set_energy_storage_working_mode",
                (GATEWAY_SERIAL, INVERTER_SERIAL, BMSWorkingMode.SELF_USE),
                {"rev_soc": 10},
                "time",
            ),
        ]
        for offset in (0, -120, 120):
            for method, args, kwargs, field in requests:
                with self.subTest(offset=offset, method=method):
                    dtu = DTU("unused", dtu_time_offset=offset)
                    dtu.async_send_request = AsyncMock(return_value=None)
                    if method == "async_set_wifi":
                        dtu.async_get_config = AsyncMock(
                            return_value=GetConfig_pb2.GetConfigReqDTO()
                        )
                    with patch("hoymiles_wifi.dtu.time.time", return_value=HOST_TIME):
                        await getattr(dtu, method)(*args, **kwargs)
                    request = dtu.async_send_request.call_args.args[1]
                    self.assertEqual(getattr(request, field), HOST_TIME + offset)
                    if "tid" in request.DESCRIPTOR.fields_by_name and request.tid:
                        self.assertEqual(request.tid, HOST_TIME)

    async def test_app_info_bootstrap_uses_host_time(self):
        """Discover the device clock even before a usable offset is available."""
        dtu = DTU("unused", dtu_time_offset=-120)
        dtu.async_send_request = AsyncMock(return_value=None)
        with patch("hoymiles_wifi.dtu.time.time", return_value=HOST_TIME):
            await dtu.async_app_information_data()
        self.assertEqual(dtu.async_send_request.call_args.args[1].time, HOST_TIME)

    async def test_paginated_request_timestamps_are_refreshed(self):
        """Refresh adjusted timestamps between live and historical data pages."""
        for method, field in [
            ("async_get_real_data_new", "time"),
            (
                "async_app_get_hist_power",
                "requested_time",
            ),
        ]:
            with self.subTest(method=method):
                dtu = DTU("unused", dtu_time_offset=-120)
                observed = []

                async def send(
                    command, request, response_class, *, observed=observed, field=field
                ):
                    observed.append((request.cp, getattr(request, field)))
                    return response_class(ap=2, cp=request.cp)

                dtu.async_send_request = AsyncMock(side_effect=send)
                with patch(
                    "hoymiles_wifi.dtu.time.time",
                    side_effect=[HOST_TIME, HOST_TIME + 3],
                ):
                    await getattr(dtu, method)()
                self.assertEqual(observed, [(0, HOST_TIME - 120), (1, HOST_TIME - 117)])

    async def test_transaction_only_commands_remain_unchanged(self):
        """Do not turn transaction IDs into adjusted device timestamps."""
        for method, args in [
            ("async_restart_dtu", ()),
            ("async_update_dtu_firmware", ()),
            ("async_turn_on_inverter", (format(INVERTER_SERIAL, "x"),)),
            ("async_turn_off_inverter", (format(INVERTER_SERIAL, "x"),)),
            ("async_reboot_inverter", (format(INVERTER_SERIAL, "x"),)),
            ("async_get_alarm_list", ()),
        ]:
            with self.subTest(method=method):
                dtu = DTU("unused", dtu_time_offset=-120)
                dtu.async_send_request = AsyncMock(return_value=None)
                with patch("hoymiles_wifi.dtu.time.time", return_value=HOST_TIME):
                    await getattr(dtu, method)(*args)
                request = dtu.async_send_request.call_args.args[1]
                self.assertEqual(request.tid, HOST_TIME)
                self.assertEqual(request.time, 0)

    async def test_discovered_clock_offset(self):
        """Report the DTU-minus-host offset for encrypted and plaintext devices."""
        for encrypted in (False, True):
            for offset in (-120, 0, 120):
                with self.subTest(encrypted=encrypted, offset=offset):
                    info = APPInfomationData_pb2.APPInfoDataReqDTO(
                        timestamp=HOST_TIME + offset
                    )
                    info.dtu_info.dfs = (1 << 25) if encrypted else 0
                    info.dtu_info.enc_rand = bytes(range(16))
                    dtu = DTU("unused")
                    dtu.async_app_information_data = AsyncMock(return_value=info)
                    with patch(
                        "hoymiles_wifi.__main__.time.time", return_value=HOST_TIME
                    ):
                        result = await async_is_encrypted(dtu)
                    self.assertEqual(result["dtu_time_offset"], offset)
                    self.assertEqual(result["is_encrypted"], encrypted)
                    self.assertEqual("enc_rand" in result, encrypted)

    async def test_discovery_failure(self):
        """Do not report an invented clock offset when discovery fails."""
        dtu = DTU("unused")
        dtu.async_app_information_data = AsyncMock(return_value=None)
        self.assertIsNone(await async_is_encrypted(dtu))

    async def test_cli_signed_offsets(self):
        """Accept minus signs both as a separate value and after an equals sign."""
        for option, expected in [
            (["--dtu-time-offset", "-120"], -120),
            (["--dtu-time-offset=-120"], -120),
            (["--dtu-time-offset", "120"], 120),
            ([], 0),
        ]:
            with self.subTest(option=option):
                dtu = DTU("unused")
                dtu.async_network_info = AsyncMock(return_value="ok")
                args = ["hoymiles-wifi", "--host", "unused", *option, "network-info"]
                with (
                    patch("sys.argv", args),
                    patch(
                        "hoymiles_wifi.__main__.DTU", return_value=dtu
                    ) as constructor,
                    patch("builtins.print"),
                ):
                    await main()
                self.assertEqual(
                    constructor.call_args.kwargs["dtu_time_offset"], expected
                )
                dtu.async_network_info.assert_awaited_once()
