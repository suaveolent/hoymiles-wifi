import argparse
from hoymiles_wifi.inverter import Inverter
import time

def main():
    parser = argparse.ArgumentParser(description="Hoymiles HMS Monitoring")
    parser.add_argument("--host", type=str, required=True, help="IP address or hostname of the inverter")
    parser.add_argument("command", type=str, choices=['get-real-data-new', 'get-real-data-hms', 'get-real-data', 'get-config', 'network-info', 'app-information-data', 'app-get-hist-power'], help="Command to execute")
    args = parser.parse_args()

    inverter = Inverter(args.host)

    try:
        while True:
            # Execute the specified command
            response = getattr(inverter, args.command, lambda: None)()
            
            if response:
                print(f"{args.command.capitalize()} Response: {response}")
            else:
                print(f"Unable to retrieve {args.command.replace('_', ' ')}")

            # Sleep for a while before the next update
            time.sleep(60)
    except KeyboardInterrupt:
        print("Exiting.")

if __name__ == "__main__":
    main()
