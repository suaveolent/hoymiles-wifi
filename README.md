# hoymiles-wifi

This Python library facilitates communication with Hoymiles DTUs, the HMS-XXXXW microinverters, and hybrid inverters, utilizing protobuf messages.

For the Home Assistant integration have a look here:
https://github.com/suaveolent/ha-hoymiles-wifi

> [!NOTE]
> Disclaimer: This library is not affiliated with Hoymiles. It is an independent project developed to provide tools for interacting with Hoymiles DTUs and Hoymiles HMS-XXXXW series micro-inverters featuring integrated WiFi DTU. Any trademarks or product names mentioned are the property of their respective owners.

## Supported Devices

The library was successfully tested with:

- Hoymiles HMS-400W-1T
- Hoymiles HMS-800W-2T
- Hoymiles HMS-2000DW-4T
- Hoymiles DTU-WLite
- Hoymiles DTU-Pro (S)
- Hoymiles HYS-4.6LV-EUG1
- Hoymiles HYT-5.0HV-EUG1
- Solenso H-1000 (not tested for command, only to get data)
- Solenso DTU_SLS (not tested for command, only to get data)

## Installation

```
$ pip install hoymiles-wifi
```

## Usage

You can integrate the library into your own project, or simply use it in the command line.

### Command line:

```
hoymiles-wifi --host HOST <command> [additional-arguments]
```

| Command                         | Device Class                           | Description                                                      |
| ------------------------------- | -------------------------------------- | ---------------------------------------------------------------- |
| get-real-data-new               | DTU and W-series                       | Retrieve real-time data                                          |
| get-real-data                   | DTU and W-series                       | Retrieve real-time data                                          |
| get-config                      | DTU and W-series                       | Retrieve configuration information                               |
| network-info                    | DTU and W-series                       | Retrieve network information                                     |
| app-information-data            | DTU and W-series                       | Retrieve application information data                            |
| app-get-hist-power              | DTU and W-series                       | Retrieve historical power data                                   |
| set-power-limit                 | DTU and W-series                       | Set the power limit of the inverter (0-100%)                     |
| set-wifi                        | DTU and W-series                       | Configure the WiFi network                                       |
| firmware-update                 | DTU and W-series                       | Update to latest firmware                                        |
| restart-dtu                     | DTU and W-series                       | Restart the DTU                                                  |
| turn-on-inverter                | DTU and W-series                       | Turn the inverter on                                             |
| turn-off-inverter               | DTU and W-series                       | Turn the inverter off                                            |
| get-information-data            | DTU and W-series                       | Retrieve information data                                        |
| get-version-info                | DTU and W-series                       | Retrieve version information                                     |
| heartbeat                       | DTU and W-series                       | Request a heartbeat message from the DTU                         |
| identify-dtu                    | DTU and W-series                       | Identify the DTU                                                 |
| identify-inverters              | DTU and W-series                       | Identify connected inverters                                     |
| identify-meters                 | DTU and W-series                       | Identify connected meters                                        |
| get-alarm-list                  | DTU and W-series                       | Get alarm list from the DTU                                      |
| enable-performance-data-mode    | DTU and W-series                       | _Experimental_: Enable higher update interval mode (30s or less) |
| get-gateway-info                | HAT / HYT / HAS / HYS battery inverter | Get gateway information for hybrid-inverters                     |
| get-gateway-network-info        | HAT / HYT / HAS / HYS battery inverter | Get network information for hybrid-inverters                     |
| get-energy-storage-registry     | HAT / HYT / HAS / HYS battery inverter | Get information about the hybrid-inverter                        |
| get-energy-storage-data         | HAT / HYT / HAS / HYS battery inverter | Get live data of the hybrid-inverter                             |
| set-energy-storage-working-mode | HAT / HYT / HAS / HYS battery inverter | Set the working mode of the hybrid-inverter                      |

### CLI Arguments

The following arguments are available when using the CLI:

