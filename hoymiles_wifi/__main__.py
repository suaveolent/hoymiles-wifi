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
            response = inverter.update_state()
            if response:
                print(f"Inverter State: {response}")
            else:
                print("Unable to retrieve inverter state")

            # Sleep for a while before the next update
            time.sleep(60)
    except KeyboardInterrupt:
        print("Exiting.")

if __name__ == "__main__":
    main()
