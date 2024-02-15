from __future__ import annotations
import asyncio
import struct
from typing import Any
from crcmod import mkCrcFun
from datetime import datetime
import time

from hoymiles_wifi import logger

from hoymiles_wifi.utils import initialize_set_config

from hoymiles_wifi.protobuf import (
    APPHeartbeatPB_pb2,
    APPInfomationData_pb2,
    AppGetHistPower_pb2,
    CommandPB_pb2,
    InfomationData_pb2,
    GetConfig_pb2,
    RealData_pb2,
    RealDataNew_pb2,
    RealDataHMS_pb2,
    NetworkInfo_pb2,
    SetConfig_pb2,
 )


from hoymiles_wifi.const import (
    INVERTER_PORT, 
    CMD_HEADER,
    CMD_GET_CONFIG,
    CMD_REAL_RES_DTO,
    CMD_REAL_DATA_RES_DTO,
    CMD_NETWORK_INFO_RES,
    CMD_APP_INFO_DATA_RES_DTO,
    CMD_APP_GET_HIST_POWER_RES,
    CMD_ACTION_POWER_LIMIT,
    CMD_COMMAND_RES_DTO,
    CMD_ACTION_FIRMWARE_UPGRADE,
    CMD_SET_CONFIG,
    CMD_CLOUD_COMMAND_RES_DTO,
    CMD_ACTION_RESTART,
    CMD_ACTION_TURN_ON,
    CMD_ACTION_TURN_OFF,
    DTU_FIRMWARE_URL_00_01_11,
    CMD_HB_RES_DTO,
)


class NetmodeSelect:
    WIFI = 1
    SIM = 2
    LAN = 3

class NetworkState:
    Unknown = 0
    Online = 1
    Offline = 2