| Argument                | Type | Description                                                                                                                             |
| ----------------------- | ---- | --------------------------------------------------------------------------------------------------------------------------------------- | --------- | ----------- |
| `--host`                | str  | IP address or hostname of the DTU (required)                                                                                            |
| `--local_addr`          | str  | IP address of the interface to bind to (optional)                                                                                       |
| `--as-json`             | flag | Format output as JSON                                                                                                                   |
| `--disable-interactive` | flag | Disables interactive prompts                                                                                                            |
| `--power-limit`         | int  | Power limit to set (0–100)                                                                                                              |
| `--bms_working_mode`    | int  | BMS mode: 1=SELF_USE, 2=ECONOMIC, 3=BACKUP_POWER, 4=PURE_OFF_GRID, 5=FORCED_CHARGING, 6=FORCED_DISCHARGE, 7=PEAK_SHAVING, 8=TIME_OF_USE |
| `--rev-soc`             | int  | Reserved SOC to set (0–100)                                                                                                             |
| `--max-power`           | int  | Max (dis)charging power to set (0–100)                                                                                                  |
| `--peak-soc`            | int  | Peak SOC to set (0–100)                                                                                                                 |
| `--peak-meter-power`    | int  | Peak meter power to set (0–100)                                                                                                         |
| `--time-settings`       | str  | Economic mode config: `START-END:WEEKDAYS=DURATION,DURATION,DURATION, ...`                                                              |
| `--time-periods`        | str  | Time of use config: `CHARGE                                                                                                             | DISCHARGE | ...` format |

## 🔧 BMS Working Modes & Required Parameters

For `set-energy-storage-working-mode` different CLI parameters must be provided depending on the selected BMS working mode. Below is an overview:

| Working Mode       | Required Parameters                             |
| ------------------ | ----------------------------------------------- |
| `SELF_USE`         | `--rev-soc`                                     |
| `ECONOMIC`         | `--rev-soc`, `--time-settings`                  |
| `BACKUP_POWER`     | `--rev-soc`                                     |
| `PURE_OFF_GRID`    | `--rev-soc`                                     |
| `FORCED_CHARGING`  | `--rev-soc`, `--max-power`                      |
| `FORCED_DISCHARGE` | `--rev-soc`, `--max-power`                      |
| `PEAK_SHAVING`     | `--rev-soc`, `--peak-soc`, `--peak-meter-power` |
| `TIME_OF_USE`      | `--rev-soc`, `--time-periods`                   |

---

#### ⏱️ `--time-settings` (Economic working mode)

```
START-END:WEEKDAYS=PEAK_START-PEAK_END-PEAK_IN-PEAK_OUT,OFF_START-OFF_END-OFF_IN-OFF_OUT,PARTIAL_START-PARTIAL_END-PARTIAL_IN-PARTIAL_OUT;WEEKDAYS=...||START-END:...||...
```

- `START`, `END`: Date in `DD.MM`
- For each date range, **exactly two time ranges** must be configured
- Each time range includes:
  - `WEEKDAYS`: Comma-separated days (`1=Mon`, ..., `7=Sun`)
  - 3 tariff blocks: `PEAK`, `OFF_PEAK`, `PARTIAL_PEAK`
- Each block format: `START-END-IN_PRICE-OUT_PRICE`
- Use `;` to separate **Time Range 1** and **Time Range 2**
- Use `||` to separate multiple date ranges

#### Example

```
01.01-31.03:1,2,3=06:00-10:00-0.20-0.10,00:00-06:00-0.10-0.05,10:00-18:00-0.15-0.08;4,5=07:00-11:00-0.22-0.11,00:00-07:00-0.08-0.04,11:00-17:00-0.14-0.07
```

| Field            | Value         | Description                |
| ---------------- | ------------- | -------------------------- |
| Start Date       | `01.01`       | Start of date range        |
| End Date         | `31.03`       | End of date range          |
| **Time Range 1** |               |                            |
| Weekdays         | `1,2,3`       | Monday, Tuesday, Wednesday |
| PEAK             | `06:00-10:00` | Buy: `0.20`, Sell: `0.10`  |
| OFF_PEAK         | `00:00-06:00` | Buy: `0.10`, Sell: `0.05`  |
| PARTIAL_PEAK     | `10:00-18:00` | Buy: `0.15`, Sell: `0.08`  |
| **Time Range 2** |               |                            |
| Weekdays         | `4,5`         | Thursday, Friday           |
| PEAK             | `07:00-11:00` | Buy: `0.22`, Sell: `0.11`  |
| OFF_PEAK         | `00:00-07:00` | Buy: `0.08`, Sell: `0.04`  |
| PARTIAL_PEAK     | `11:00-17:00` | Buy: `0.14`, Sell: `0.07`  |

##### `--time-periods` (Time of use mode)

