# hoymiles-wifi


This Python library facilitates communication with Hoymiles HMS microinverters, specifically targeting the HMS-XXXXW-T2 series.

**Disclaimer: This library is not affiliated with Hoymiles. It is an independent project developed to provide tools for interacting with Hoymiles HMS-XXXXW-T2 series micro-inverters featuring integrated WiFi DTU. Any trademarks or product names mentioned are the property of their respective owners.**


## Installation

```
$ pip install hoymiles-wifi
```

## Usage

You can integrate the library into your own project, or simply use it in the command line.

### Command line:

```
hoymiles-wifi [-h] --host HOST <command>

commands:
    get-real-data-new, 
    get-real-data-hms,
    get-real-data,
    get-config,
    network-info,
    app-information-data,
    app-get-hist-power,
    set-power-limit,
    set-wifi,
    firmware-update,
    restart,
    turn-on,
    turn-off,
    get-information-data,
    get-version-info
```

### Python code

```
from hoymiles_wifi.inverter import Inverter

inverter = Inverter(<ip_address>)
response = inverter.<command>

if response:
    print(f"Inverter Response: {response}")
else:
    print("Unable to get response!")
```

#### Available functions
- `get_real_data_new()`: Retrieve real-time data
- `get_real_data_hms()`: Retrieve real-time data
- `get_real_data()`: Retrieve real-time data
- `get_config()`: Retrieve configuration information
- `network_info()`: Retrieve network information
- `app_information_data()`: Retrieve application information data
- `app_get_hist_power()`: Retrieve historical power data
- `set_power_limit(power_limit)`: Set the power limit of the inverter (0-100%)
- `set_wifi(wifi_ssid, wifi_password)`: Configure the wifi network
- `firmware_update()`: Update to latest firmware
- `restart`: Restart the inverter
- `turn_on`: Turn the inverter on
- `turn_off`: Turn the inverter off

## Note

Please be aware of the following considerations:

 - No DTU Implementation: This library
   retrieves information directly from the internal DTU of Hoymiles Wifi
   inverters.

## Caution

Use this library responsibly and be aware of potential risks. There are no guarantees provided, and any misuse or incorrect implementation may result in undesirable outcomes. Ensure that your inverter is not compromised during communication.

  
## Known Limitations

**Update Frequency:** The library may experience limitations in fetching updates, potentially around twice per minute. The inverter firmware may enforce a mandatory wait period of approximately 30 seconds between requests.

**Compatibility:** While developed for the HMS-800W-T2 inverter, compatibility with other inverters from the series is untested at the time of writing. Exercise caution and conduct thorough testing if using with different inverter models.

## Attribution

A special thank you for the inspiration and codebase to:
 - [DennisOSRM](https://github.com/DennisOSRM): [hms-mqtt-publisher](https://github.com/DennisOSRM/hms-mqtt-publisher)
 - [henkwiedig](https://github.com/henkwiedig): [Hoymiles-DTU-Proto](https://github.com/henkwiedig/Hoymiles-DTU-Proto)
