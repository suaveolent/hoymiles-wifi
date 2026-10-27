"""Decode versioned grid-profile sections without changing inverter settings.

Format reference: https://github.com/tbnobody/OpenDTU/blob/master/lib/Hoymiles/src/parser/GridProfileParser.cpp
Local replies contain big-endian words; cloud captures contain little-endian words.
"""

from dataclasses import dataclass

_PROFILE_NAMES = {
    0x0C01: "AT_TOR_Erzeuger_Q(U)",
}


def get_grid_profile_name(profile_code: int | None) -> str | None:
    """Return the confirmed profile name, or None for an unknown code."""
    return _PROFILE_NAMES.get(profile_code)


def get_grid_profile_version(profile_version: int) -> str:
    """Decode the packed major/minor/patch version reported by app-info."""
    major = (profile_version >> 12) & 0x0F
    minor = (profile_version >> 8) & 0x0F
    patch = profile_version & 0xFF
    return f"{major}.{minor}.{patch}"


@dataclass(frozen=True)
class GridProfileValue:
    """A scaled setting and its original unsigned wire value."""

    name: str
    value: float
    unit: str
    raw_value: int


@dataclass(frozen=True)
class GridProfileSection:
    """A complete section with a recognized layout version."""

    name: str
    version: int
    values: list[GridProfileValue]


@dataclass(frozen=True)
class DecodedGridProfile:
    """Decoded settings, retaining bytes that could not be interpreted."""

    byte_order: str
    version: str
    sections: list[GridProfileSection]
    undecoded_hex: str


