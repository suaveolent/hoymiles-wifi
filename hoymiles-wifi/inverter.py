import socket
import struct
from protos.RealData_pb2 import RealDataResDTO, HMSStateResponse
import crcmod
import logging
from datetime import datetime
import time

logging.basicConfig(level=logging.INFO)

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
            logging.info(f"Inverter is {new_state}")

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
        crc16_func = crcmod.predefined.Crc('modbus')
        crc16_func.update(request_as_bytes)
        crc16 = crc16_func.crcValue & 0xFFFF

        len_bytes = struct.pack('>H', len(request_as_bytes) + 10)

        message = header + struct.pack('>HHH', self.sequence, crc16, len(request_as_bytes)) + request_as_bytes

        ip = socket.gethostbyname(self.host)
        address = (ip, INVERTER_PORT)

        try:
            with socket.create_connection(address, timeout=0.5) as stream:
                stream.sendall(message)
                buf = stream.recv(1024)
        except socket.error as e:
            logging.debug(str(e))
            self.set_state(NetworkState.Offline)
            return None

        read_length = struct.unpack('>H', buf[6:8])[0]
        parsed = HMSStateResponse.FromString(buf[10:10 + read_length])

        if parsed is None:
            logging.debug("Error parsing response")
            self.set_state(NetworkState.Offline)
            return None

        self.set_state(NetworkState.Online)
        return parsed