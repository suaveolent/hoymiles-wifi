"""Hoymiles quirks for inverters and DTU."""

import struct
from dataclasses import dataclass
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
    SOL_H = "SOL_H"


class InverterPower(Enum):
    """Inverter power."""

    P_100 = "100"
    P_250 = "250"
    P_300_350_400 = "300/350/400"
    P_400 = "400"
    P_400W = "400W"
    P_500 = "500"
    P_600_700_800 = "600/700/800"
    P_1000 = "1000"
    P_800W_1000W = "800W/1000W"
    P_1000_1200_1500 = "1000/1200/1500"
    P_1200_1500 = "1200/1500"
    P_1600_1800_2000 = "1600/1800/2000"
    P_2000DW = "2000DW"
    P_2250 = "2250"


power_mapping = {
    0x1011: InverterPower.P_100,
    0x1020: InverterPower.P_250,
    0x1021: InverterPower.P_300_350_400,
    0x1121: InverterPower.P_300_350_400,
    0x1125: InverterPower.P_400,
    0x1403: InverterPower.P_400W,
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
    0x2821: InverterPower.P_1000,
    0x1222: InverterPower.P_2000DW,
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
    DTU_SLS = "DTU-SLS"
    DTS_WIFI_G1 = "DTS-WIFI-G1"


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
    0x4141: DTUType.DTUBI,
    0x4143: DTUType.DTUBI,
    0x4144: DTUType.DTUBI,
    0xD030: DTUType.DTU_SLS,
    0x4301: DTUType.DTS_WIFI_G1,
}


class MeterType(Enum):
    """Meter type."""

    DDSU666 = "DDSU666"
    DTSU666 = "DTSU666"


meter_mapping = {
    0x10C0: MeterType.DDSU666,
    0x37FF: MeterType.DTSU666,
}


class BMSWorkingMode(Enum):
    """BMS working mode."""

    SELF_USE = 1
    ECONOMIC = 2
    BACKUP_POWER = 3
    PURE_OFF_GRID = 4
    FORCED_CHARGING = 5
    FORCED_DISCHARGE = 6
    PEAK_SHAVING = 7
    TIME_OF_USE = 8
    UNKNOWN = -1


class TariffType(Enum):
    """Tariff type for BMS working mode."""

    OFF_PEAK = 1
    PARTIAL_PEAK = 2
    PEAK = 3


@dataclass
class DurationBean:
    """Duration bean for BMS working mode."""

    start_time: str = None
    end_time: str = None
    in_price: float = None
    out_price: float = None
    type: TariffType = None


@dataclass
class TimeBean:
    """Time bean for BMS working mode."""

    durations: list[DurationBean] = None
    week: list[int] = None


@dataclass
class DateBean:
    """Date bean for BMS working mode."""

    end_date: str = None
    start_date: str = None
    time: list[TimeBean] = None


@dataclass
class TimePeriodBean:
    """Time period bean for BMS working mode."""

    charge_time_from: str = None
    charge_time_to: str = None
    discharge_time_from: str = None
    discharge_time_to: str = None
    charge_power: int = None
    discharge_power: int = None
    max_soc: int = None
    min_soc: int = None


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
    if serial_bytes[0] == 0x10:
        if (serial_bytes[1]) == 0x14:
            inverter_type = InverterType.TWO
    elif serial_bytes[0] == 0x11:
        if serial_bytes[1] in [0x25, 0x24, 0x22, 0x21]:
            inverter_type = InverterType.ONE
        elif serial_bytes[1] in [0x44, 0x42, 0x41]:
            inverter_type = InverterType.TWO
        elif serial_bytes[1] in [0x64, 0x62, 0x61]:
            inverter_type = InverterType.FOUR
    elif serial_bytes[0] == 0x12:
        if serial_bytes[1] in [0x22]:
            inverter_type = InverterType.FOUR
    elif serial_bytes[0] == 0x13:
        inverter_type = InverterType.SIX
    elif serial_bytes[0] == 0x14:
        if serial_bytes[1] in [0x03]:
            inverter_type = InverterType.ONE
        if serial_bytes[1] in [0x10, 0x12]:
            inverter_type = InverterType.TWO
    elif serial_bytes[0] == 0x28:
        if serial_bytes[1] in [0x21]:
            inverter_type = InverterType.TWO

    if inverter_type is None:
        raise ValueError(
            f"Unknown inverter type: {hex(serial_bytes[0])} {hex(serial_bytes[1])}"
        )

    return inverter_type


def get_inverter_series(serial_bytes: bytes) -> InverterSeries:
    """Get inverter series."""

    series = None
    if serial_bytes[0] == 0x10:
        if serial_bytes[1] & 0x03 == 0x02:
            series = InverterSeries.HM
        else:
            series = InverterSeries.HMS
    elif serial_bytes[0] == 0x11:
        if serial_bytes[1] & 0x0F == 0x04:
            series = InverterSeries.HMS
        else:
            series = InverterSeries.HM
    elif serial_bytes[0] == 0x12:
        series = InverterSeries.HMS
    elif serial_bytes[0] == 0x13:
        series = InverterSeries.HMT
    elif serial_bytes[0] == 0x14:
        series = InverterSeries.HMS
    elif serial_bytes[0] == 0x28:
        series = InverterSeries.SOL_H

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

    if serial_number[-1:] == "J":
        serial_number = serial_number[:-1]

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


def encode_date_time_range(
    from_date_time: str, to_date_time: str, delimiter: str = ":"
) -> int:
    """Encode date/time range into a 32-bit integer."""

    def parse_date_time(date_time_str):
        """Split the time string and ensures it has two numeric parts."""
        parts = (date_time_str or "00" + delimiter + "00").split(delimiter)
        if len(parts) != 2:
            raise ValueError(f"Invalid date/time format: {date_time_str}")
        return [int(p) for p in parts]

    # Extract hours/days and minutes/month for both datetimes
    from_first, from_second = parse_date_time(from_date_time)
    to_first, to_second = parse_date_time(to_date_time)

    # Encode into a 32-bit integer
    encoded = (from_first << 24) | (from_second << 16) | (to_first << 8) | to_second
    return encoded


def encode_week_range(week: list[int]) -> int:
    """Encode week range into an integer."""
    week = week if week is not None else []

    i3 = 0
    for value in week:
        if value == 1:
            i3 |= 1
        elif value == 2:
            i3 |= 2
        elif value == 3:
            i3 |= 4
        elif value == 4:
            i3 |= 8
        elif value == 5:
            i3 |= 16
        elif value == 6:
            i3 |= 32
        elif value == 7:
            i3 |= 64

    return i3


def float_to_scaled_int(float_value: float) -> int:
    """Convert a float value to an integer scaled by 100."""
    return int((float_value if float_value is not None else 0.0) * 100)
