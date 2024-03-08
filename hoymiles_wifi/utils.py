""""Utils for interacting with Hoymiles WiFi API."""

from hoymiles_wifi.protobuf import (
    GetConfig_pb2,
    SetConfig_pb2,
)

devInfo = [
    ([0x10, 0x10, 0x10, "ALL"], 300, "HM-300-1T"),
    ([0x10, 0x10, 0x20, "ALL"], 350, "HM-350-1T"),
    ([0x10, 0x10, 0x30, "ALL"], 400, "HM-400-1T"),
    ([0x10, 0x10, 0x40, "ALL"], 400, "HM-400-1T"),
    ([0x10, 0x11, 0x10, "ALL"], 600, "HM-600-2T"),
    ([0x10, 0x11, 0x20, "ALL"], 700, "HM-700-2T"),
    ([0x10, 0x11, 0x30, "ALL"], 800, "HM-800-2T"),
    ([0x10, 0x11, 0x40, "ALL"], 800, "HM-800-2T"),
    ([0x10, 0x12, 0x10, "ALL"], 1200, "HM-1200-4T"),
    ([0x10, 0x02, 0x30, "ALL"], 1500, "MI-1500-4T Gen3"),
    ([0x10, 0x12, 0x30, "ALL"], 1500, "HM-1500-4T"),
    ([0x10, 0x10, 0x10, 0x15], int(300 * 0.7), "HM-300-1T"),  # HM-300 factory limited to 70%

    ([0x10, 0x20, 0x11, "ALL"], 300, "HMS-300-1T"),  # 00
    ([0x10, 0x20, 0x21, "ALL"], 350, "HMS-350-1T"),  # 00
    ([0x10, 0x20, 0x41, "ALL"], 400, "HMS-400-1T"),  # 00
    ([0x10, 0x10, 0x51, "ALL"], 450, "HMS-450-1T"),  # 01
    ([0x10, 0x20, 0x51, "ALL"], 450, "HMS-450-1T"),  # 03
    ([0x10, 0x10, 0x71, "ALL"], 500, "HMS-500-1T"),  # 02
    ([0x10, 0x20, 0x71, "ALL"], 500, "HMS-500-1T v2"),  # 02
    ([0x10, 0x21, 0x11, "ALL"], 600, "HMS-600-2T"),  # 01
    ([0x10, 0x21, 0x41, "ALL"], 800, "HMS-800-2T"),  # 00
    ([0x10, 0x11, 0x51, "ALL"], 900, "HMS-900-2T"),  # 01
    ([0x10, 0x21, 0x51, "ALL"], 900, "HMS-900-2T"),  # 03
    ([0x10, 0x21, 0x71, "ALL"], 1000, "HMS-1000-2T"),  # 05
    ([0x10, 0x11, 0x71, "ALL"], 1000, "HMS-1000-2T"),  # 01
    ([0x10, 0x22, 0x41, "ALL"], 1600, "HMS-1600-4T"),  # 4
    ([0x10, 0x12, 0x51, "ALL"], 1800, "HMS-1800-4T"),  # 01
    ([0x10, 0x22, 0x51, "ALL"], 1800, "HMS-1800-4T"),  # 16
    ([0x10, 0x12, 0x71, "ALL"], 2000, "HMS-2000-4T"),  # 01
    ([0x10, 0x22, 0x71, "ALL"], 2000, "HMS-2000-4T"),  # 10

    ([0x10, 0x32, 0x41, "ALL"], 1600, "HMT-1600-4T"),  # 00
    ([0x10, 0x32, 0x51, "ALL"], 1800, "HMT-1800-4T"),  # 00
    ([0x10, 0x32, 0x71, "ALL"], 2000, "HMT-2000-4T"),  # 0

    ([0x10, 0x33, 0x11, "ALL"], 1800, "HMT-1800-6T"),  # 01
    ([0x10, 0x33, 0x31, "ALL"], 2250, "HMT-2250-6T")  # 01
]

def format_number(number) -> str:
    return "{:02d}".format(number)

