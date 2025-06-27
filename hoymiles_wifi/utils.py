"""Utils for interacting with Hoymiles WiFi API."""

from hoymiles_wifi.hoymiles import (
    BMSWorkingMode,
    DateBean,
    DurationBean,
    TariffType,
    TimeBean,
    TimePeriodBean,
)
from hoymiles_wifi.protobuf import (
    GetConfig_pb2,
    SetConfig_pb2,
)


def initialize_set_config(get_config_req: GetConfig_pb2.GetConfigReqDTO):
    """Initialize set config response with get config request."""

    set_config_res = SetConfig_pb2.SetConfigResDTO()
    set_config_res.lock_password = get_config_req.lock_password
    set_config_res.lock_time = get_config_req.lock_time
    set_config_res.limit_power_mypower = get_config_req.limit_power_mypower
    set_config_res.zero_export_433_addr = get_config_req.zero_export_433_addr
    set_config_res.zero_export_enable = get_config_req.zero_export_enable
    set_config_res.netmode_select = get_config_req.netmode_select
    set_config_res.channel_select = get_config_req.channel_select
    set_config_res.server_send_time = get_config_req.server_send_time
    set_config_res.serverport = get_config_req.serverport
    set_config_res.apn_set = get_config_req.apn_set
    set_config_res.meter_kind = get_config_req.meter_kind
    set_config_res.meter_interface = get_config_req.meter_interface
    set_config_res.wifi_ssid = get_config_req.wifi_ssid
    set_config_res.wifi_password = get_config_req.wifi_password
    set_config_res.server_domain_name = get_config_req.server_domain_name
    set_config_res.inv_type = get_config_req.inv_type
    set_config_res.dtu_sn = get_config_req.dtu_sn
    set_config_res.access_model = get_config_req.access_model
    set_config_res.mac_0 = get_config_req.mac_0
    set_config_res.mac_1 = get_config_req.mac_1
    set_config_res.mac_2 = get_config_req.mac_2
    set_config_res.mac_3 = get_config_req.mac_3
    set_config_res.mac_4 = get_config_req.mac_4
    set_config_res.mac_5 = get_config_req.mac_5
    set_config_res.dhcp_switch = get_config_req.dhcp_switch
    set_config_res.ip_addr_0 = get_config_req.ip_addr_0
    set_config_res.ip_addr_1 = get_config_req.ip_addr_1
    set_config_res.ip_addr_2 = get_config_req.ip_addr_2
    set_config_res.ip_addr_3 = get_config_req.ip_addr_3
    set_config_res.subnet_mask_0 = get_config_req.subnet_mask_0
    set_config_res.subnet_mask_1 = get_config_req.subnet_mask_1
    set_config_res.subnet_mask_2 = get_config_req.subnet_mask_2
    set_config_res.subnet_mask_3 = get_config_req.subnet_mask_3
    set_config_res.default_gateway_0 = get_config_req.default_gateway_0
    set_config_res.default_gateway_1 = get_config_req.default_gateway_1
    set_config_res.default_gateway_2 = get_config_req.default_gateway_2
    set_config_res.default_gateway_3 = get_config_req.default_gateway_3
    set_config_res.apn_name = get_config_req.apn_name
    set_config_res.apn_password = get_config_req.apn_password
    set_config_res.sub1g_sweep_switch = get_config_req.sub1g_sweep_switch
    set_config_res.sub1g_work_channel = get_config_req.sub1g_work_channel
    set_config_res.cable_dns_0 = get_config_req.cable_dns_0
    set_config_res.cable_dns_1 = get_config_req.cable_dns_1
    set_config_res.cable_dns_2 = get_config_req.cable_dns_2
    set_config_res.cable_dns_3 = get_config_req.cable_dns_3
    set_config_res.dtu_ap_ssid = get_config_req.dtu_ap_ssid
    set_config_res.dtu_ap_pass = get_config_req.dtu_ap_pass

    return set_config_res


def prompt_user_for_bms_working_mode() -> BMSWorkingMode:
    """Prompt user for BMS working mode."""

    print("Please select the working mode:")  # noqa: T201
    print("1.) Self-consumption mode")  # noqa: T201
    print("2.) Economy mode")  # noqa: T201
    print("3.) Backup mode")  # noqa: T201
    print("4.) Off-grid mode")  # noqa: T201
    print("5.) Force charge mode")  # noqa: T201
    print("6.) Force discharge mode")  # noqa: T201
    print("7.) Peak shaving mode")  # noqa: T201
    print("8.) Time of use mode")  # noqa: T201

    return BMSWorkingMode(int(input("Working mode: (1-8): ")))