# Each setting specifies its unit and the divisor applied to the signed wire word.
_VOLTAGE = (
    ("nominal_voltage", "V", 10),
    ("low_voltage_1", "V", 10),
    ("low_voltage_1_trip_time", "s", 10),
    ("high_voltage_1", "V", 10),
    ("high_voltage_1_trip_time", "s", 10),
    ("low_voltage_2", "V", 10),
    ("low_voltage_2_trip_time", "s", 100),
    ("high_voltage_2", "V", 10),
    ("high_voltage_2_trip_time", "s", 100),
)
_AVERAGE_VOLTAGE = ("average_high_voltage_10_minutes", "V", 10)
_FREQUENCY = (
    ("nominal_frequency", "Hz", 100),
    ("low_frequency_1", "Hz", 100),
    ("low_frequency_1_trip_time", "s", 10),
    ("high_frequency_1", "Hz", 100),
    ("high_frequency_1_trip_time", "s", 10),
)
_RECONNECTION = (
    ("reconnect_time", "s", 10),
    ("reconnect_high_voltage", "V", 10),
    ("reconnect_low_voltage", "V", 10),
    ("reconnect_high_frequency", "Hz", 100),
    ("reconnect_low_frequency", "Hz", 100),
)
_FREQUENCY_WATT = (
    ("enabled", "", 1),
    ("start_frequency", "Hz", 100),
    ("droop_slope", "%Pn/Hz", 10),
    ("recovery_ramp_rate", "%Pn/s", 100),
)
_VOLT_WATT = (
    ("enabled", "", 1),
    ("start_voltage", "V", 10),
    ("end_voltage", "V", 10),
    ("droop_slope", "%Pn/V", 100),
)
_VOLT_VAR = (
    ("enabled", "", 1),
    ("voltage_1", "V", 10),
    ("reactive_power_1", "%Pn", 10),
    ("voltage_2", "V", 10),
    ("voltage_3", "V", 10),
    ("voltage_4", "V", 10),
    ("reactive_power_4", "%Pn", 10),
)
_LAYOUTS = {
    (0x00, 0x00): ("voltage", _VOLTAGE[:5]),
    (0x00, 0x01): ("voltage", _VOLTAGE[:5] + _VOLTAGE[7:]),
    (0x00, 0x02): ("voltage", _VOLTAGE[:7]),
    (0x00, 0x0A): ("voltage", (*_VOLTAGE[:7], _AVERAGE_VOLTAGE)),
    (0x00, 0x0B): ("voltage", (*_VOLTAGE, _AVERAGE_VOLTAGE)),
    (0x00, 0x0C): (
        "voltage",
        (
            *_VOLTAGE,
            ("high_voltage_3", "V", 10),
            ("high_voltage_3_trip_time", "s", 100),
            _AVERAGE_VOLTAGE,
        ),
    ),
    (0x10, 0x00): ("frequency", _FREQUENCY),
    (0x10, 0x03): (
        "frequency",
        (
            *_FREQUENCY,
            ("low_frequency_2", "Hz", 100),
            ("low_frequency_2_trip_time", "s", 100),
            ("high_frequency_2", "Hz", 100),
            ("high_frequency_2_trip_time", "s", 100),
        ),
    ),
    (0x20, 0x00): ("island_detection", (("enabled", "", 1),)),
    (0x30, 0x03): ("reconnection", _RECONNECTION),
    (0x30, 0x07): (
        "reconnection",
        (
            *_RECONNECTION,
            ("short_interruption_reconnect_time", "s", 10),
            ("short_interruption_time", "s", 10),
        ),
    ),
    (0x40, 0x00): (
        "ramp_rates",
        (
            ("normal_ramp_up_rate", "%rated/s", 100),
            ("soft_start_ramp_up_rate", "%rated/s", 100),
        ),
    ),
    (0x50, 0x00): ("frequency_watt", _FREQUENCY_WATT),
    (0x50, 0x01): (
        "frequency_watt",
        (*_FREQUENCY_WATT, ("recovery_high_frequency", "Hz", 10)),
    ),
    (0x50, 0x08): (
        "frequency_watt",
        (
            *_FREQUENCY_WATT,
            ("recovery_high_frequency", "Hz", 10),
            ("recovery_low_frequency", "Hz", 100),
        ),
    ),
    (0x50, 0x11): (
        "frequency_watt",
        (*_FREQUENCY_WATT, ("settling_time", "s", 10)),
    ),
    (0x60, 0x00): ("volt_watt", _VOLT_WATT),
    (0x60, 0x04): ("volt_watt", _VOLT_WATT),
    (0x70, 0x00): ("active_power_control", (("enabled", "", 1),)),
    (0x70, 0x02): (
        "active_power_control",
        (("enabled", "", 1), ("ramp_rate", "%Pn/s", 100)),
    ),
    (0x80, 0x00): ("volt_var", _VOLT_VAR),
    (0x80, 0x01): ("volt_var", (*_VOLT_VAR, ("settling_time", "s", 10))),
    (0x90, 0x00): (
        "specified_power_factor",
        (("enabled", "", 1), ("power_factor", "", 100)),
    ),
    (0xA0, 0x02): (
        "reactive_power_control",
        (("enabled", "", 1), ("reactive_power", "%Sn", 1)),
    ),
    (0xB0, 0x00): (
        "watt_power_factor",
        (
            ("enabled", "", 1),
            ("start_power", "%Pn", 10),
            ("rated_power_factor", "", 100),
        ),
    ),
}


def decode_grid_profile(
    data: bytes, profile_code: int, profile_version: int
) -> DecodedGridProfile | None:
    """Select byte order from app-info IDs and decode complete known sections."""
    if len(data) < 4:
        return None
    byte_order = next(
        (
            order
            for order in ("big", "little")
            if int.from_bytes(data[:2], order) == profile_code
            and int.from_bytes(data[2:4], order) == profile_version
        ),
        None,
    )
    if byte_order is None:
        return None
    canonical = b"".join(
        data[pos : pos + 2][:: 1 if byte_order == "big" else -1]
        for pos in range(0, len(data), 2)
    )
    version = get_grid_profile_version(profile_version)
    sections = []
    position = 4
    while position + 2 <= len(canonical):
        layout = _LAYOUTS.get(tuple(canonical[position : position + 2]))
        if layout is None:
            break
        name, fields = layout
        end = position + 2 + len(fields) * 2
        if end > len(canonical):
            break
        values = []
        for index, (field_name, unit, divisor) in enumerate(fields):
            offset = position + 2 + index * 2
            word = canonical[offset : offset + 2]
            values.append(
                GridProfileValue(
                    field_name,
                    int.from_bytes(word, "big", signed=True) / divisor,
                    unit,
                    int.from_bytes(word, "big"),
                )
            )
        sections.append(GridProfileSection(name, canonical[position + 1], values))
        position = end
    return DecodedGridProfile(byte_order, version, sections, data[position:].hex())
