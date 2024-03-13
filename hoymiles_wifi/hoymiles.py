""""Hoymiles quirks for inverters and DTU"""

from enum import Enum
import struct

from hoymiles_wifi import logger

class InverterType(Enum):
    ONE = "1T"
    TWO = "2T"
    FOUR = "4T"
    SIX = "6T"

class InverterSeries(Enum):
    HM = "HM"
    HMS = "HMS"
    HMT = "HMT"

class InverterPower(Enum):
    P_100 = "100"
    P_250 = "250"
    P_300_350_400 = "300/350/400"
    P_400 = "400"
    P_500 = "500"
    P_600_700_800 = "600/700/800"
    P_800W = "800W"
    P_1000 = "1000"
    P_1000_1200_1500 = "1000/1200/1500"
    P_1200_1500 = "1200/1500"
    P_1600 = "1600"
    P_2000 = "2000"


class DTUType(Enum):
    DTU_G100 = "DTU-G100"
    DTU_W100 = "DTU-W100"
    DTU_LITE_S = "DTU-Lite-S"
    DTU_LITE = "DTU-Lite"
    DTU_PRO = "DTU-PRO"
    DTU_PRO_S = "DTU-PRO-S"
    DTU_HMS_W = "DTU-HMS-W"
    DTU_W100_LITE_S = "DTU-W100/DTU-Lite-S"
    DTU_W_LITE = "DTU-WLite"


def format_number(number) -> str:
    return "{:02d}".format(number)

