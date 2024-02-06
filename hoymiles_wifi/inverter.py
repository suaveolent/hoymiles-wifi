import socket
import struct
from typing import Any
from crcmod import mkCrcFun
from datetime import datetime
import time
import warnings

from hoymiles_wifi import logger

from hoymiles_wifi.utils import initialize_set_config

from hoymiles_wifi.protobuf import (
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

    def get_state(self):
        return self.state

    def set_state(self, new_state: NetworkState):
        if self.state != new_state:
            self.state = new_state
            logger.debug(f"Inverter is {new_state}")

    def update_state(self):
        warnings.warn("This function is deprecated and will be removed in the future.", FutureWarning)
        return self.get_real_data_hms()
        
    def get_real_data_hms(self):
        request = RealDataHMS_pb2.HMSRealDataResDTO()
        command = CMD_REAL_DATA_RES_DTO
        return self.send_request(command, request, RealDataHMS_pb2.HMSStateResponse)
    
    def get_real_data(self):
        request = RealData_pb2.RealDataResDTO()
        command = CMD_REAL_DATA_RES_DTO
        return self.send_request(command, request, RealData_pb2.RealDataReqDTO)

    def get_real_data_new(self):
        request = RealDataNew_pb2.RealDataNewResDTO()
        request.time_ymd_hms = datetime.now().strftime("%Y-%m-%d %H:%M:%S").encode("utf-8")
        request.offset = 28800
        request.time = int(time.time())
        command = CMD_REAL_RES_DTO
        return self.send_request(command, request, RealDataNew_pb2.RealDataNewReqDTO)
    
    def get_config(self):
        request = GetConfig_pb2.GetConfigResDTO()
        request.offset = 28800
        request.time = int(time.time()) - 60
        command = CMD_GET_CONFIG
        return self.send_request(command, request, GetConfig_pb2.GetConfigReqDTO)    

    def network_info(self):
        request = NetworkInfo_pb2.NetworkInfoResDTO()
        request.offset = 28800
        request.time = int(time.time())
        command = CMD_NETWORK_INFO_RES
        return self.send_request(command, request, NetworkInfo_pb2.NetworkInfoReqDTO)
    
    def app_information_data(self):
        request = APPInfomationData_pb2.APPInfoDataResDTO()
        request.time_ymd_hms = datetime.now().strftime("%Y-%m-%d %H:%M:%S").encode("utf-8")
        request.offset = 28800
        request.time = int(time.time())
        command = CMD_APP_INFO_DATA_RES_DTO
        return self.send_request(command, request, APPInfomationData_pb2.APPInfoDataReqDTO)
    
    def app_get_hist_power(self):
        request = AppGetHistPower_pb2.AppGetHistPowerResDTO()
        request.offset = 28800
        request.requested_time = int(time.time())
        command = CMD_APP_GET_HIST_POWER_RES
        return self.send_request(command, request, AppGetHistPower_pb2.AppGetHistPowerReqDTO)
    
    def set_power_limit(self, power_limit: int):

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

        return self.send_request(command, request, CommandPB_pb2.CommandReqDTO)
    
    def set_wifi(self, ssid, password):

        get_config_req = self.get_config()

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
        return self.send_request(command, request, SetConfig_pb2.SetConfigReqDTO)


    def firmware_update(self):

        request = CommandPB_pb2.CommandResDTO()
        request.action = CMD_ACTION_FIRMWARE_UPGRADE
        request.package_nub = 1
        request.tid = int(time.time())
        request.data = 'http://fwupdate.hoymiles.com/cfs/bin/2311/06/,1488725943932555264.bin\r'.encode('utf-8')

        command = CMD_CLOUD_COMMAND_RES_DTO
        return self.send_request(command, request, CommandPB_pb2.CommandReqDTO)
    

    def restart(self):

        request = CommandPB_pb2.CommandResDTO()
        request.action = CMD_ACTION_RESTART
        request.package_nub = 1
        request.tid = int(time.time())

        command = CMD_CLOUD_COMMAND_RES_DTO
        return self.send_request(command, request, CommandPB_pb2.CommandReqDTO)


    def turn_on(self):

        request = CommandPB_pb2.CommandResDTO()
        request.action = CMD_ACTION_TURN_ON
        request.package_nub = 1
        request.dev_kind = 1
        request.tid = int(time.time())

        command = CMD_CLOUD_COMMAND_RES_DTO
        return self.send_request(command, request, CommandPB_pb2.CommandReqDTO)
    
    def turn_off(self):

        request = CommandPB_pb2.CommandResDTO()
        request.action = CMD_ACTION_TURN_OFF
        request.package_nub = 1
        request.dev_kind = 1
        request.tid = int(time.time())

        command = CMD_CLOUD_COMMAND_RES_DTO
        return self.send_request(command, request, CommandPB_pb2.CommandReqDTO)
    
    def get_information_data(self):

        request = InfomationData_pb2.InfoDataResDTO()
        request.time_ymd_hms = datetime.now().strftime("%Y-%m-%d %H:%M:%S").encode("utf-8")
        request.offset = 28800
        request.time = int(time.time())
        command = CMD_APP_INFO_DATA_RES_DTO
        return self.send_request(command, request, InfomationData_pb2.InfoDataReqDTO)
    

    
    def send_request(self, command: bytes, request: Any, response_type: Any, inverter_port: int = INVERTER_PORT):
        self.sequence = (self.sequence + 1) & 0xFFFF

        request_as_bytes = request.SerializeToString()
        crc16 = mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)(request_as_bytes)
        length = len(request_as_bytes) + 10

        # compose request message
        header = CMD_HEADER + command
        message = header + struct.pack('>HHH', self.sequence, crc16, length) + request_as_bytes

        address = (self.host, inverter_port)
        try:
            with socket.create_connection(address, timeout=0.5) as stream:
                stream.settimeout(5)
                stream.sendall(message)
                buf = stream.recv(1024)
        except (socket.error, socket.timeout) as e:
            logger.debug(f"{e}")
            self.set_state(NetworkState.Offline)
            return None
        
        read_length = struct.unpack('>H', buf[6:8])[0]

        try:
            parsed = response_type.FromString(buf[10:10 + read_length])

            if not parsed:
                raise ValueError("Parsing resulted in an empty or falsy value")

        except Exception as e:
            logger.debug(f"Failed to parse response: {e}")
            self.set_state(NetworkState.Unknown)
            return None

        self.set_state(NetworkState.Online)
        return parsed