```
CHARGE_FROM-CHARGE_TO-CHARGE_PWR-MAX_SOC|DISCHARGE_FROM-DISCHARGE_TO-DISCHARGE_PWR-MIN_SOC||...
```

- All values are required
- Use `||` to separate multiple time periods
- Power and SOC values must be `0–100`

###### Example

```
06:00-08:00-50-90|18:00-20:00-40-20
```

| Field             | Value         | Description               |
| ----------------- | ------------- | ------------------------- |
| Charge From–To    | `06:00-08:00` | Charging window           |
| Charge Power      | `50`          | % power used to charge    |
| Max SOC           | `90`          | Max state of charge (%)   |
| Discharge From–To | `18:00-20:00` | Discharging window        |
| Discharge Power   | `40`          | % power used to discharge |
| Min SOC           | `20`          | Min state of charge (%)   |

### Python code

```python
from hoymiles_wifi.dtu import DTU
...
dtu = DTU(<ip_address>)
response = await dtu.<command>

if response:
    print(f"DTU Response: {response}")
else:
    print("Unable to get response!")
```

#### Available functions

- `async_get_real_data_new()`: Retrieve real-time data
- `async_get_real_data()`: Retrieve real-time data
- `async_get_config()`: Retrieve configuration information
- `async_network_info()`: Retrieve network information
- `async_app_information_data()`: Retrieve application information data
- `async_app_get_hist_power()`: Retrieve historical power data
- `async_set_power_limit(power_limit)`: Set the power limit of the inverter (0-100%)
- `async_set_wifi(wifi_ssid, wifi_password)`: Configure the wifi network
- `async_firmware_update()`: Update to latest firmware
- `async_restart_dtu()`: Restart the DTU
- `async_turn_on_inverter()`: Turn the inverter on
- `async_turn_off_inverter()`: Turn the inverter off
- `async_get_information_data()`: Retrieve information data
- `async_heartbeat()`: Request a heartbeat message from the DTU
- `async_get_alarm_list()`: Get alarm list from the DTU
- `async_enable_performance_data_mode()`: _Experimental_: Enable higher update interval mode (30s or less)
- `async_get_gateway_info()`: Get gateway information for hybrid-inverters
- `async_get_gateway_network_info()` : Get network information for hybrid-inverters
- `async_get_energy_storage_registry()`: Get information about the hybrid-inverter
- `async_get_energy_storage_data()`: Get live data of the hybrid-inverter
- `async_set_energy_storage_working_mode()`: Set the working mode of the hybrid-inverter

## Note

Please be aware:

> [!NOTE]
> No DTU Implementation: This library retrieves information directly from the (internal) DTU of Hoymiles Wifi inverters.

## Caution

Use this library responsibly and be aware of potential risks. There are no guarantees provided, and any misuse or incorrect implementation may result in undesirable outcomes. Ensure that your inverter is not compromised during communication.

## Known Limitations

### Update Frequency:

> [!NOTE]
> The library may encounter limitations in fetching updates, restricting updates to approximately twice per minute.
> This issue can be identified when the data returned matches the response from the previous request.
> If you encounter this, you have three options:
>
> 1. Set the update interval to 35 seconds or longer between requests.
> 2. Use `async_enable_performance_data_mode()`
> 3. Open the S-Miles Installer App, connect to the DTU, and access the Toolkit (which sends the same data as option 2).
>
> Options 2 and 3 need to be repeated whenever the DTU restarts.

> [!IMPORTANT]
> Setting the update interval below approximately 32 seconds may disable Hoymiles cloud functionality. To ensure proper communication with Hoymiles servers, keep the update interval at or above this threshold.

> [!CAUTION]
> Setting the update interval to 1–2 seconds could also cause disruptions in the App's connection.

### Compatibility:

> [!IMPORTANT]
> While developed for the HMS-800W-2T inverter, compatibility with other inverters from the series is untested at the time of writing. Exercise caution and conduct thorough testing if using with different inverter models.

## Attribution

A special thank you for the inspiration and codebase to:

- [DennisOSRM](https://github.com/DennisOSRM): [hms-mqtt-publisher](https://github.com/DennisOSRM/hms-mqtt-publisher)
- [henkwiedig](https://github.com/henkwiedig): [Hoymiles-DTU-Proto](https://github.com/henkwiedig/Hoymiles-DTU-Proto)
