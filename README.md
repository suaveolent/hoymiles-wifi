# hoymiles-wifi

This Python library facilitates communication with Hoymiles HMS microinverters, specifically targeting the HMS-XXXXW-T2 series. A special thank you to [DennisOSRM](https://github.com/DennisOSRM) for the inspiration and codebase from the [hms-mqtt-publisher](https://github.com/DennisOSRM/hms-mqtt-publisher) repository.

## Installation

```
$ pip install hoymiles-wifi
```

## Usage

You can integrate the library into your own project, or simply use it in the command line.

### Command line:

```
hoymiles-wifi <ip_address>
```

This will retrieve the current inverter state.

### Python code

```
from hoymiles_wifi.inverter import Inverter

inverter = Inverter(<ip_address>)
response = inverter.update_state()

if response:
    print(f"Inverter State: {response}")
else:
    print("Unable to retrieve inverter state")
```

## Note

Please be aware of the following considerations:

 - No DTU Implementation: Unlike the original tool, this library
   retrieves information directly from the internal DTU of Hoymiles
   inverters.

## Caution

Use this library responsibly and be aware of potential risks. There are no guarantees provided, and any misuse or incorrect implementation may result in undesirable outcomes. Ensure that your inverter is not compromised during communication.

  
## Known Limitations

**Update Frequency:** The library may experience limitations in fetching updates, potentially around twice per minute. The inverter firmware may enforce a mandatory wait period of approximately 30 seconds between requests.

**Compatibility:** While developed for the HMS-800W-T2 inverter, compatibility with other inverters from the series is untested at the time of writing. Exercise caution and conduct thorough testing if using with different inverter models.