class Inverter:
    def __init__(self, host: str):
        self.host = host
        self.state = NetworkState.Unknown
        self.sequence = 0

    def get_state(self) -> NetworkState:
        return self.state

    def set_state(self, new_state: NetworkState):
        if self.state != new_state:
            self.state = new_state
            logger.debug(f"Inverter is {new_state}")
        
    async def async_get_real_data_hms(self) -> RealDataHMS_pb2.HMSStateResponse | None:
        request = RealDataHMS_pb2.HMSRealDataResDTO()
        command = CMD_REAL_DATA_RES_DTO
        return await self.async_send_request(command, request, RealDataHMS_pb2.HMSStateResponse)
    
    async def async_get_real_data(self) -> RealData_pb2.RealDataResDTO | None:
        request = RealData_pb2.RealDataResDTO()
        command = CMD_REAL_DATA_RES_DTO
        return await self.async_send_request(command, request, RealData_pb2.RealDataReqDTO)

    async def async_get_real_data_new(self) -> RealDataNew_pb2.RealDataNewResDTO | None:
        request = RealDataNew_pb2.RealDataNewResDTO()
        request.time_ymd_hms = datetime.now().strftime("%Y-%m-%d %H:%M:%S").encode("utf-8")
        request.offset = 28800
        request.time = int(time.time())
        command = CMD_REAL_RES_DTO
        return await self.async_send_request(command, request, RealDataNew_pb2.RealDataNewReqDTO)
    
    async def async_get_config(self) -> GetConfig_pb2.GetConfigResDTO | None:
        request = GetConfig_pb2.GetConfigResDTO()
        request.offset = 28800
        request.time = int(time.time()) - 60
        command = CMD_GET_CONFIG
        return await self.async_send_request(command, request, GetConfig_pb2.GetConfigReqDTO)    

    async def async_network_info(self) -> NetworkInfo_pb2.NetworkInfoResDTO | None:
        request = NetworkInfo_pb2.NetworkInfoResDTO()
        request.offset = 28800
        request.time = int(time.time())
        command = CMD_NETWORK_INFO_RES
        return await self.async_send_request(command, request, NetworkInfo_pb2.NetworkInfoReqDTO)
    
    async def async_app_information_data(self) -> APPInfomationData_pb2.APPInfoDataResDTO:
        request = APPInfomationData_pb2.APPInfoDataResDTO()
        request.time_ymd_hms = datetime.now().strftime("%Y-%m-%d %H:%M:%S").encode("utf-8")
        request.offset = 28800
        request.time = int(time.time())
        command = CMD_APP_INFO_DATA_RES_DTO
        return await self.async_send_request(command, request, APPInfomationData_pb2.APPInfoDataReqDTO)
    
    async def async_app_get_hist_power(self) -> AppGetHistPower_pb2.AppGetHistPowerResDTO | None:
        request = AppGetHistPower_pb2.AppGetHistPowerResDTO()
        request.offset = 28800
        request.requested_time = int(time.time())
        command = CMD_APP_GET_HIST_POWER_RES
        return await self.async_send_request(command, request, AppGetHistPower_pb2.AppGetHistPowerReqDTO)
    
    async def async_set_power_limit(self, power_limit: int) -> CommandPB_pb2.CommandResDTO | None:

        if(power_limit < 0 or power_limit > 100):
            logger.error("Error. Invalid power limit!")
            return

        power_limit = power_limit * 10

        request = CommandPB_pb2.CommandResDTO()
        request.time = int(time.time())
        request.action = CMD_ACTION_POWER_LIMIT
        request.package_nub = 1
        request.tid = int(time.time())
        request.data = f'A:{power_limit},B:0,C:0\r'.encode('utf-8')

        command = CMD_COMMAND_RES_DTO

        return await self.async_send_request(command, request, CommandPB_pb2.CommandReqDTO)
    
    async def async_set_wifi(self, ssid: str, password: str) -> SetConfig_pb2.SetConfigResDTO | None:

        get_config_req = await self.async_get_config()

        if(get_config_req is None):
            logger.error("Failed to get config")
            return
    
        request = initialize_set_config(get_config_req)
    
        request.time = int(time.time()) 
        request.offset = 28800
        request.app_page = 1
        request.netmode_select = NetmodeSelect.WIFI
        request.wifi_ssid = ssid.encode('utf-8')
        request.wifi_password = password.encode('utf-8')

        command = CMD_SET_CONFIG
        return await self.async_send_request(command, request, SetConfig_pb2.SetConfigReqDTO)


    async def async_update_dtu_firmware(self, firmware_url: str = DTU_FIRMWARE_URL_00_01_11) -> CommandPB_pb2.CommandResDTO | None:

        request = CommandPB_pb2.CommandResDTO()
        request.action = CMD_ACTION_FIRMWARE_UPGRADE
        request.package_nub = 1
        request.tid = int(time.time())
        request.data = (firmware_url + '\r').encode('utf-8')

        command = CMD_CLOUD_COMMAND_RES_DTO
        return await self.async_send_request(command, request, CommandPB_pb2.CommandReqDTO)
    

    async def async_restart(self) -> CommandPB_pb2.CommandResDTO | None:

        request = CommandPB_pb2.CommandResDTO()
        request.action = CMD_ACTION_RESTART
        request.package_nub = 1
        request.tid = int(time.time())

        command = CMD_CLOUD_COMMAND_RES_DTO
        return await self.async_send_request(command, request, CommandPB_pb2.CommandReqDTO)


    async def async_turn_on(self) -> CommandPB_pb2.CommandResDTO | None:

        request = CommandPB_pb2.CommandResDTO()
        request.action = CMD_ACTION_TURN_ON
        request.package_nub = 1
        request.dev_kind = 1
        request.tid = int(time.time())

        command = CMD_CLOUD_COMMAND_RES_DTO
        return await self.async_send_request(command, request, CommandPB_pb2.CommandReqDTO)
    
    async def async_turn_off(self) -> CommandPB_pb2.CommandResDTO | None:

        request = CommandPB_pb2.CommandResDTO()
        request.action = CMD_ACTION_TURN_OFF
        request.package_nub = 1
        request.dev_kind = 1
        request.tid = int(time.time())

        command = CMD_CLOUD_COMMAND_RES_DTO
        return await self.async_send_request(command, request, CommandPB_pb2.CommandReqDTO)
    
    async def async_get_information_data(self) -> InfomationData_pb2.InfoDataResDTO | None:

        request = InfomationData_pb2.InfoDataResDTO()
        request.time_ymd_hms = datetime.now().strftime("%Y-%m-%d %H:%M:%S").encode("utf-8")
        request.offset = 28800
        request.time = int(time.time())
        command = CMD_APP_INFO_DATA_RES_DTO
        return await self.async_send_request(command, request, InfomationData_pb2.InfoDataReqDTO)
    

    async def async_heartbeat(self) -> APPHeartbeatPB_pb2.HBReqDTO | None:

        request = APPHeartbeatPB_pb2.HBResDTO()
        request.time_ymd_hms = datetime.now().strftime("%Y-%m-%d %H:%M:%S").encode("utf-8")
        request.offset = 28800
        request.time = int(time.time())

        command = CMD_HB_RES_DTO
        return await self.async_send_request(command, request, APPHeartbeatPB_pb2.HBReqDTO)
    

    async def async_send_request(self, command: bytes, request: Any, response_type: Any, inverter_port: int = INVERTER_PORT):
        self.sequence = (self.sequence + 1) & 0xFFFF

        request_as_bytes = request.SerializeToString()
        crc16 = mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)(request_as_bytes)
        length = len(request_as_bytes) + 10

        # compose request message
        header = CMD_HEADER + command
        message = header + struct.pack('>HHH', self.sequence, crc16, length) + request_as_bytes

        address = (self.host, inverter_port)

        try:
            reader, writer = await asyncio.open_connection(*address)
            
            writer.write(message)
            await writer.drain()
            
            buf = await asyncio.wait_for(reader.read(1024), timeout=5)
        except (OSError, asyncio.TimeoutError) as e:
            logger.debug(f"{e}")
            self.set_state(NetworkState.Offline)
            return None

        try:
            if len(buf) < 8:
                raise ValueError("Buffer is too short for unpacking")
        
            read_length = struct.unpack('>H', buf[6:8])[0]

            parsed = response_type.FromString(buf[10:10 + read_length])

            if not parsed:
                raise ValueError("Parsing resulted in an empty or falsy value")
        except Exception as e:
            logger.debug(f"Failed to parse response: {e}")
            self.set_state(NetworkState.Unknown)
            return None
        finally:
            writer.close()
            await writer.wait_closed()

        self.set_state(NetworkState.Online)
        return parsed



