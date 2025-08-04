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
    CMD_ACTION_INV_REBOOT,
    CMD_ACTION_LIMIT_POWER,
    CMD_ACTION_MI_SHUTDOWN,
    CMD_ACTION_MI_START,
    CMD_ACTION_PERFORMANCE_DATA_MODE,
    CMD_APP_GET_HIST_POWER_RES,
    CMD_APP_INFO_DATA_RES_DTO,
    CMD_CLOUD_COMMAND_RES_DTO,
    CMD_COMMAND_RES_DTO,
    CMD_ES_DATA_DTO,
    CMD_ES_REG_RES_DTO,
    CMD_ES_USER_SET_RES_DTO,
    CMD_GET_CONFIG,
    CMD_GW_INFO_RES_DTO,
    CMD_GW_NET_INFO_RES,
    CMD_HB_RES_DTO,
    CMD_HEADER,
    CMD_NETWORK_INFO_RES,
    CMD_REAL_DATA_RES_DTO,
    CMD_REAL_RES_DTO,
    CMD_SET_CONFIG,
    DEV_DTU,
    DTU_FIRMWARE_URL_00_01_11,
    DTU_PORT,
    NOT_ENCRYPTED_COMMANDS,
    OFFSET,
)
from hoymiles_wifi.crypt_util import crypt_data
from hoymiles_wifi.hoymiles import (
    BMSWorkingMode,
    DateBean,
    TariffType,
    TimePeriodBean,
    convert_inverter_serial_number,
    encode_date_time_range,
    encode_week_range,
    float_to_scaled_int,
)
from hoymiles_wifi.protobuf import (
    AppGetHistPower_pb2,
    APPHeartbeatPB_pb2,
    APPInfomationData_pb2,
    CommandPB_pb2,
    ESData_pb2,
    ESRegPB_pb2,
    ESUserSet_pb2,
    GetConfig_pb2,
    GWInfo_pb2,
    GWNetInfo_pb2,
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

    def __init__(
        self,
        host: str,
        local_addr: str = None,
        is_encrypted: bool = False,
        enc_rand: bytes = b"",
    ):
        """Initialize DTU class."""

        self.host: str = host
        self.local_addr: str = local_addr
        self.state: NetworkState = NetworkState.Unknown
        self.sequence: int = 0
        self.mutex: asyncio.Lock = asyncio.Lock()
        self.last_request_time: int = 0
        self.is_encrypted: bool = is_encrypted
        self.enc_rand: bytes = enc_rand

    def get_state(self) -> NetworkState:
        """Get DTU state."""

        return self.state

    def set_state(self, new_state: NetworkState):
        """Set DTU state."""

        if self.state != new_state:
            self.state = new_state
            logger.debug(f"DTU is {new_state}")

    async def async_get_real_data(self) -> RealData_pb2.RealDataReqDTO | None:
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

    async def async_get_real_data_new(self) -> RealDataNew_pb2.RealDataNewReqDTO | None:
        """Get real data new."""

        combined_response = RealDataNew_pb2.RealDataNewReqDTO()

        request = RealDataNew_pb2.RealDataNewResDTO()
        request.time_ymd_hms = (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S").encode("utf-8")
        )
        request.offset = OFFSET
        request.time = int(time.time())
        request.cp = 0
        command = CMD_REAL_RES_DTO

        # Await the initial response
        response = await self.async_send_request(
            command, request, RealDataNew_pb2.RealDataNewReqDTO
        )

        # Combine the initial response into the combined_response
        if response is not None:
            combined_response.MergeFrom(response)

            # Fetch additional data based on the value of response.ap
            for cp in range(1, response.ap):
                request.cp = cp

                additional_response = await self.async_send_request(
                    command, request, RealDataNew_pb2.RealDataNewReqDTO
                )
                if additional_response is not None:
                    combined_response.MergeFrom(additional_response)

        return combined_response if combined_response.ByteSize() > 0 else None

    async def async_get_config(self) -> GetConfig_pb2.GetConfigReqDTO | None:
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

    async def async_network_info(self) -> NetworkInfo_pb2.NetworkInfoReqDTO | None:
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
    ) -> APPInfomationData_pb2.APPInfoDataReqDTO:
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
    ) -> AppGetHistPower_pb2.AppGetHistPowerReqDTO | None:
        """Get historical power."""

        combined_response = AppGetHistPower_pb2.AppGetHistPowerReqDTO()

        request = AppGetHistPower_pb2.AppGetHistPowerResDTO()
        request.cp = 0
        request.offset = OFFSET
        request.requested_time = int(time.time())
        request.requested_day = 0
        command = CMD_APP_GET_HIST_POWER_RES

        response = await self.async_send_request(
            command,
            request,
            AppGetHistPower_pb2.AppGetHistPowerReqDTO,
        )

        if response is not None:
            combined_response.MergeFrom(response)

            # Fetch additional data based on the value of response.ap
            for cp in range(1, response.ap):
                request.cp = cp

                additional_response = await self.async_send_request(
                    command,
                    request,
                    AppGetHistPower_pb2.AppGetHistPowerReqDTO,
                )
                if additional_response is not None:
                    combined_response.MergeFrom(additional_response)

        return combined_response if combined_response.ByteSize() > 0 else None

    async def async_set_power_limit(
        self,
        power_limit: int,
    ) -> CommandPB_pb2.CommandReqDTO | None:
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
    ) -> SetConfig_pb2.SetConfigReqDTO | None:
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
    ) -> CommandPB_pb2.CommandReqDTO | None:
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

    async def async_restart_dtu(self) -> CommandPB_pb2.CommandReqDTO | None:
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
    ) -> CommandPB_pb2.CommandReqDTO | None:
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
    ) -> CommandPB_pb2.CommandReqDTO | None:
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

    async def async_reboot_inverter(
        self, inverter_serial: str
    ) -> CommandPB_pb2.CommandResDTO | None:
        """Reboot Inverter."""

        inverter_serial_int = convert_inverter_serial_number(inverter_serial)

        request = CommandPB_pb2.CommandResDTO()
        request.action = CMD_ACTION_INV_REBOOT
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

    async def async_enable_performance_data_mode(
        self,
    ) -> CommandPB_pb2.CommandReqDTO | None:
        """Enable performance data mode."""

        request = CommandPB_pb2.CommandResDTO()
        request.time = int(time.time())
        request.action = CMD_ACTION_PERFORMANCE_DATA_MODE
        request.package_nub = 1

        command = CMD_COMMAND_RES_DTO
        return await self.async_send_request(
            command, request, CommandPB_pb2.CommandReqDTO
        )

    async def async_get_gateway_info(self) -> GWInfo_pb2.GWInfoReqDTO | None:
        """Get gateway info."""

        request = GWInfo_pb2.GWInfoResDTO()
        request.time = int(time.time())
        request.offset = OFFSET

        command = CMD_GW_INFO_RES_DTO

        return await self.async_send_request(
            command,
            request,
            GWInfo_pb2.GWInfoReqDTO,
            is_extended_format=True,
            number=255,
        )

    async def async_get_gateway_network_info(
        self, dtu_serial_number: int
    ) -> GWNetInfo_pb2.GWNetInfoReq | None:
        """Get gateway network info."""

        request = GWNetInfo_pb2.GWNetInfoRes()
        request.time = int(time.time())
        request.offset = OFFSET

        command = CMD_GW_NET_INFO_RES

        return await self.async_send_request(
            command,
            request,
            GWNetInfo_pb2.GWNetInfoReq,
            is_extended_format=True,
            dtu_serial_number=dtu_serial_number,
            number=255,
        )

    async def async_get_energy_storage_registry(
        self, dtu_serial_number: int
    ) -> ESRegPB_pb2.ESRegReqDTO | None:
        """Get energy storage registry."""

        request = ESRegPB_pb2.ESRegResDTO()
        request.time = int(time.time())
        request.time_ymd_hms = (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S").encode("utf-8")
        )
        request.offset = OFFSET
        request.cp = 0

        command = CMD_ES_REG_RES_DTO

        return await self.async_send_request(
            command,
            request,
            ESRegPB_pb2.ESRegReqDTO,
            is_extended_format=True,
            dtu_serial_number=dtu_serial_number,
            number=1,
        )

    async def async_get_energy_storage_data(
        self, dtu_serial_number: int, inverter_serial_number: int
    ) -> ESData_pb2.ESDataReqDTO | None:
        """Get energy storage registry."""

        request = ESData_pb2.ESDataResDTO()
        request.time = int(time.time())
        request.time_ymd_hms = (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S").encode("utf-8")
        )
        request.offset = OFFSET
        request.cp = 0
        request.serial_number = inverter_serial_number

        command = CMD_ES_DATA_DTO

        return await self.async_send_request(
            command,
            request,
            ESData_pb2.ESDataReqDTO,
            is_extended_format=True,
            dtu_serial_number=dtu_serial_number,
            number=1,
        )

    async def async_set_energy_storage_working_mode(
        self,
        dtu_serial_number: int,
        inverter_serial_number: int,
        bms_working_mode: BMSWorkingMode,
        rev_soc: int = None,
        time_settings: list[DateBean] = None,
        max_power: int = None,
        peak_soc: int = None,
        peak_meter_power: int = None,
        time_periods: list[TimePeriodBean] = None,
    ) -> ESUserSet_pb2.ESUserSetPutReqDTO | None:
        """Set energy storage working mode."""

        request = ESUserSet_pb2.ESUserSetPutResDTO()
        request.time = int(time.time())
        request.tid = int(time.time())
        request.serial_number.extend([inverter_serial_number])
        request.mode = bms_working_mode.value

        if rev_soc is not None:
            request.rev_soc = rev_soc

        if max_power is not None:
            if max_power < 0 or max_power > 100:
                logger.error("Error. Max power! (" + str(max_power) + ")")
                return
            request.max_power = max_power * 10

        if bms_working_mode == BMSWorkingMode.ECONOMIC:
            for time_setting in time_settings:
                set_date = ESUserSet_pb2.EconomicsSetDateMO()
                set_date.dr = encode_date_time_range(
                    time_setting.start_date, time_setting.end_date, "."
                )

                if time_setting.time is None or len(time_setting.time) != 2:
                    logger.error(
                        "Error. No time settings or too many time settings provided!"
                    )
                    return

                for idx, time_range in enumerate(time_setting.time):
                    set_week = ESUserSet_pb2.EconomicsSetWeekMO()
                    set_week.wr = encode_week_range(time_range.week)

                    for duration in time_range.durations:
                        if duration.type == TariffType.PEAK:
                            set_week.peak_in = float_to_scaled_int(duration.in_price)
                            set_week.peak_out = float_to_scaled_int(duration.out_price)
                            set_week.peak_time = encode_date_time_range(
                                duration.start_time, duration.end_time, ":"
                            )
                        elif duration.type == TariffType.OFF_PEAK:
                            set_week.valley_in = float_to_scaled_int(duration.in_price)
                            set_week.valley_out = float_to_scaled_int(
                                duration.out_price
                            )
                            set_week.valley_time = encode_date_time_range(
                                duration.start_time, duration.end_time, ":"
                            )
                        elif duration.type == TariffType.PARTIAL_PEAK:
                            set_week.partial_peak_in = float_to_scaled_int(
                                duration.in_price
                            )
                            set_week.partial_peak_out = float_to_scaled_int(
                                duration.out_price
                            )

                        if idx == 0:
                            set_date.w1.CopyFrom(set_week)
                        elif idx == 1:
                            set_date.w2.CopyFrom(set_week)

                request.date.extend([set_date])

        elif bms_working_mode == BMSWorkingMode.PEAK_SHAVING:
            if peak_soc is None or peak_meter_power is None:
                logger.error("Error. Peak SOC or peak meter power!")
                return
            request.peak_soc = peak_soc
            request.peak_meterpwr = peak_meter_power
        elif bms_working_mode == BMSWorkingMode.TIME_OF_USE:
            for time_period in time_periods:
                if (
                    time_period.charge_time_from is None
                    or time_period.charge_time_to is None
                    or time_period.discharge_time_from is None
                    or time_period.discharge_time_to is None
                    or time_period.charge_power is None
                    or time_period.discharge_power is None
                    or time_period.max_soc is None
                    or time_period.min_soc is None
                ):
                    logger.error("Error. Check parameters for Time of Use!")
                    return

                if (
                    time_period.charge_power < 0
                    or time_period.charge_power > 100
                    or time_period.discharge_power < 0
                    or time_period.discharge_power > 100
                    or time_period.max_soc < 0
                    or time_period.max_soc > 100
                    or time_period.min_soc < 0
                    or time_period.min_soc > 100
                ):
                    logger.error("Error. Check power values for Time of Use!")
                    return

                time_of_use = ESUserSet_pb2.TimeOfUseSetMO()
                time_of_use.chrg_tr = encode_date_time_range(
                    time_period.charge_time_from, time_period.charge_time_to, ":"
                )
                time_of_use.dischrg_tr = encode_date_time_range(
                    time_period.discharge_time_from, time_period.discharge_time_to, ":"
                )
                time_of_use.chrg_pwr = time_period.charge_power
                time_of_use.dischrg_pwr = time_period.discharge_power
                time_of_use.max_soc = time_period.max_soc
                time_of_use.min_soc = time_period.min_soc

                request.tou.extend([time_of_use])

        command = CMD_ES_USER_SET_RES_DTO

        logger.debug("Set energy storage working mode: " + str(request))

        return await self.async_send_request(
            command,
            request,
            ESUserSet_pb2.ESUserSetPutReqDTO,
            is_extended_format=True,
            dtu_serial_number=dtu_serial_number,
            number=1,
        )

    async def async_send_request(
        self,
        command: bytes,
        request: Any,
        response_type: Any,
        dtu_port: int = DTU_PORT,
        is_extended_format: bool = False,
        dtu_serial_number: int = 0,
        number: int = 0,
    ):
        """Send request to DTU."""

        message = self.generate_message(
            command, request, is_extended_format, dtu_serial_number, number
        )

        ip_to_bind = (self.local_addr, 0) if self.local_addr is not None else None

        async with self.mutex:
            current_time = time.time()
            elapsed_time = current_time - self.last_request_time

            if elapsed_time < 2:
                logger.debug(
                    f"Last request was sent less than 2s ago. Waiting for {2 - elapsed_time}s"
                )
                await asyncio.sleep(2 - elapsed_time)

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

                buffer = await asyncio.wait_for(reader.read(1024), timeout=5)
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

        self.last_request_time = time.time()

        return self.parse_response(buffer, response_type, is_extended_format)

    def generate_message(
        self,
        command: bytes,
        request: Any,
        is_extended_format: bool,
        serial_number: int,
        number: int,
    ) -> bytes:
        """Generate message to send to DTU."""

        self.sequence = (self.sequence + 1) & 0xFFFF

        u16_tag = struct.unpack(">H", command)[0]

        if (
            self.is_encrypted
            and not is_extended_format
            and command not in NOT_ENCRYPTED_COMMANDS
        ):
            request_as_bytes = crypt_data(
                encrypt=True,
                enc_rand=self.enc_rand,
                u16_tag=u16_tag,
                u16_seq=self.sequence,
                input_data=request.SerializeToString(),
            )
            crc16 = mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)(
                request_as_bytes[:-16]
            )

        else:
            request_as_bytes = request.SerializeToString()
            crc16 = mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)(
                request_as_bytes
            )

        header = CMD_HEADER + command
        metadata = struct.pack(">HH", self.sequence, crc16)

        if is_extended_format:
            metadata += struct.pack(
                ">HHQHH", 24 + len(request_as_bytes), 14, serial_number, 0, number
            )
        elif self.is_encrypted and command not in NOT_ENCRYPTED_COMMANDS:
            metadata += struct.pack(">H", len(request_as_bytes) - 16 + 10)
        else:
            metadata += struct.pack(">H", len(request_as_bytes) + 10)

        message = header + metadata + request_as_bytes

        logger.debug(f"[*] Request header: {header.hex()}")
        logger.debug(f"[*] Request metadata: {metadata.hex()}")
        logger.debug(f"[*] Request: {request_as_bytes.hex()}")
        logger.debug(f"[*] Request message: {message.hex()}")

        return message

    def parse_response(self, buffer, response_type: Any, is_extended_format: bool):
        """Parse response from DTU."""

        try:
            if len(buffer) < 10:
                raise ValueError("Buffer is too short for unpacking")

            tag_num = buffer[2:4]
            u16_tag, u16_seq = struct.unpack(">HH", buffer[2:6])

            crc16_target, read_length = struct.unpack(">HH", buffer[6:10])

            logger.debug(f"Read length: {read_length}")

            expected_length = (
                read_length + 16
                if self.is_encrypted
                and tag_num not in NOT_ENCRYPTED_COMMANDS
                and not is_extended_format
                else read_length
            )

            if len(buffer) != expected_length:
                raise ValueError(
                    f"Buffer is incomplete (expected {expected_length}, got {len(buffer)})"
                )

            if is_extended_format:
                crc16_response = mkCrcFun(
                    0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000
                )(buffer[24:read_length])
            else:
                crc16_response = mkCrcFun(
                    0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000
                )(buffer[10:read_length])

            if crc16_response != crc16_target:
                logger.error(
                    f"CRC16 mismatch: {hex(crc16_response)} != {hex(crc16_target)}"
                )
                raise ValueError("CRC16 mismatch")

            if is_extended_format:
                logger.debug("Detected extended format!")
                response_as_bytes = buffer[24:read_length]
            elif self.is_encrypted and tag_num not in NOT_ENCRYPTED_COMMANDS:
                logger.debug("Detected encrypted format!")
                ciphertext = buffer[10:expected_length]
                response_as_bytes = crypt_data(
                    False, self.enc_rand, u16_tag, u16_seq, ciphertext
                )
            else:
                logger.debug("Detected unencrypted format!")
                response_as_bytes = buffer[10:read_length]

            logger.debug(f"Response: {response_as_bytes.hex()}")

            parsed = response_type.FromString(response_as_bytes)

            if not parsed:
                raise ValueError("Parsing resulted in an empty or falsy value")
        except Exception as e:
            logger.debug(f"Failed to parse response: {e}")
            self.set_state(NetworkState.Unknown)
            return None

        self.set_state(NetworkState.Online)
        return parsed
