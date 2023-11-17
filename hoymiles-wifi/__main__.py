from inverter import Inverter
import time

def main():
    # Replace 'your_inverter_ip' with the actual IP address or hostname of your inverter
    inverter = Inverter('192.168.1.190')

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