"""Utils for interacting with Hoymiles WiFi API."""

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
