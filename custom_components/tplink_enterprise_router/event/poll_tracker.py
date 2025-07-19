import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers import translation

from custom_components.tplink_enterprise_router.const import (DOMAIN)

_LOGGER = logging.getLogger(__name__)


class PollTracker:
    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self.hosts = {}
        self.first_load = True
        self.translations = None

    async def handle(self, data, start_time):
        hosts = data['wireless_hosts']
        device = data['device_info']['model']
        if self.translations is None:
            self.translations = await translation.async_get_translations(
                self.hass,
                self.hass.config.language,
                "component",
                [DOMAIN],
            )

        if self.first_load:
            self.first_load = False
            self.hosts = {item["mac"]: item for item in hosts}
            return

        """ Update hosts immediately """
        old_hosts = self.hosts
        new_hosts = {item["mac"]: item for item in hosts}
        self.hosts = new_hosts

        compare = self.compare_dict_lists(old_hosts, new_hosts, compare_fields=("ap_name", "ssid", "freq_name"))

        if len(compare['added']) > 0:
            for data in compare['added']:
                final_data = {
                    "device": device,
                    "timestamp": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "client_mac": data['mac'],
                    "ap_name": data['ap_name'],
                    "ap_ip": "",
                    "ap_mac": "",
                    "ap_ssid": data['ssid'],
                    "ap_frequency": data['freq_name'].replace("Hz", ""),
                    "type": "wireless_client_connected",
                    "readable_message": ""
                }
                self.hass.bus.fire(f"{DOMAIN}_wireless_client_connected", final_data)
                self.hass.bus.fire(f"{DOMAIN}_syslog", final_data)
                self.fire_wireless_client_changed(final_data)
        if len(compare['removed']) > 0:
            for data in compare['removed']:
                final_data = {
                    "device": device,
                    "timestamp": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "client_mac": data['mac'],
                    "type": "wireless_client_disconnected",
                    "readable_message": ""
                }
                self.hass.bus.fire(f"{DOMAIN}_wireless_client_disconnected", final_data)
                self.hass.bus.fire(f"{DOMAIN}_syslog", final_data)
                self.fire_wireless_client_changed(final_data)
        if len(compare['changed']) > 0:
            for data in compare['changed']:
                final_data = {
                    "device": device,
                    "timestamp": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "client_mac": data['new']['mac'],
                    "previous_ap_name": data["old"]['ap_name'],
                    "previous_ap_ssid": data["old"]['ssid'],
                    "previous_ap_frequency": data["old"]['freq_name'].replace("Hz", ""),
                    "current_ap_name": data["new"]['ap_name'],
                    "current_ap_ssid": data["new"]['ssid'],
                    "current_ap_frequency": data["new"]['freq_name'],
                    "type": "wireless_client_roamed",
                    "readable_message": ""
                }

                self.hass.bus.fire(f"{DOMAIN}_wireless_client_roamed", final_data)
                self.hass.bus.fire(f"{DOMAIN}_syslog", final_data)
                self.fire_wireless_client_changed(final_data)

    def fire_wireless_client_changed(self, data) -> None:
        final_data = None
        if data['type'] == "wireless_client_roamed":
            final_data = {
                **data,
                "previous_status": "connected",
                "current_status": "connected",
                "type": data['type'],
                "readable_message": ""
            }
        elif data['type'] == "wireless_client_connected":
            final_data = {
                "device": data['device'],
                "timestamp": data['timestamp'],
                "client_mac": data['client_mac'],
                "previous_ap_name": "",
                "previous_ap_ssid": "",
                "previous_ap_frequency": "",
                "previous_status": "disconnected",
                "current_ap_name": data['ap_name'],
                "current_ap_ssid": data['ap_ssid'],
                "current_ap_frequency": data['ap_frequency'],
                "current_status": "connected",
                "type": data['type'],
                "readable_message": ""
            }
        elif data['type'] == "wireless_client_disconnected":
            final_data = {
                "device": data['device'],
                "timestamp": data['timestamp'],
                "client_mac": data['client_mac'],
                "previous_ap_name": "",
                "previous_ap_ssid": "",
                "previous_ap_frequency": "",
                "previous_status": "connected",
                "current_ap_name": "",
                "current_ap_ssid": "",
                "current_ap_frequency": "",
                "current_status": "disconnected",
                "type": data['type'],
                "readable_message": ""
            }
        self.hass.bus.fire(f"{DOMAIN}_wireless_client_changed", final_data)
        self.hass.bus.fire(f"{DOMAIN}_syslog", final_data)

    def compare_dict_lists(self, dict1_map, dict2_map, compare_fields=()):
        keys_list1 = set(dict1_map.keys())
        keys_list2 = set(dict2_map.keys())

        added = [dict2_map[key] for key in keys_list2 - keys_list1]
        removed = [dict1_map[key] for key in keys_list1 - keys_list2]

        changed = []
        for key in keys_list1 & keys_list2:
            dict1 = dict1_map[key]
            dict2 = dict2_map[key]
            differences = {
                field: (dict1.get(field), dict2.get(field))
                for field in compare_fields
                if dict1.get(field) != dict2.get(field)
            }
            if differences:
                changed.append({"old": dict1, "new": dict2, "diff": differences})

        return {"added": added, "removed": removed, "changed": changed}
