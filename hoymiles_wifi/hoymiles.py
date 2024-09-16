"""Hoymiles quirks for inverters and DTU."""

import struct
from enum import Enum

from hoymiles_wifi import logger


class InverterType(Enum):
    """Inverter type."""

    ONE = "1T"
    TWO = "2T"
    FOUR = "4T"
    SIX = "6T"


class InverterSeries(Enum):
    """Inverter series."""

    HM = "HM"
    HMS = "HMS"
    HMT = "HMT"


class InverterPower(Enum):
    """Inverter power."""

    P_100 = "100"
    P_250 = "250"
    P_300_350_400 = "300/350/400"
    P_400 = "400"
    P_500 = "500"
    P_600_700_800 = "600/700/800"
    P_1000 = "1000"
    P_800W_1000W = "800W/1000W"
    P_1000_1200_1500 = "1000/1200/1500"
    P_1200_1500 = "1200/1500"
    P_1600_1800_2000 = "1600/1800/2000"
    P_2250 = "2250"


power_mapping = {
    0x1011: InverterPower.P_100,
    0x1020: InverterPower.P_250,
    0x1021: InverterPower.P_300_350_400,
    0x1121: InverterPower.P_300_350_400,
    0x1125: InverterPower.P_400,
    0x1040: InverterPower.P_500,
    0x1041: InverterPower.P_600_700_800,
    0x1042: InverterPower.P_600_700_800,
    0x1141: InverterPower.P_600_700_800,
    0x1060: InverterPower.P_1000,
    0x1061: InverterPower.P_1200_1500,
    0x1161: InverterPower.P_1000_1200_1500,
    0x1164: InverterPower.P_1600_1800_2000,
    0x1412: InverterPower.P_800W_1000W,
    0x1382: InverterPower.P_2250,
}


class DTUType(Enum):
    """DTU type."""

    DTU_G100 = "DTU-G100"
    DTU_W100 = "DTU-W100"
    DTU_LITE_S = "DTU-Lite-S"
    DTU_LITE = "DTU-Lite"
    DTU_PRO = "DTU-PRO"
    DTU_PRO_S = "DTU-PRO-S"
    DTUBI = "DTUBI"
    DTU_W100_LITE_S = "DTU-W100/DTU-Lite-S"
    DTU_W_LITE = "DTU-WLite"


type_mapping = {
    0x10F7: DTUType.DTU_PRO,
    0x10FB: DTUType.DTU_PRO,
    0x4101: DTUType.DTU_PRO,
    0x10FC: DTUType.DTU_PRO,
    0x4120: DTUType.DTU_PRO,
    0x10F8: DTUType.DTU_PRO,
    0x4100: DTUType.DTU_PRO,
    0x10FD: DTUType.DTU_PRO,
    0x4121: DTUType.DTU_PRO,
    0x10D3: DTUType.DTU_W100_LITE_S,
    0x4110: DTUType.DTU_W100_LITE_S,
    0x10D8: DTUType.DTU_W100_LITE_S,
    0x4130: DTUType.DTU_W100_LITE_S,
    0x4132: DTUType.DTU_W100_LITE_S,
    0x4133: DTUType.DTU_W100_LITE_S,
    0x10D9: DTUType.DTU_W100_LITE_S,
    0x4111: DTUType.DTU_W100_LITE_S,
    0x10D2: DTUType.DTU_G100,
    0x10D6: DTUType.DTU_LITE,
    0x10D7: DTUType.DTU_LITE,
    0x4131: DTUType.DTU_LITE,
    0x1124: DTUType.DTUBI,
    0x1125: DTUType.DTUBI,
    0x1403: DTUType.DTUBI,
    0x1144: DTUType.DTUBI,
    0x1143: DTUType.DTUBI,
    0x1145: DTUType.DTUBI,
    0x1412: DTUType.DTUBI,
    0x1164: DTUType.DTUBI,
    0x1165: DTUType.DTUBI,
    0x1166: DTUType.DTUBI,
    0x1167: DTUType.DTUBI,
    0x1222: DTUType.DTUBI,
    0x1422: DTUType.DTUBI,
    0x1423: DTUType.DTUBI,
    0x1361: DTUType.DTUBI,
    0x1362: DTUType.DTUBI,
    0x1381: DTUType.DTUBI,
    0x1382: DTUType.DTUBI,
    0x4143: DTUType.DTUBI,
}


class MeterType(Enum):
    """Meter type."""

    DDSU666 = "DDSU666"
    DTSU666 = "DTSU666"


meter_mapping = {0x10C0: MeterType.DDSU666}


def format_number(number: int) -> str:
    """Format number to two digits."""

    return f"{number:02d}"


