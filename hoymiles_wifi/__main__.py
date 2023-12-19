import argparse
from hoymiles_wifi.inverter2 import Inverter2
import time

def main():
    parser = argparse.ArgumentParser(description="Hoymiles HMS Monitoring")
    parser.add_argument("ip_address", type=str, help="IP address or hostname of the inverter")
    args = parser.parse_args()

    inverter = Inverter2(args.ip_address)

    try:
        while True:

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

            # Sleep for a while before the next update
            time.sleep(60)
    except KeyboardInterrupt:
        print("Exiting.")

if __name__ == "__main__":
    main()