def generate_version_string(version_number: int) -> str:
    version_string = format_number(version_number // 2048) + "." + format_number((version_number // 64) % 32) + "." + format_number(version_number % 64)
    return version_string

def generate_sw_version_string(version_number: int) -> str:

    version_number2 = version_number // 10000
    version_number3 = (version_number - (version_number2 * 10000)) // 100
    version_number4 = (version_number - (version_number2 * 10000)) - (version_number3 * 100)

    version_string = format_number(version_number2) + "." + format_number(version_number3) + "." + format_number(version_number4)
    return version_string


def generate_dtu_version_string(version_number: int, type: str = None) -> str:

    version_string = ""
    version_number2 = version_number % 256
    version_number3 = (version_number // 256) % 16

    if "SRF" == str:
        version_string += f"{format_number(version_number // 1048576)}.{format_number((version_number % 65536) // 4096)}.{format_number(version_number3)}.{format_number(version_number2)}"
    elif "HRF" == str:
        version_string += f"{format_number(version_number // 65536)}.{format_number((version_number % 65536) // 4096)}.{format_number(version_number3)}.{format_number(version_number2)}"
    else:
        version_string += f"{format_number(version_number // 4096)}.{format_number(version_number3)}.{format_number(version_number2)}"

    return version_string

def generate_inverter_serial_number(serial_number: int) -> str:
    return hex(serial_number)[2:]

def get_inverter_type(serial_bytes: bytes) -> InverterType:
    
    inverter_type = None
    # Access individual bytes
    if serial_bytes[0] == 0x11:
        if serial_bytes[1] in [0x25, 0x24, 0x22, 0x21]:
            inverter_type = InverterType.ONE
        elif serial_bytes[1] in [0x44, 0x42, 0x41]:
            inverter_type = InverterType.TWO
        elif serial_bytes[1] in [0x64, 0x62, 0x61]:
            inverter_type = InverterType.FOUR
    elif serial_bytes[0] == 0x13:
        inverter_type = InverterType.SIX
    elif serial_bytes[0] == 0x14:
        if serial_bytes[1] in [0x12]:
            inverter_type = InverterType.TWO

    if inverter_type == None:
        raise ValueError(f"Unknown inverter type: {hex(serial_bytes[0])} {hex(serial_bytes[1])}")

    return inverter_type


def get_inverter_series(serial_bytes: bytes) -> InverterSeries:

    series = None
    if serial_bytes[0] == 0x11:
        if (serial_bytes[1] & 0x0f) == 0x04:
            series = InverterSeries.HMS
        else:
            series = InverterSeries.HM
    elif serial_bytes[0] == 0x10:
        if serial_bytes[1] & 0x03 == 0x02:
            series = InverterSeries.HM
        else:
            series = InverterSeries.HMS
    elif serial_bytes[0] == 0x13:
        series = InverterSeries.HMT
    elif serial_bytes[0] == 0x14:
        series = InverterSeries.HMS
    
    if series is None:
        raise ValueError(f"Unknown series: {hex(serial_bytes[0])} {hex(serial_bytes[1])}!")
    
    return series

def get_inverter_power(serial_bytes: bytes) -> InverterPower:
    
    inverter_type_bytes = struct.unpack('>H', serial_bytes[:2])[0]

    power = None

    if inverter_type_bytes in [0x1011]:
        power = InverterPower.P_100
    elif inverter_type_bytes in [0x1020]:
        power = InverterPower.P_250
    elif inverter_type_bytes in [0x1021, 0x1121]:
        power = InverterPower.P_300_350_400
    elif inverter_type_bytes in [0x1125]:
        power = InverterPower.P_400
    elif inverter_type_bytes in [0x1040]:
        power = InverterPower.P_500
    elif inverter_type_bytes in [0x1041, 0x1042, 0x1141]:
        power = InverterPower.P_600_700_800
    elif inverter_type_bytes in [0x1060]:
        power = InverterPower.P_1000
    elif inverter_type_bytes in [0x1061]:
        power = InverterPower.P_1200_1500
    elif inverter_type_bytes in [0x1161]:
        power = InverterPower.P_1000_1200_1500
    elif inverter_type_bytes in [0x1164]:
        power = InverterPower.P_1600
    elif inverter_type_bytes in [0x1412]:
        power = InverterPower.P_800W

    if power is None:
        raise ValueError(f"Unknown power: {hex(serial_bytes[0])} {hex(serial_bytes[1])}!")
    
    return power




def get_hw_model_name(serial_number: str) -> str:

    if(serial_number == "22069994886948"):
        serial_number = generate_inverter_serial_number(int(serial_number))

    serial_bytes = bytes.fromhex(serial_number)

    try:
        inverter_type = get_inverter_type(serial_bytes)
        inverter_series = get_inverter_series(serial_bytes)
        inverter_power = get_inverter_power(serial_bytes)
    except Exception as e:
        logger.error(e)
        return "Unknown"
    else:
        inverter_model_name = inverter_series.value + "-" + inverter_power.value + "-" + inverter_type.value
        return inverter_model_name

def get_dtu_model_type(serial_bytes: bytes) -> DTUType:

    dtu_type = None

    dtu_type_bytes = struct.unpack('>H', serial_bytes[:2])[0]

    if (dtu_type_bytes in [0x10F7] or
        dtu_type_bytes in [0x10FB, 0x4101, 0x10FC, 0x4120] or
        dtu_type_bytes in [0x10F8, 0x4100, 0x10FD, 0x4121]):
        dtu_type = DTUType.DTU_PRO
    elif dtu_type_bytes in [0x10D3, 0x4110, 0x10D8, 0x4130, 0x4132, 0x4133, 0x10D9, 0x4111]:
        dtu_type = DTUType.DTU_W100_LITE_S
    elif dtu_type_bytes in [0x10D2]:
        dtu_type = DTUType.DTU_G100
    elif dtu_type_bytes in [0x10D6, 0x10D7, 0x4131]:
        dtu_type = DTUType.DTU_LITE
    elif (dtu_type_bytes in [0x1124, 0x1125, 0x1403] or
          dtu_type_bytes in [0x1144, 0x1143, 0x1145, 0x1412] or
          dtu_type_bytes in [0x1164, 0x1165, 0x1166, 0x1167, 0x1222, 0x1422, 0x1423] or
          dtu_type_bytes in [0x1361, 0x1362] or
          dtu_type_bytes in [0x1381, 0x1382] or
          dtu_type_bytes in [0x4143]):
        dtu_type = DTUType.DTU_HMS_W

    if dtu_type is None:
        raise ValueError(f"Unknown DTU: {serial_bytes[:2]}!")

    return dtu_type

def get_dtu_model_name(serial_number: str) -> str:
        
    serial_bytes = bytes.fromhex(serial_number)

    try:
        dtu_type = get_dtu_model_type(serial_bytes)
    except Exception as e:
        logger.error(e)
        return "Unknown"
    else:
        return dtu_type.value