def generate_version_string(version_number: int) -> str:
    """Generate version string."""

    version_string = (
        format_number(version_number // 2048)
        + "."
        + format_number((version_number // 64) % 32)
        + "."
        + format_number(version_number % 64)
    )
    return version_string


def generate_sw_version_string(version_number: int) -> str:
    """Generate software version string."""

    version_number2 = version_number // 10000
    version_number3 = (version_number - (version_number2 * 10000)) // 100
    version_number4 = (version_number - (version_number2 * 10000)) - (
        version_number3 * 100
    )

    version_string = (
        format_number(version_number2)
        + "."
        + format_number(version_number3)
        + "."
        + format_number(version_number4)
    )
    return version_string


def generate_dtu_version_string(version_number: int, type: str = "") -> str:
    """Generate DTU version string."""

    version_string = ""
    version_number2 = version_number % 256
    version_number3 = (version_number // 256) % 16

    if type == "SRF":
        version_string += f"{format_number(version_number // 1048576)}.{format_number((version_number % 65536) // 4096)}.{format_number(version_number3)}.{format_number(version_number2)}"
    elif type == "HRF":
        version_string += f"{format_number(version_number // 65536)}.{format_number((version_number % 65536) // 4096)}.{format_number(version_number3)}.{format_number(version_number2)}"
    else:
        version_string += f"{format_number(version_number // 4096)}.{format_number(version_number3)}.{format_number(version_number2)}"

    return version_string


def generate_inverter_serial_number(serial_number: int) -> str:
    """Generate inverter serial number."""

    return hex(serial_number)[2:]


def convert_inverter_serial_number(serial_number_str: str) -> int:
    """Get inverter serial number from string."""

    return int(serial_number_str, 16)


def get_inverter_type(serial_bytes: bytes) -> InverterType:
    """Get inverter type."""

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

    if inverter_type is None:
        raise ValueError(
            f"Unknown inverter type: {hex(serial_bytes[0])} {hex(serial_bytes[1])}"
        )

    return inverter_type


def get_inverter_series(serial_bytes: bytes) -> InverterSeries:
    """Get inverter series."""

    series = None
    if serial_bytes[0] == 0x11:
        if (serial_bytes[1] & 0x0F) == 0x04:
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
        raise ValueError(
            f"Unknown series: {hex(serial_bytes[0])} {hex(serial_bytes[1])}!"
        )

    return series


def get_inverter_power(serial_bytes: bytes) -> InverterPower:
    """Get inverter power."""

    inverter_type_bytes = struct.unpack(">H", serial_bytes[:2])[0]
    power = power_mapping.get(inverter_type_bytes)

    if power is None:
        raise ValueError(
            f"Unknown power: {hex(serial_bytes[0])} {hex(serial_bytes[1])}!"
        )

    return power


def get_inverter_model_name(serial_number: str) -> str:
    """Get hardware model name."""

    serial_bytes = bytes.fromhex(serial_number)

    try:
        inverter_type = get_inverter_type(serial_bytes)
        inverter_series = get_inverter_series(serial_bytes)
        inverter_power = get_inverter_power(serial_bytes)
    except Exception as e:
        logger.error(e)
        return "Unknown"
    else:
        inverter_model_name = (
            inverter_series.value
            + "-"
            + inverter_power.value
            + "-"
            + inverter_type.value
        )
        return inverter_model_name


def get_dtu_model_type(serial_bytes: bytes) -> DTUType:
    """Get DTU model type."""

    dtu_type_bytes = struct.unpack(">H", serial_bytes[:2])[0]

    dtu_type = type_mapping.get(dtu_type_bytes)

    if dtu_type is None:
        raise ValueError(f"Unknown DTU: {serial_bytes[:2]}!")

    return dtu_type


def get_dtu_model_name(serial_number: str) -> str:
    """Get DTU model name."""

    serial_bytes = bytes.fromhex(serial_number)

    try:
        dtu_type = get_dtu_model_type(serial_bytes)
    except Exception as e:
        logger.error(e)
        return "Unknown"
    else:
        return dtu_type.value


def get_meter_model_type(serial_bytes: bytes) -> MeterType:
    """Get Meter model type."""

    dtu_type_bytes = struct.unpack(">H", serial_bytes[:2])[0]

    meter_type = meter_mapping.get(dtu_type_bytes)

    if meter_type is None:
        raise ValueError(f"Unknown Meter: {serial_bytes[:2]}!")

    return meter_type


def get_meter_model_name(serial_number: str) -> str:
    """Get Meter model name."""

    serial_bytes = bytes.fromhex(serial_number)

    try:
        meter_type = get_meter_model_type(serial_bytes)
    except Exception as e:
        logger.error(e)
        return "Unknown"
    else:
        return meter_type.value