def generate_version_string(version_number: int) -> str:
    version_string = format_number(version_number // 2048) + "." + format_number((version_number // 64) % 32) + "." + format_number(version_number % 64)
    return version_string

def generate_sw_version_string(version_number: int) -> str:

    version_number2 = version_number // 10000
    version_number3 = (version_number - (version_number2 * 10000)) // 100
    version_number4 = (version_number - (version_number2 * 10000)) - (version_number3 * 100)

    version_string = format_number(version_number2) + "." + format_number(version_number3) + "." + format_number(version_number4)
    return version_string


def generate_dtu_version_string(version_number: int, type: str = None) -> str:

    version_string = ""
    version_number2 = version_number % 256
    version_number3 = (version_number // 256) % 16

    if "SRF" == str:
        version_string += f"{format_number(version_number // 1048576)}.{format_number((version_number % 65536) // 4096)}.{format_number(version_number3)}.{format_number(version_number2)}"
    elif "HRF" == str:
        version_string += f"{format_number(version_number // 65536)}.{format_number((version_number % 65536) // 4096)}.{format_number(version_number3)}.{format_number(version_number2)}"
    else:
        version_string += f"{format_number(version_number // 4096)}.{format_number(version_number3)}.{format_number(version_number2)}"

    return version_string

def generate_inverter_serial_number(serial_number: int) -> str:
    return hex(serial_number)[2:]


def initialize_set_config(get_config_req: GetConfig_pb2.GetConfigReqDTO):
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


ALL = 0xff

dev_info = [
    ([0x10, 0x10, 0x10, ALL], 300, "HM-300-1T"),
    ([0x10, 0x10, 0x20, ALL], 350, "HM-350-1T"),
    ([0x10, 0x10, 0x30, ALL], 400, "HM-400-1T"),
    ([0x10, 0x10, 0x40, ALL], 400, "HM-400-1T"),
    ([0x10, 0x11, 0x10, ALL], 600, "HM-600-2T"),
    ([0x10, 0x11, 0x20, ALL], 700, "HM-700-2T"),
    ([0x10, 0x11, 0x30, ALL], 800, "HM-800-2T"),
    ([0x10, 0x11, 0x40, ALL], 800, "HM-800-2T"),
    ([0x10, 0x12, 0x10, ALL], 1200, "HM-1200-4T"),
    ([0x10, 0x02, 0x30, ALL], 1500, "MI-1500-4T Gen3"),
    ([0x10, 0x12, 0x30, ALL], 1500, "HM-1500-4T"),
    ([0x10, 0x10, 0x10, 0x15], int(300 * 0.7), "HM-300-1T"),  # HM-300 factory limited to 70%

    ([0x10, 0x20, 0x11, ALL], 300, "HMS-300-1T"),  # 00
    ([0x10, 0x20, 0x21, ALL], 350, "HMS-350-1T"),  # 00
    ([0x10, 0x20, 0x41, ALL], 400, "HMS-400-1T"),  # 00
    ([0x10, 0x10, 0x51, ALL], 450, "HMS-450-1T"),  # 01
    ([0x10, 0x20, 0x51, ALL], 450, "HMS-450-1T"),  # 03
    ([0x10, 0x10, 0x71, ALL], 500, "HMS-500-1T"),  # 02
    ([0x10, 0x20, 0x71, ALL], 500, "HMS-500-1T v2"),  # 02
    ([0x10, 0x21, 0x11, ALL], 600, "HMS-600-2T"),  # 01
    ([0x10, 0x21, 0x41, ALL], 800, "HMS-800-2T"),  # 00
    ([0x10, 0x11, 0x51, ALL], 900, "HMS-900-2T"),  # 01
    ([0x10, 0x21, 0x51, ALL], 900, "HMS-900-2T"),  # 03
    ([0x10, 0x21, 0x71, ALL], 1000, "HMS-1000-2T"),  # 05
    ([0x10, 0x11, 0x71, ALL], 1000, "HMS-1000-2T"),  # 01
    ([0x10, 0x22, 0x41, ALL], 1600, "HMS-1600-4T"),  # 4
    ([0x10, 0x12, 0x51, ALL], 1800, "HMS-1800-4T"),  # 01
    ([0x10, 0x22, 0x51, ALL], 1800, "HMS-1800-4T"),  # 16
    ([0x10, 0x12, 0x71, ALL], 2000, "HMS-2000-4T"),  # 01
    ([0x10, 0x22, 0x71, ALL], 2000, "HMS-2000-4T"),  # 10

    ([0x10, 0x32, 0x41, ALL], 1600, "HMT-1600-4T"),  # 00
    ([0x10, 0x32, 0x51, ALL], 1800, "HMT-1800-4T"),  # 00
    ([0x10, 0x32, 0x71, ALL], 2000, "HMT-2000-4T"),  # 0

    ([0x10, 0x33, 0x11, ALL], 1800, "HMT-1800-6T"),  # 01
    ([0x10, 0x33, 0x31, ALL], 2250, "HMT-2250-6T")  # 01
]


def convert_serial_to_hex(serial_number: str):
    # Convert the serial number from string to int and then to hex
    return [int(serial_number[i:i + 2], 16) for i in range(0, len(serial_number), 2)]

def get_dev_idx(serial_number: str):
    ret = 0xff
    pos = 0

    # Convert serial number to hex
    serial_hex = convert_serial_to_hex(serial_number)

    print(serial_hex)

    # Check for all 4 bytes first
    for pos in range(len(dev_info)):
        if dev_info[pos][0] == serial_hex:
            ret = pos
            break

    # Then only for 3 bytes but only if not already found
    if ret == 0xff:
        for pos in range(len(dev_info)):
            if dev_info[pos][0][:3] == serial_hex[:3]:
                ret = pos
                break

    return ret

def get_hw_model_name(serial_number: str):
    # Convert serial number to hex
    idx = get_dev_idx(serial_number)
    if idx == 0xff:
        return ""
    return dev_info[idx][2]

