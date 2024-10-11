"""DTU communication implementation for Hoymiles WiFi."""

from __future__ import annotations

import asyncio
import struct
import time
from datetime import datetime
from enum import Enum, IntEnum
from typing import Any

from crcmod import mkCrcFun

from hoymiles_wifi import logger
from hoymiles_wifi.const import (
    CMD_ACTION_ALARM_LIST,
    CMD_ACTION_DTU_REBOOT,
    CMD_ACTION_DTU_UPGRADE,
    CMD_ACTION_LIMIT_POWER,
    CMD_ACTION_MI_SHUTDOWN,
    CMD_ACTION_MI_START,
    CMD_APP_GET_HIST_POWER_RES,
    CMD_APP_INFO_DATA_RES_DTO,
    CMD_CLOUD_COMMAND_RES_DTO,
    CMD_COMMAND_RES_DTO,
    CMD_GET_CONFIG,
    CMD_HB_RES_DTO,
    CMD_HEADER,
    CMD_NETWORK_INFO_RES,
    CMD_REAL_DATA_RES_DTO,
    CMD_REAL_RES_DTO,
    CMD_SET_CONFIG,
    DEV_DTU,
    DTU_FIRMWARE_URL_00_01_11,
    DTU_PORT,
    OFFSET,
)
from hoymiles_wifi.hoymiles import convert_inverter_serial_number
from hoymiles_wifi.protobuf import (
    AppGetHistPower_pb2,
    APPHeartbeatPB_pb2,
    APPInfomationData_pb2,
    CommandPB_pb2,
    GetConfig_pb2,
    InfomationData_pb2,
    NetworkInfo_pb2,
    RealData_pb2,
    RealDataNew_pb2,
    SetConfig_pb2,
)
from hoymiles_wifi.utils import initialize_set_config


class NetmodeSelect(IntEnum):
    """Network mode selection."""

    WIFI = 1
    SIM = 2
    LAN = 3


class NetworkState(Enum):
    """Network state."""

    Unknown = 0
    Online = 1
    Offline = 2


