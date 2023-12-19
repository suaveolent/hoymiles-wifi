import argparse
from hoymiles_wifi.inverter import Inverter
import time

def main():
    parser = argparse.ArgumentParser(description="Hoymiles HMS Monitoring")
    parser.add_argument("ip_address", type=str, help="IP address or hostname of the inverter")
    args = parser.parse_args()

    inverter = Inverter(args.ip_address)

    try:
        while True:

            response = inverter.get_real_data_new()
            if response:
                print(f"Get Real Data New Response: {response}")
            else:
                print("Unable to retrieve real data new")

            response = inverter.get_real_data_hms()
            if response:
                print(f"Get Real Data HMS Response: {response}")
            else:
                print("Unable to retrieve real data hms")

            response = inverter.get_real_data()
            if response:
                print(f"Get Real Data Response: {response}")
            else:
                print("Unable to retrieve real data")

            response = inverter.get_config()
            if response:
                print(f"Get Config Response: {response}")
            else:
                print("Unable to retrieve config")

            response = inverter.network_info()
            if response:
                print(f"Get Networking Info Response: {response}")
            else:
                print("Unable to retrieve network info")

            response = inverter.app_information_data()
            if response:
                print(f"Get App Info Response: {response}")
            else:
                print("Unable to retrieve network info")

            # Sleep for a while before the next update
            time.sleep(60)
    except KeyboardInterrupt:
        print("Exiting.")

if __name__ == "__main__":
    main()
