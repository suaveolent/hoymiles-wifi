import argparse
from hoymiles_wifi.inverter import Inverter

from hoymiles_wifi.utils import (
    generate_version_string,
    generate_sw_version_string, 
    generate_dtu_version_string
)


# Inverter commands
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

def set_power_limit(inverter):

    RED = '\033[91m'
    END = '\033[0m'

    print(RED + "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! WARNING !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" + END)
    print(RED + "!!! Danger zone! This will change the power limit of the inverter. !!!" + END)
    print(RED + "!!!  Please be careful and make sure you know what you are doing.  !!!" + END)
    print(RED + "!!!          Only proceed if you know what you are doing.          !!!" + END)
    print(RED + "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! WARNING !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" + END)
    print("")


    cont = input("Do you want to continue? (y/n): ")
    if(cont != 'y'):
        return

    power_limit = int(input("Enter the new power limit (0-100): "))

    if(power_limit < 0 or power_limit > 100):
        print("Error. Invalid power limit!")
        return
    
    print(f"Setting power limit to {power_limit}%")
    cont = input("Are you sure? (y/n): ") 

    if(cont != 'y'):
        return

    return inverter.set_power_limit(power_limit)


def set_wifi(inverter):
    wifi_ssid = input("Enter the new wifi SSID: ").strip()
    wifi_password = input("Enter the new wifi password: ").strip()
    print(f'Setting wifi to "{wifi_ssid}"')
    print(f'Setting wifi password to "{wifi_password}"')
    cont = input("Are you sure? (y/n): ")
    if(cont != 'y'):
        return
    return inverter.set_wifi(wifi_ssid, wifi_password)

def firmware_update(inverter):
    RED = '\033[91m'
    END = '\033[0m'

    print(RED + "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! WARNING !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" + END)
    print(RED + "!!!  Danger zone! This will update the firmeware of the inverter.  !!!" + END)
    print(RED + "!!!  Please be careful and make sure you know what you are doing.  !!!" + END)
    print(RED + "!!!          Only proceed if you know what you are doing.          !!!" + END)
    print(RED + "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! WARNING !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" + END)
    print("")

    cont = input("Do you want to continue? (y/n): ")
    if(cont != 'y'):
        return
    
    print()
    print("Updating firmware to version: V00.01.11...")
    print()

    cont = input("Do you want to continue? (y/n): ")
    if(cont != 'y'):
        return
    
    return inverter.firmware_update()

def restart(inverter):

    cont = input("Do you want to restart the device? (y/n): ")
    if(cont != 'y'):
        return
    
    return inverter.restart()

def turn_off(inverter):
    cont = input("Do you want to turn *OFF* the device? (y/n): ")
    if(cont != 'y'):
        return
    
    return inverter.turn_off()

def turn_on(inverter):
    cont = input("Do you want to turn *ON* the device? (y/n): ")
    if(cont != 'y'):
        return
    
    return inverter.turn_on()

def get_information_data(inverter):
    return inverter.get_information_data()

def get_version_info(inverter):
    response = app_information_data(inverter)
    return {
        "dtu_hw_version": "H" + generate_dtu_version_string(response.dtu_info.dtu_hw_version),
        "dtu_sw_version": "V" + generate_dtu_version_string(response.dtu_info.dtu_sw_version),
        "inverter_hw_version" : "H" + generate_version_string(response.pv_info[0].pv_hw_version),
        "inverter_sw_version": "V" + generate_sw_version_string(response.pv_info[0].pv_sw_version),
    }
    

def print_invalid_command(command):
    print(f"Invalid command: {command}")

def main():
    parser = argparse.ArgumentParser(description="Hoymiles HMS Monitoring")
    parser.add_argument(
        "--host", type=str, required=True, help="IP address or hostname of the inverter"
    )    
    parser.add_argument(
        "command",
        type=str,
        choices=[
            "get-real-data-new",
            "get-real-data-hms",
            "get-real-data",
            "get-config",
            "network-info",
            "app-information-data",
            "app-get-hist-power",
            "set-power-limit",
            "set-wifi",
            "firmware-update",
            "restart",
            "turn-on",
            "turn-off",
            "get-information-data",
            "get-version-info"
        ],
        help="Command to execute",
    )
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
        'set-power-limit': set_power_limit,
        'set-wifi': set_wifi,
        'firmware-update': firmware_update,
        'restart': restart,
        'turn-on': turn_on,
        'turn-off': turn_off,
        'get-information-data': get_information_data,
        'get-version-info': get_version_info,
    }

    command_func = switch.get(args.command, print_invalid_command)
    response = command_func(inverter)

    if response:
        print(f"{args.command.capitalize()} Response: {response}")
    else:
        print(f"No response or unable to retrieve response for {args.command.replace('_', ' ')}")


if __name__ == "__main__":
    main()
