"""Contains the main functionality of the hoymiles_wifi package."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict, dataclass

from google.protobuf.json_format import MessageToJson
from google.protobuf.message import Message

from hoymiles_wifi.const import DTU_FIRMWARE_URL_00_01_11, MAX_POWER_LIMIT
from hoymiles_wifi.dtu import DTU
from hoymiles_wifi.hoymiles import (
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
    GetConfig_pb2,
    InfomationData_pb2,
    NetworkInfo_pb2,
    RealData_pb2,
    RealDataNew_pb2,
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
) -> CommandPB_pb2.CommandResDTO | None:
    """Set the power limit of the inverter asynchronously."""

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


async def async_heatbeat(dtu: DTU) -> APPHeartbeatPB_pb2.APPHeartbeatResDTO | None:
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
        ],
        help="Command to execute",
    )
    args = parser.parse_args()

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
    }

    command_func = switch.get(args.command, print_invalid_command)
    response = await command_func(dtu)

    if response:
        if args.as_json:
            if isinstance(response, Message):
                print(MessageToJson(response))  # noqa: T201
            elif isinstance(response, dict):
                print(json.dumps(response, indent=4))  # noqa: T201
            else:
                print(json.dumps(asdict(response), indent=4))  # noqa: T201
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
