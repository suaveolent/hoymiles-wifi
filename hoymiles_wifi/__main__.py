"""Contains the main functionality of the hoymiles_wifi package."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict, dataclass, is_dataclass
from pprint import pprint

from google.protobuf.json_format import MessageToDict, MessageToJson
from google.protobuf.message import Message

from hoymiles_wifi.const import (
    DTU_FIRMWARE_URL_00_01_11,
    IS_ENCRYPTED_BIT_INDEX,
    MAX_POWER_LIMIT,
)
from hoymiles_wifi.dtu import DTU
from hoymiles_wifi.hoymiles import (
    BMSWorkingMode,
    DateBean,
    TimePeriodBean,
    generate_dtu_version_string,
    generate_inverter_serial_number,
    generate_sw_version_string,
    generate_version_string,
    get_dtu_model_name,
    get_inverter_model_name,
    get_meter_model_name,
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
)
from hoymiles_wifi.utils import (
    parse_time_periods_input,
    parse_time_settings_input,
    prompt_user_for_bms_working_mode,
    promt_user_for_rate_time_range,
)

RED = "\033[91m"
END = "\033[0m"


@dataclass
class VersionInfo:
    """Represents version information for the hoymiles_wifi package."""

    dtu_hw_version: str
    dtu_sw_version: str
    inverter_hw_version: str
    inverter_sw_version: str

    def __str__(self: VersionInfo) -> str:
        """Return a string representation of the VersionInfo object."""

        return (
            f'dtu_hw_version: "{self.dtu_hw_version}"\n'
            f'dtu_sw_version: "{self.dtu_sw_version}"\n'
            f'inverter_hw_version: "{self.inverter_hw_version}"\n'
            f'inverter_sw_version: "{self.inverter_sw_version}"\n'
        )

    def to_dict(self: VersionInfo) -> dict:
        """Convert the VersionInfo object to a dictionary."""

        return asdict(self)


# Inverter commands
async def async_get_real_data_new(
    dtu: DTU,
) -> RealDataNew_pb2.RealDataNewResDTO | None:
    """Get real data from the inverter asynchronously."""
    return await dtu.async_get_real_data_new()


async def async_get_real_data(dtu: DTU) -> RealData_pb2.RealDataResDTO | None:
    """Get real data from the inverter asynchronously."""

    return await dtu.async_get_real_data()


async def async_get_config(dtu: DTU) -> GetConfig_pb2.GetConfigResDTO | None:
    """Get the config from the inverter asynchronously."""

    return await dtu.async_get_config()


async def async_network_info(
    dtu: DTU,
) -> NetworkInfo_pb2.NetworkInfoResDTO | None:
    """Get network information from the inverter asynchronously."""

    return await dtu.async_network_info()


async def async_app_information_data(
    dtu: DTU,
) -> APPInfomationData_pb2.AppInfomationDataResDTO | None:
    """Get application information data from the inverter asynchronously."""

    return await dtu.async_app_information_data()


async def async_app_get_hist_power(
    dtu: DTU,
) -> AppGetHistPower_pb2.AppGetHistPowerResDTO:
    """Get historical power data from the inverter asynchronously."""

    return await dtu.async_app_get_hist_power()


async def async_set_power_limit(
    dtu: DTU,
    power_limit: int = -1,
    interactive_mode: bool = True,
) -> CommandPB_pb2.CommandResDTO | None:
    """Set the power limit of the inverter asynchronously."""

    if interactive_mode:
        print(  # noqa: T201
            RED
            + "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! WARNING !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
            + "!!! Danger zone! This will change the power limit of the dtu. !!!\n"
            + "!!!   Please be careful and make sure you know what you are doing. !!!\n"
            + "!!!          Only proceed if you know what you are doing.          !!!\n"
            + "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! WARNING !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
            + END,
        )

        cont = input("Do you want to continue? (y/n): ")
        if cont != "y":
            return None

        power_limit = int(input("Enter the new power limit (0-100): "))

    if power_limit < 0 or power_limit > MAX_POWER_LIMIT:
        print("Error. Invalid power limit!")  # noqa: T201
        return None

    print(f"Setting power limit to {power_limit}%")  # noqa: T201

    if interactive_mode:
        cont = input("Are you sure? (y/n): ")

        if cont != "y":
            return None

    return await dtu.async_set_power_limit(power_limit)


async def async_set_wifi(dtu: DTU) -> CommandPB_pb2.CommandResDTO | None:
    """Set the wifi SSID and password of the inverter asynchronously."""

    wifi_ssid = input("Enter the new wifi SSID: ").strip()
    wifi_password = input("Enter the new wifi password: ").strip()
    print(f'Setting wifi to "{wifi_ssid}"')  # noqa: T201
    print(f'Setting wifi password to "{wifi_password}"')  # noqa: T201
    cont = input("Are you sure? (y/n): ")
    if cont != "y":
        return None
    return await dtu.async_set_wifi(wifi_ssid, wifi_password)


async def async_firmware_update(dtu: DTU) -> CommandPB_pb2.CommandResDTO | None:
    """Update the firmware of the DTU asynchronously."""

    print(  # noqa: T201
        RED
        + "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! WARNING !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
        + "!!!    Danger zone! This will update the firmeware of the DTU.     !!!\n"
        + "!!!  Please be careful and make sure you know what you are doing.  !!!\n"
        + "!!!          Only proceed if you know what you are doing.          !!!\n"
        + "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! WARNING !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
        + END,
    )

    cont = input("Do you want to continue? (y/n): ")
    if cont != "y":
        return None

    print("Please select a firmware version:")  # noqa: T201
    print("1.) V00.01.11")  # noqa: T201
    print("2.) Custom URL")  # noqa: T201

    while True:
        selection = input("Enter your selection (1 or 2): ")

        if selection == "1":
            url = DTU_FIRMWARE_URL_00_01_11
            break
        if selection == "2":
            url = input("Enter the custom URL: ").strip()
            break

        print("Invalid selection. Please enter 1 or 2.")  # noqa: T201

    print()  # noqa: T201
    print(f'Firmware update URL: "{url}"')  # noqa: T201
    print()  # noqa: T201

    cont = input("Do you want to continue? (y/n): ")
    if cont != "y":
        return None

    return await dtu.async_update_dtu_firmware()


async def async_restart_dtu(dtu: DTU) -> CommandPB_pb2.CommandResDTO | None:
    """Restart the DTU asynchronously."""

    cont = input("Do you want to restart the DTU? (y/n): ")
    if cont != "y":
        return None

    return await dtu.async_restart_dtu()


async def async_turn_on_inverter(dtu: DTU) -> CommandPB_pb2.CommandResDTO | None:
    """Turn on the inverter asynchronously."""

    inverter_serial = input("Enter the inverter serial number to turn *ON*: ")

    cont = input(f"Do you want to turn *ON* the Inverter {inverter_serial}? (y/n): ")
    if cont != "y":
        return None

    return await dtu.async_turn_on_inverter(inverter_serial)


async def async_turn_off_inverter(dtu: DTU) -> CommandPB_pb2.CommandResDTO | None:
    """Turn off the inverter asynchronously."""

    inverter_serial = input("Enter the inverter serial number to turn *OFF*: ")

    cont = input(f"Do you want to turn *OFF* the Inverter {inverter_serial}? (y/n): ")
    if cont != "y":
        return None

    return await dtu.async_turn_off_inverter(inverter_serial)


async def async_get_information_data(
    dtu: DTU,
) -> InfomationData_pb2.InfomationDataResDTO:
    """Get information data from the dtu asynchronously."""

    return await dtu.async_get_information_data()


async def async_get_version_info(dtu: DTU) -> VersionInfo | None:
    """Get version information from the dtu asynchronously."""

    response = await async_app_information_data(dtu)

    if not response:
        return None

    return VersionInfo(
        dtu_hw_version="H"
        + generate_dtu_version_string(response.dtu_info.dtu_hw_version),
        dtu_sw_version="V"
        + generate_dtu_version_string(response.dtu_info.dtu_sw_version),
        inverter_hw_version="H"
        + generate_version_string(response.pv_info[0].pv_hw_version),
        inverter_sw_version="V"
        + generate_sw_version_string(response.pv_info[0].pv_sw_version),
    )


async def async_heatbeat(dtu: DTU) -> APPHeartbeatPB_pb2.HBReqDTO | None:
    """Request a heartbeat from the dtu asynchronously."""

    return await dtu.async_heartbeat()


async def async_identify_dtu(dtu: DTU) -> str:
    """Identify the DTU asynchronously."""

    real_data = await async_get_real_data_new(dtu)
    dtu_model_name = get_dtu_model_name(real_data.device_serial_number)

    return {real_data.device_serial_number: dtu_model_name}


async def async_identify_inverters(dtu: DTU) -> list[str]:
    """Identify the DTU asynchronously."""

    inverter_models = {}
    real_data = await async_get_real_data_new(dtu)
    if real_data:
        for sgs_data in real_data.sgs_data:
            serial_number = generate_inverter_serial_number(sgs_data.serial_number)
            inverter_model = get_inverter_model_name(serial_number)
            inverter_models[serial_number] = inverter_model

        for tgs_data in real_data.tgs_data:
            serial_number = generate_inverter_serial_number(tgs_data.serial_number)
            inverter_model = get_inverter_model_name(serial_number)
            inverter_models[serial_number] = inverter_model

    return inverter_models


async def async_identify_meters(dtu: DTU) -> list[str]:
    """Identify the meters asynchronously."""

    meter_models = {}
    real_data = await async_get_real_data_new(dtu)
    if real_data:
        for meter_model in real_data.meter_data:
            serial_number = generate_inverter_serial_number(meter_model.serial_number)
            meter_model = get_meter_model_name(serial_number)
            meter_models[serial_number] = meter_model

    return meter_models


async def async_get_alarm_list(dtu: DTU) -> None:
    """Get alarm list from the dtu asynchronously."""

    return await dtu.async_get_alarm_list()


async def async_enable_performance_data_mode(dtu: DTU) -> None:
    """Enable performance data mode asynchronously."""

    return await dtu.async_enable_performance_data_mode()


async def async_get_gateway_info(dtu: DTU) -> GWInfo_pb2.GWInfoReqDTO | None:
    """Get gateway info."""

    return await dtu.async_get_gateway_info()


async def async_get_gateway_network_info(dtu: DTU) -> GWNetInfo_pb2.GWNetInfoReq | None:
    """Get gateway network info."""

    gateway_info = await dtu.async_get_gateway_info()

    return await dtu.async_get_gateway_network_info(gateway_info.serial_number)


async def async_get_energy_storage_registry(dtu: DTU) -> ESRegPB_pb2.ESRegReqDTO | None:
    """Get energy storage registry from the dtu asynchronously."""

    gateway_info = await dtu.async_get_gateway_info()

    return await dtu.async_get_energy_storage_registry(
        dtu_serial_number=gateway_info.serial_number
    )


async def async_get_energy_storage_data(
    dtu: DTU,
) -> list[ESData_pb2.ESDataReqDTO] | None:
    """Get energy storage registry from the dtu asynchronously."""

    gateway_info = await dtu.async_get_gateway_info()

    if gateway_info is None:
        return None

    registry = await dtu.async_get_energy_storage_registry(
        dtu_serial_number=gateway_info.serial_number
    )

    if registry is None:
        return None

    responses = []
    for inverter in registry.inverters:
        storage_data = await dtu.async_get_energy_storage_data(
            dtu_serial_number=gateway_info.serial_number,
            inverter_serial_number=inverter.serial_number,
        )
        if storage_data is not None:
            responses.append(storage_data)

    return responses


async def async_set_energy_storage_working_mode(
    dtu: DTU,
    bms_working_mode: BMSWorkingMode = None,
    inverter_serial_number: int = None,
    interactive_mode: bool = True,
    rev_soc: int = None,
    max_power: int = None,
    peak_soc: int = None,
    peak_meter_power: int = None,
    time_settings_str: str = None,
    time_periods_str: str = None,
) -> ESUserSet_pb2.ESUserSetPutReqDTO | None:
    """Set the working mode of the energy storage."""

    gateway_info = await dtu.async_get_gateway_info()

    if gateway_info is None:
        return None

    registry = await dtu.async_get_energy_storage_registry(
        dtu_serial_number=gateway_info.serial_number
    )

    if registry is None or not registry.inverters:
        return None

    if interactive_mode:
        return await async_set_energy_storage_working_mode_interactive(
            dtu,
            dtu_serial_number=gateway_info.serial_number,
            registry=registry,
            bms_working_mode=bms_working_mode,
        )

    else:
        time_settings = None
        time_periods = None

        if inverter_serial_number is None:
            print("Error. No inverter serial number provided!")  # noqa: T201
            return None

        if rev_soc is None:
            print("Error. No reserve SOC provided!")  # noqa: T201
            return None

        if bms_working_mode == BMSWorkingMode.ECONOMIC:
            time_settings: list[DateBean] = parse_time_settings_input(time_settings_str)
            if not time_settings:
                print("Error. Invalid time settings!")  # noqa: T201
                return None

        elif bms_working_mode in (
            BMSWorkingMode.FORCED_CHARGING,
            BMSWorkingMode.FORCED_DISCHARGE,
        ):
            if max_power is None:
                print("Error. No max power provided!")  # noqa: T201
                return None

        elif bms_working_mode == BMSWorkingMode.PEAK_SHAVING:
            if peak_soc is None:
                print("Error. No peak SOC provided!")  # noqa: T201
                return None

            if peak_meter_power is None:
                print("Error. No peak meter power provided!")  # noqa: T201
                return None

        elif bms_working_mode == BMSWorkingMode.TIME_OF_USE:
            time_periods: list[TimePeriodBean] = parse_time_periods_input(
                time_periods_str
            )

            if not time_periods:
                print("Error. Invalid time periods!")  # noqa: T201
                return None

        return await dtu.async_set_energy_storage_working_mode(
            dtu_serial_number=gateway_info.serial_number,
            inverter_serial_number=inverter_serial_number,
            bms_working_mode=bms_working_mode,
            rev_soc=rev_soc,
            time_settings=time_settings,
            max_power=max_power,
            peak_soc=peak_soc,
            peak_meter_power=peak_meter_power,
            time_periods=time_periods,
        )


async def async_set_energy_storage_working_mode_interactive(
    dtu: DTU,
    dtu_serial_number: int,
    registry: ESRegPB_pb2.ESRegReqDTO,
    bms_working_mode: BMSWorkingMode = None,
) -> ESUserSet_pb2.ESUserSetPutReqDTO | None:
    """Set the working mode of the energy storage."""

    time_settings: list[DateBean] = None
    time_periods: list[TimePeriodBean] = None
    max_power: int = None
    peak_soc: int = None
    peak_meter_power: int = None

    print(  # noqa: T201
        RED
        + "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! WARNING !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
        + "!!! Danger zone! This will change the working mode of the energy storage. !!!\n"
        + "!!!      Please be careful and make sure you know what you are doing.     !!!\n"
        + "!!!              Only proceed if you know what you are doing.             !!!\n"
        + "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! WARNING !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
        + END,
    )

    print("Available inverters:")  # noqa: T201
    for idx, inverter in enumerate(registry.inverters, start=1):
        print(f"{idx}: {inverter.serial_number}")  # noqa: T201

    while True:
        try:
            selection = int(
                input(f"Select inverter number (1-{len(registry.inverters)}): ")
            )
            if 1 <= selection <= len(registry.inverters):
                selected_inverter = registry.inverters[selection - 1]
                break
            else:
                print("Invalid selection. Please choose a valid number.")  # noqa: T201
        except ValueError:
            print("Please enter a number.")  # noqa: T201
    inverter_serial_number = selected_inverter.serial_number

    print(f"Inverter serial number: {inverter_serial_number}")  # noqa: T201

    cont = input("Do you want to continue? (y/n): ")
    if cont != "y":
        return None

    bms_working_mode = prompt_user_for_bms_working_mode()

    if bms_working_mode is None:
        print("Error. Invalid working mode!")  # noqa: T201
        return None

    rev_soc = int(input("Enter the SOC to reserve: (0-100): "))
    if rev_soc < 0 or rev_soc > 100:
        print("Error. Invalid SOC!")  # noqa: T201
        return None

    if bms_working_mode == BMSWorkingMode.ECONOMIC:
        time_settings = []
        while True:
            print("Configuring time settings...")  # noqa: T201

            start_date = input("Please enter the start date (DD.MM): ").strip()
            end_date = input("Please enter the end date (DD.MM): ").strip()

            print("Configuring  time range 1...")  # noqa: T201
            time_range_1 = promt_user_for_rate_time_range()

            print("Configuring  time range 2...")  # noqa: T201
            time_range_2 = promt_user_for_rate_time_range()

            time_setting = DateBean()
            time_setting.start_date = start_date
            time_setting.end_date = end_date
            time_setting.time = [time_range_1, time_range_2]

            time_settings.append(time_setting)

            cont = input("Do you want to add another time setting? (y/n): ")
            if cont != "y":
                break
            else:
                continue

        print()  # noqa: T201
        print("Your time settings:")  # noqa: T201
        for time_setting in time_settings:
            pprint(asdict(time_setting))  # noqa: T203
        print()  # noqa: T201

        cont = input("Do you want to continue with these settings? (y/n): ")
        if cont != "y":
            return None

    elif bms_working_mode == BMSWorkingMode.FORCED_CHARGING:
        max_power = int(input("Enter the max charging power to set (0-100): "))
        if max_power < 0 or max_power > 100:
            print("Error. Invalid charging power!")  # noqa: T201
            return None

    elif bms_working_mode == BMSWorkingMode.FORCED_DISCHARGE:
        max_power = int(input("Enter the min discharge power to set (0-100): "))
        if max_power < 0 or max_power > 100:
            print("Error. Invalid discharge power!")  # noqa: T201
            return None

    elif bms_working_mode == BMSWorkingMode.PEAK_SHAVING:
        peak_soc = int(input("Enter baseline SOC to reserve: (0-100): "))
        if peak_soc < 0 or peak_soc > 100:
            print("Error. Invalid SOC!")  # noqa: T201
            return None

        peak_meter_power = int(input("Enter the peak meter power meter: "))

    elif bms_working_mode == BMSWorkingMode.TIME_OF_USE:
        time_periods = []

        while True:
            charge_time_from = input("Enter the charge time from (HH:MM): ").strip()
            charge_time_to = input("Enter the charge time to (HH:MM): ").strip()

            charge_power = int(input("Enter the charge power to set (0-100): "))

            if charge_power < 0 or charge_power > 100:
                print("Error. Invalid charge power!")  # noqa: T201
                return None

            max_soc = int(input("Enter the max SOC to set (0-100): "))
            if max_soc < 0 or max_soc > 100:
                print("Error. Invalid SOC!")  # noqa: T201
                return None

            discharge_time_from = input(
                "Enter the discharge time from (HH:MM): "
            ).strip()
            discharge_time_to = input("Enter the discharge time to (HH:MM): ").strip()

            discharge_power = int(input("Enter the discharge power to set (0-100): "))

            if discharge_power < 0 or discharge_power > 100:
                print("Error. Invalid discharge power!")  # noqa: T201
                return None

            min_soc = int(input("Enter the min SOC to set (0-100): "))
            if min_soc < 0 or min_soc > 100:
                print("Error. Invalid SOC!")  # noqa: T201
                return None

            time_period = TimePeriodBean()
            time_period.charge_time_from = charge_time_from
            time_period.charge_time_to = charge_time_to
            time_period.discharge_time_from = discharge_time_from
            time_period.discharge_time_to = discharge_time_to
            time_period.charge_power = charge_power
            time_period.discharge_power = discharge_power
            time_period.max_soc = max_soc
            time_period.min_soc = min_soc

            time_periods.append(time_period)

            cont = input("Do you want to add another time period? (y/n): ")
            if cont != "y":
                break
            else:
                continue

        print(f"Your time periods: {time_periods}")  # noqa: T201

        cont = input("Do you want to continue with these settings? (y/n): ")
        if cont != "y":
            return None

    return await dtu.async_set_energy_storage_working_mode(
        dtu_serial_number=dtu_serial_number,
        inverter_serial_number=inverter_serial_number,
        bms_working_mode=bms_working_mode,
        rev_soc=rev_soc,
        time_settings=time_settings,
        max_power=max_power,
        peak_soc=peak_soc,
        peak_meter_power=peak_meter_power,
        time_periods=time_periods,
    )


async def async_is_encrypted(dtu: DTU):
    """Check if the DTU is using encrypted communication."""

    app_information_data = await dtu.async_app_information_data()

    is_encrypted_info = {}

    if app_information_data and app_information_data.dtu_info.dfs:
        if (app_information_data.dtu_info.dfs >> IS_ENCRYPTED_BIT_INDEX) & 1:
            is_encrypted_info["is_encrypted"] = True
            is_encrypted_info["enc_rand"] = app_information_data.dtu_info.enc_rand.hex()

    else:
        is_encrypted_info["is_encrypted"] = False

    return is_encrypted_info


def print_invalid_command(command: str) -> None:
    """Print an invalid command message."""

    print(f"Invalid command: {command}")  # noqa: T201
    sys.exit(1)


async def main() -> None:
    """Execute the main function for the hoymiles_wifi package."""

    parser = argparse.ArgumentParser(description="Hoymiles DTU Monitoring")
    parser.add_argument(
        "--host", type=str, required=True, help="IP address or hostname of the DTU"
    )
    parser.add_argument(
        "--local_addr",
        type=str,
        required=False,
        help="IP address of the interface to bind to",
    )
    parser.add_argument(
        "--as-json",
        action="store_true",
        default=False,
        help="Format the output as JSON",
    )
    parser.add_argument(
        "--disable-interactive",
        action="store_true",
        default=False,
        help="Disables interactive mode, forcing non-interactive operations.",
    )
    parser.add_argument(
        "--power-limit",
        type=int,
        default=None,
        choices=range(0, 101),
        help="Power limit to set (0...100).",
    )

    parser.add_argument(
        "--bms_working_mode",
        type=int,
        choices=range(1, 9),  # Restrict input to 1 through 8
        default=-1,
        help="BMS working mode to set (1...8).",
    )

    parser.add_argument(
        "--inverter-serial-number",
        type=int,
        default=None,
        help="Inverter serial number to set.",
    )

    parser.add_argument(
        "--rev-soc",
        type=int,
        default=None,
        choices=range(0, 101),
        help="Reserved SOC to set (0...100).",
    )

    parser.add_argument(
        "--max-power",
        type=int,
        default=None,
        choices=range(0, 101),
        help="Max (dis-)charging power to set (0...100).",
    )

    parser.add_argument(
        "--peak-soc",
        type=int,
        default=None,
        choices=range(0, 101),
        help="Peak SOC to set (0...100).",
    )

    parser.add_argument(
        "--peak-meter-power",
        type=int,
        default=None,
        choices=range(0, 101),
        help="Peak meter power to set (0...100).",
    )

    parser.add_argument(
        "--time-settings",
        type=str,
        required=False,
        help="Time settings for the economic working mode (START_DATE|END_DATE|WEEKDAYS:DURATION,DURATION;WEEKDAYS:DURATION,DURATION||START_DATE|END_DATE|...)",
    )

    parser.add_argument(
        "--time-periods",
        type=str,
        required=False,
        help="Time periods for the time of use working mode (CHARGE_FROM-CHARGE_TO-CHARGE_POWER-MAX_SOC|DISCHARGE_FROM-DISCHARGE_TO-DISCHARGE_POWER-MIN_SOC||...)",
    )

    parser.add_argument(
        "--enc-rand",
        type=str,
        required=False,
        help="The inverter specific random string used for encryption, see command: is-encrypted",
    )

    parser.add_argument(
        "command",
        type=str,
        choices=[
            "get-real-data-new",
            "get-real-data",
            "get-config",
            "network-info",
            "app-information-data",
            "app-get-hist-power",
            "set-power-limit",
            "set-wifi",
            "firmware-update",
            "restart-dtu",
            "turn-on-inverter",
            "turn-off-inverter",
            "get-information-data",
            "get-version-info",
            "heartbeat",
            "identify-dtu",
            "identify-inverters",
            "identify-meters",
            "get-alarm-list",
            "enable-performance-data-mode",
            "get-energy-storage-registry",
            "get-energy-storage-data",
            "get-gateway-info",
            "get-gateway-network-info",
            "set-energy-storage-working-mode",
            "is-encrypted",
        ],
        help="Command to execute",
    )

    args = parser.parse_args()

    if args.enc_rand:
        dtu = DTU(
            args.host,
            args.local_addr,
            is_encrypted=True,
            enc_rand=bytes.fromhex(args.enc_rand),
        )
    else:
        dtu = DTU(args.host, args.local_addr)

    # Execute the specified command using a switch case
    switch = {
        "get-real-data-new": async_get_real_data_new,
        "get-real-data": async_get_real_data,
        "get-config": async_get_config,
        "network-info": async_network_info,
        "app-information-data": async_app_information_data,
        "app-get-hist-power": async_app_get_hist_power,
        "set-power-limit": async_set_power_limit,
        "set-wifi": async_set_wifi,
        "firmware-update": async_firmware_update,
        "restart-dtu": async_restart_dtu,
        "turn-on-inverter": async_turn_on_inverter,
        "turn-off-inverter": async_turn_off_inverter,
        "get-information-data": async_get_information_data,
        "get-version-info": async_get_version_info,
        "heartbeat": async_heatbeat,
        "identify-dtu": async_identify_dtu,
        "identify-inverters": async_identify_inverters,
        "identify-meters": async_identify_meters,
        "get-alarm-list": async_get_alarm_list,
        "enable-performance-data-mode": async_enable_performance_data_mode,
        "get-gateway-info": async_get_gateway_info,
        "get-gateway-network-info": async_get_gateway_network_info,
        "get-energy-storage-registry": async_get_energy_storage_registry,
        "get-energy-storage-data": async_get_energy_storage_data,
        "set-energy-storage-working-mode": async_set_energy_storage_working_mode,
        "is-encrypted": async_is_encrypted,
    }

    command_func = switch.get(args.command, print_invalid_command)
    if args.command == "set-power-limit":
        kwargs = {}
        kwargs["power_limit"] = args.power_limit
        kwargs["interactive_mode"] = not args.disable_interactive
        response = await command_func(dtu, **kwargs)
    if args.command == "set-energy-storage-working-mode":
        kwargs = {}
        kwargs["interactive_mode"] = not args.disable_interactive
        kwargs["bms_working_mode"] = BMSWorkingMode(args.bms_working_mode)
        kwargs["inverter_serial_number"] = args.inverter_serial_number
        kwargs["rev_soc"] = args.rev_soc
        kwargs["time_settings_str"] = args.time_settings
        kwargs["max_power"] = args.max_power
        kwargs["peak_soc"] = args.peak_soc
        kwargs["peak_meter_power"] = args.peak_meter_power
        kwargs["time_periods_str"] = args.time_periods

        response = await command_func(dtu, **kwargs)
    else:
        response = await command_func(dtu)

    if response:
        if args.as_json:
            if isinstance(response, Message):
                print(MessageToJson(response))  # noqa: T201
            elif isinstance(response, dict):
                print(json.dumps(response, indent=4))  # noqa: T201
            elif isinstance(response, list):
                json_list = [
                    MessageToDict(item) if isinstance(item, Message) else item
                    for item in response
                ]
                print(json.dumps(json_list, indent=4))  # noqa: T201
            elif is_dataclass(response):
                print(json.dumps(asdict(response), indent=4))  # noqa: T201
            else:
                print("ERROR: Response is not a valid dataclass instance.")  # noqa: T201
                print(f"Response type: {type(response)}")  # noqa: T201

        else:
            print(f"{args.command.capitalize()} Response: \n{response}")  # noqa: T201
    else:
        if args.as_json:
            print(  # noqa: T201
                json.dumps(
                    {"error": f"No response for {args.command.replace('_', ' ')}"},
                    indent=4,
                )
            )
        else:
            print(  # noqa: T201
                f"No response or unable to retrieve response for "
                f"{args.command.replace('_', ' ')}",
            )
        sys.exit(2)


def run_main() -> None:
    """Run the main function for the hoymiles_wifi package."""

    asyncio.run(main())


if __name__ == "__main__":
    run_main()
