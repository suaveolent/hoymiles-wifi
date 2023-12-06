import socket
import struct
from hoymiles_wifi import logger
from hoymiles_wifi.protos.RealData_pb2 import RealDataResDTO, HMSStateResponse
from crcmod import mkCrcFun
from datetime import datetime
import time


INVERTER_PORT = 10081

class NetworkState:
    Unknown = 0
    Online = 1
    Offline = 2

class Inverter:
    def __init__(self, host):
        self.host = host
        self.state = NetworkState.Unknown
        self.sequence = 0

    def set_state(self, new_state):
        if self.state != new_state:
            self.state = new_state
            logger.info(f"Inverter is {new_state}")

    def update_state(self):
        self.sequence = (self.sequence + 1) & 0xFFFF

        request = RealDataResDTO()
        # date = datetime.now()
        # time_string = date.strftime("%Y-%m-%d %H:%M:%S")
        # request.ymd_hms = time_string
        # request.cp = 23 + self.sequence
        # request.offset = 0
        # request.time = int(time.time())
        header = b"\x48\x4d\xa3\x03"
        request_as_bytes = request.SerializeToString()
        crc16 = mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)(request_as_bytes)
        length = len(request_as_bytes) + 10

        # compose request message
        message = header + struct.pack('>HHHH', self.sequence, crc16, length, 0) + request_as_bytes

        address = (self.host, INVERTER_PORT)
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
        parsed = HMSStateResponse.FromString(buf[10:10+read_length])

        if not parsed:
            logger.debug(f"Failed to parse response")
            self.set_state(NetworkState.Offline)
            return None

        self.set_state(NetworkState.Online)
        return parsed
