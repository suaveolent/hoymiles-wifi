import argparse
from hoymiles_wifi.inverter import Inverter
import time

def get_real_data_new(inverter):
    return inverter.get_real_data_new()

def get_real_data_hms(inverter):
    return inverter.get_real_data_hms()

def get_real_data(inverter):
    return inverter.get_real_data()

def get_config(inverter):
    return inverter.get_config()

def network_info(inverter):
    return inverter.network_info()

def app_information_data(inverter):
    return inverter.app_information_data()

def app_get_hist_power(inverter):
    return inverter.app_get_hist_power()

def print_invalid_command(command):
    print(f"Invalid command: {command}")

def main():
    parser = argparse.ArgumentParser(description="Hoymiles HMS Monitoring")
    parser.add_argument("--host", type=str, required=True, help="IP address or hostname of the inverter")
    parser.add_argument("command", type=str, choices=['get-real-data-new', 'get-real-data-hms', 'get-real-data', 'get-config', 'network-info', 'app-information-data', 'app-get-hist-power'], help="Command to execute")
    args = parser.parse_args()

    inverter = Inverter(args.host)

    # Execute the specified command using a switch case
    switch = {
        'get-real-data-new': get_real_data_new,
        'get-real-data-hms': get_real_data_hms,
        'get-real-data': get_real_data,
        'get-config': get_config,
        'network-info': network_info,
        'app-information-data': app_information_data,
        'app-get-hist-power': app_get_hist_power,
    }

    command_func = switch.get(args.command, print_invalid_command)
    response = command_func(inverter)

    if response:
        print(f"{args.command.capitalize()} Response: {response}")
    else:
        print(f"Unable to retrieve {args.command.replace('_', ' ')}")


if __name__ == "__main__":
    main()