def promt_user_for_rate_time_range() -> TimeBean:
    """Prompt user for electricity rate time range."""

    time_bean = TimeBean()
    time_bean.durations = []
    user_input = input(
        "Enter the weekdays as numbers (Monday = 1, Sunday = 7), separated by commas (e.g., 1,3,5): "
    )
    time_bean.week = [
        int(day.strip()) for day in user_input.split(",") if day.strip().isdigit()
    ]

    print("")  # noqa: T201
    print("Configuring peak time...")  # noqa: T201
    duration_bean = prompt_user_for_tariff_details(TariffType.PEAK)
    time_bean.durations.append(duration_bean)
    print("")  # noqa: T201

    print("Configuring off-peak time...")  # noqa: T201
    duration_bean = prompt_user_for_tariff_details(TariffType.OFF_PEAK)
    time_bean.durations.append(duration_bean)
    print("")  # noqa: T201

    print("Configuring partial-peak time...")  # noqa: T201
    duration_bean = prompt_user_for_tariff_details(
        TariffType.PARTIAL_PEAK, include_time=False
    )
    time_bean.durations.append(duration_bean)
    print("")  # noqa: T201

    return time_bean


def prompt_user_for_tariff_details(
    tariff: TariffType, include_time: bool = True
) -> DurationBean:
    """Query duration for a given tariff type from user."""

    duration_bean = DurationBean()

    if include_time:
        duration_bean.start_time = input(
            "Please enter the start time (HH:MM): "
        ).strip()
        duration_bean.end_time = input("Please enter the end time (HH:MM): ").strip()

    duration_bean.in_price = float(
        input("Please enter the price for a kWh to buy (e.g. 0.12): ").strip()
    )
    duration_bean.out_price = float(
        input("Please enter the price for a kWh to sell (e.g. 0.05): ").strip()
    )
    duration_bean.type = tariff

    return duration_bean


def parse_time_settings_input(time_settings_str: str) -> list[DateBean]:
    """Parse the --time-settings CLI input into DateBean objects."""

    time_settings = []

    if not time_settings_str.strip():
        return time_settings

    entries = time_settings_str.strip().split("||")

    try:
        for entry in entries:
            date_part, rest = entry.split(":", 1)
            start_date, end_date = date_part.strip().split("-")

            time_ranges = rest.split(";")
            if len(time_ranges) != 2:
                raise ValueError(
                    "Each date block must contain exactly two time ranges separated by ';'."
                )

            parsed_time_ranges = []

            for time_range in time_ranges:
                week_part, durations_part = time_range.split("=")
                week = [
                    int(day.strip())
                    for day in week_part.split(",")
                    if day.strip().isdigit()
                ]

                duration_strs = durations_part.split(",")
                if len(duration_strs) != 3:
                    raise ValueError(
                        "Each time range must include exactly 3 tariff durations."
                    )

                durations = []
                for idx, duration_str in enumerate(duration_strs):
                    start, end, in_price, out_price = duration_str.strip().split("-")
                    durations.append(
                        DurationBean(
                            start_time=start.strip(),
                            end_time=end.strip(),
                            in_price=float(in_price),
                            out_price=float(out_price),
                            type=[
                                TariffType.PEAK,
                                TariffType.OFF_PEAK,
                                TariffType.PARTIAL_PEAK,
                            ][idx],
                        )
                    )

                parsed_time_ranges.append(TimeBean(durations=durations, week=week))

            time_settings.append(
                DateBean(
                    start_date=start_date.strip(),
                    end_date=end_date.strip(),
                    time=parsed_time_ranges,
                )
            )

    except Exception as e:
        raise ValueError(f"Invalid time-setting format in block '{entry}': {e}") from e

    return time_settings


def parse_time_periods_input(time_periods_str: str) -> list[TimePeriodBean]:
    """Parse --time-periods input into a list of TimePeriodBean objects."""

    time_periods = []

    if not time_periods_str.strip():
        return time_periods

    period_blocks = time_periods_str.strip().split("||")

    try:
        for block in period_blocks:
            charge_part, discharge_part = block.split("|")

            charge_time_from, charge_time_to, charge_power, max_soc = charge_part.split(
                "-"
            )
            discharge_time_from, discharge_time_to, discharge_power, min_soc = (
                discharge_part.split("-")
            )

            time_period = TimePeriodBean(
                charge_time_from=charge_time_from,
                charge_time_to=charge_time_to,
                charge_power=int(charge_power),
                max_soc=int(max_soc),
                discharge_time_from=discharge_time_from,
                discharge_time_to=discharge_time_to,
                discharge_power=int(discharge_power),
                min_soc=int(min_soc),
            )

            for value_name, value in {
                "charge_power": time_period.charge_power,
                "max_soc": time_period.max_soc,
                "discharge_power": time_period.discharge_power,
                "min_soc": time_period.min_soc,
            }.items():
                if not 0 <= value <= 100:
                    raise ValueError(f"{value_name} out of range: {value}")

            time_periods.append(time_period)

    except Exception as e:
        raise ValueError(f"Invalid time period format: '{block}' -> {e}") from e

    return time_periods