class DTU:
    """DTU class."""

    def __init__(self, host: str, local_addr: str = None):
        """Initialize DTU class."""

        self.host = host
        self.local_addr = local_addr
        self.state = NetworkState.Unknown
        self.sequence = 0
        self.mutex = asyncio.Lock()

    def get_state(self) -> NetworkState:
        """Get DTU state."""

        return self.state

    def set_state(self, new_state: NetworkState):
        """Set DTU state."""

        if self.state != new_state:
            self.state = new_state
            logger.debug(f"DTU is {new_state}")

    async def async_get_real_data(self) -> RealData_pb2.RealDataResDTO | None:
        """Get real data."""

        request = RealData_pb2.RealDataResDTO()
        request.time_ymd_hms = (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S").encode("utf-8")
        )
        request.time = int(time.time())
        request.offset = OFFSET
        request.error_code = 0

        command = CMD_REAL_DATA_RES_DTO
        return await self.async_send_request(
            command, request, RealData_pb2.RealDataReqDTO
        )

    async def async_get_real_data_new(self) -> RealDataNew_pb2.RealDataNewResDTO | None:
        """Get real data new."""

        request = RealDataNew_pb2.RealDataNewResDTO()
        request.time_ymd_hms = (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S").encode("utf-8")
        )
        request.offset = OFFSET
        request.time = int(time.time())
        command = CMD_REAL_RES_DTO
        return await self.async_send_request(
            command, request, RealDataNew_pb2.RealDataNewReqDTO
        )

    async def async_get_config(self) -> GetConfig_pb2.GetConfigResDTO | None:
        """Get config."""

        request = GetConfig_pb2.GetConfigResDTO()
        request.offset = OFFSET
        request.time = int(time.time()) - 60
        command = CMD_GET_CONFIG
        return await self.async_send_request(
            command,
            request,
            GetConfig_pb2.GetConfigReqDTO,
        )

    async def async_network_info(self) -> NetworkInfo_pb2.NetworkInfoResDTO | None:
        """Get network info."""

        request = NetworkInfo_pb2.NetworkInfoResDTO()
        request.offset = OFFSET
        request.time = int(time.time())
        command = CMD_NETWORK_INFO_RES
        return await self.async_send_request(
            command, request, NetworkInfo_pb2.NetworkInfoReqDTO
        )

    async def async_app_information_data(
        self,
    ) -> APPInfomationData_pb2.APPInfoDataResDTO:
        """Get app information data."""
        request = APPInfomationData_pb2.APPInfoDataResDTO()
        request.time_ymd_hms = (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S").encode("utf-8")
        )
        request.offset = OFFSET
        request.time = int(time.time())
        command = CMD_APP_INFO_DATA_RES_DTO
        return await self.async_send_request(
            command, request, APPInfomationData_pb2.APPInfoDataReqDTO
        )

    async def async_app_get_hist_power(
        self,
    ) -> AppGetHistPower_pb2.AppGetHistPowerResDTO | None:
        """Get historical power."""

        request = AppGetHistPower_pb2.AppGetHistPowerResDTO()
        request.control_point = 0
        request.offset = OFFSET
        request.requested_time = int(time.time())
        request.requested_day = 0
        command = CMD_APP_GET_HIST_POWER_RES
        return await self.async_send_request(
            command,
            request,
            AppGetHistPower_pb2.AppGetHistPowerReqDTO,
        )

    async def async_set_power_limit(
        self,
        power_limit: int,
    ) -> CommandPB_pb2.CommandResDTO | None:
        """Set power limit."""
        if power_limit < 0 or power_limit > 100:
            logger.error("Error. Invalid power limit!")
            return

        power_limit = power_limit * 10

        request = CommandPB_pb2.CommandResDTO()
        request.time = int(time.time())
        request.action = CMD_ACTION_LIMIT_POWER
        request.package_nub = 1
        request.tid = int(time.time())
        request.data = f"A:{power_limit},B:0,C:0\r".encode()

        command = CMD_COMMAND_RES_DTO

        return await self.async_send_request(
            command, request, CommandPB_pb2.CommandReqDTO
        )

    async def async_set_wifi(
        self, ssid: str, password: str
    ) -> SetConfig_pb2.SetConfigResDTO | None:
        """Set wifi."""

        get_config_req = await self.async_get_config()

        if get_config_req is None:
            logger.error("Failed to get config")
            return None

        request = initialize_set_config(get_config_req)

        request.time = int(time.time())
        request.offset = OFFSET
        request.app_page = 1
        request.netmode_select = NetmodeSelect.WIFI
        request.wifi_ssid = ssid.encode("utf-8")
        request.wifi_password = password.encode("utf-8")

        command = CMD_SET_CONFIG
        return await self.async_send_request(
            command, request, SetConfig_pb2.SetConfigReqDTO
        )

    async def async_update_dtu_firmware(
        self,
        firmware_url: str = DTU_FIRMWARE_URL_00_01_11,
    ) -> CommandPB_pb2.CommandResDTO | None:
        """Update DTU firmware."""

        request = CommandPB_pb2.CommandResDTO()
        request.action = CMD_ACTION_DTU_UPGRADE
        request.package_nub = 1
        request.tid = int(time.time())
        request.data = (firmware_url + "\r").encode("utf-8")

        command = CMD_CLOUD_COMMAND_RES_DTO
        return await self.async_send_request(
            command, request, CommandPB_pb2.CommandReqDTO
        )

    async def async_restart_dtu(self) -> CommandPB_pb2.CommandResDTO | None:
        """Restart DTU."""

        request = CommandPB_pb2.CommandResDTO()
        request.action = CMD_ACTION_DTU_REBOOT
        request.package_nub = 1
        request.tid = int(time.time())

        command = CMD_CLOUD_COMMAND_RES_DTO
        return await self.async_send_request(
            command, request, CommandPB_pb2.CommandReqDTO
        )

    async def async_turn_on_inverter(
        self, inverter_serial: str
    ) -> CommandPB_pb2.CommandResDTO | None:
        """Turn on Inverter."""

        inverter_serial_int = convert_inverter_serial_number(inverter_serial)

        request = CommandPB_pb2.CommandResDTO()
        request.action = CMD_ACTION_MI_START
        request.package_nub = 1
        request.dev_kind = DEV_DTU
        request.tid = int(time.time())
        request.mi_to_sn.extend([inverter_serial_int])

        command = CMD_CLOUD_COMMAND_RES_DTO

        return await self.async_send_request(
            command, request, CommandPB_pb2.CommandReqDTO
        )

    async def async_turn_off_inverter(
        self, inverter_serial: str
    ) -> CommandPB_pb2.CommandResDTO | None:
        """Turn off Inverter."""

        inverter_serial_int = convert_inverter_serial_number(inverter_serial)

        request = CommandPB_pb2.CommandResDTO()
        request.action = CMD_ACTION_MI_SHUTDOWN
        request.package_nub = 1
        request.dev_kind = DEV_DTU
        request.tid = int(time.time())
        request.mi_to_sn.extend([inverter_serial_int])

        command = CMD_CLOUD_COMMAND_RES_DTO

        return await self.async_send_request(
            command, request, CommandPB_pb2.CommandReqDTO
        )

    async def async_get_information_data(
        self,
    ) -> InfomationData_pb2.InfoDataResDTO | None:
        """Get information data."""

        request = InfomationData_pb2.InfoDataResDTO()
        request.time_ymd_hms = (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S").encode("utf-8")
        )
        request.offset = OFFSET
        request.time = int(time.time())
        command = CMD_APP_INFO_DATA_RES_DTO
        return await self.async_send_request(
            command, request, InfomationData_pb2.InfoDataReqDTO
        )

    async def async_heartbeat(self) -> APPHeartbeatPB_pb2.HBReqDTO | None:
        """Request heartbeat."""

        request = APPHeartbeatPB_pb2.HBResDTO()
        request.time_ymd_hms = (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S").encode("utf-8")
        )
        request.offset = OFFSET
        request.time = int(time.time())

        command = CMD_HB_RES_DTO
        return await self.async_send_request(
            command, request, APPHeartbeatPB_pb2.HBReqDTO
        )

    async def async_get_alarm_list(self) -> CommandPB_pb2.CommandResDTO | None:
        """Turn off DTU."""

        request = CommandPB_pb2.CommandResDTO()
        request.action = CMD_ACTION_ALARM_LIST
        request.package_nub = 1
        request.dev_kind = 0
        request.tid = int(time.time())

        command = CMD_COMMAND_RES_DTO
        return await self.async_send_request(
            command, request, CommandPB_pb2.CommandReqDTO
        )

    async def async_send_request(
        self,
        command: bytes,
        request: Any,
        response_type: Any,
        dtu_port: int = DTU_PORT,
    ):
        """Send request to DTU."""

        self.sequence = (self.sequence + 1) & 0xFFFF

        request_as_bytes = request.SerializeToString()
        crc16 = mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)(
            request_as_bytes
        )
        length = len(request_as_bytes) + 10

        # compose request message
        header = CMD_HEADER + command
        message = (
            header
            + struct.pack(">HHH", self.sequence, crc16, length)
            + request_as_bytes
        )

        ip_to_bind = (self.local_addr, 0) if self.local_addr is not None else None

        async with self.mutex:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(
                        host=self.host,
                        port=dtu_port,
                        local_addr=ip_to_bind,
                    ),
                    timeout=5,
                )

                writer.write(message)
                await writer.drain()

                buf = await asyncio.wait_for(reader.read(1024), timeout=5)
            except (OSError, asyncio.TimeoutError) as e:
                logger.debug(f"{e}")
                self.set_state(NetworkState.Offline)
                return None
            finally:
                try:
                    if writer:
                        writer.close()
                        await writer.wait_closed()
                except Exception as e:
                    logger.debug(f"Error closing writer: {e}")

        try:
            if len(buf) < 10:
                raise ValueError("Buffer is too short for unpacking")

            crc16_target, read_length = struct.unpack(">HH", buf[6:10])

            logger.debug(f"Read length: {read_length}")

            if len(buf) != read_length:
                raise ValueError("Buffer is incomplete")

            response_as_bytes = buf[10:read_length]

            crc16_response = mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)(
                response_as_bytes
            )

            if crc16_response != crc16_target:
                logger.debug(
                    f"CRC16 mismatch: {hex(crc16_response)} != {hex(crc16_target)}"
                )
                raise ValueError("CRC16 mismatch")

            parsed = response_type.FromString(response_as_bytes)

            if not parsed:
                raise ValueError("Parsing resulted in an empty or falsy value")
        except Exception as e:
            logger.debug(f"Failed to parse response: {e}")
            self.set_state(NetworkState.Unknown)
            return None

        self.set_state(NetworkState.Online)
        return parsed
