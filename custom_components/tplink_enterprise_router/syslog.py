import logging
import re

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers import translation

from . import TPLinkEnterpriseRouterCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class EventMatcher:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, severities: list, regex: str, type: str):
        self.hass = hass
        self.entry = entry
        self.severities = severities
        self.regex = regex
        self.type = type
        self.translations = None

        pass

    async def process(self, event: Event) -> bool:
        if self.translations is None:
            self.translations = await translation.async_get_translations(
                self.hass,
                "zh-Hans",
                "component",
                [DOMAIN],
            )

        if event.data.get('severity') not in self.severities:
            return False

        matched_object = re.match(self.regex, event.data.get('message'))

        if matched_object is None:
            return False

        self._process(matched_object.groupdict())

        return True

    def build_readable_message(self, data: dict) -> str:
        template = self.translations.get(f"component.tplink_enterprise_router.component.tplink_enterprise_router.event.{self.type}")

        if template is not None:
            return template.format_map(data)

        return ""

    def _process(self, data) -> None:
        final_data = {
            **data,
            "type": self.type,
            "readable_message": self.build_readable_message(data)
        }
        self.hass.bus.fire(f"{DOMAIN}_{self.type}", final_data)
        self.hass.bus.fire(f"{DOMAIN}_syslog", final_data)

class WebLoginEventMatcher(EventMatcher):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(
            hass,
            entry,
            [5],
            r"\w{3}\s\d{1,2}\s[\d:]{6,8}\s(?P<device>.+)\sweb:\s(?P<timestamp>.+)\s<\d>\s:\s{1,2}(?P<username>.+)\(IP:(?P<ip>[\d\.]+)\)\s成功登录设备Web管理系统!",
            "web_login"
        )

    def _process(self, data) -> None:
        pass

class WirelessClientChangedEventMatcher(EventMatcher):
    def _process(self, data) -> None:
        super()._process(data)
        final_data = None
        if self.type == "wireless_client_roamed":
            final_data = {
                **data,
                "previous_status": "connected",
                "current_status": "connected",
                "type": self.type,
                "readable_message": self.build_readable_message(data)
            }
        elif self.type == "wireless_client_connected":
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
                "type": self.type,
                "readable_message": self.build_readable_message(data)
            }
        elif self.type == "wireless_client_disconnected":
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
                "type": self.type,
                "readable_message": self.build_readable_message(data)
            }
        self.hass.bus.fire(f"{DOMAIN}_wireless_client_changed", final_data)

class WirelessClientRoamedEventMatcher(WirelessClientChangedEventMatcher):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(
            hass,
            entry,
            [7],
            r"\w{3}\s\d{1,2}\s[\d:]{6,8}\s(?P<device>.+)\swstation:\s(?P<timestamp>.+)\s<\d>\s:\s{1,2}STA\(MAC\s(?P<client_mac>[\w-]+)\)从AP\s(?P<previous_ap_name>.+)的无线服务\s(?P<previous_ap_ssid>.+)\((?P<previous_ap_frequency>2\.4G|5G)\)\s成功漫游到AP\s(?P<current_ap_name>.+)的无线服务\s(?P<current_ap_ssid>.+)\((?P<current_ap_frequency>2\.4G|5G)\)",
            "wireless_client_roamed"
        )

class WirelessClientConnectedEventMatcher(WirelessClientChangedEventMatcher):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(
            hass,
            entry,
            [7],
                r"\w{3}\s\d{1,2}\s[\d:]{6,8}\s(?P<device>.+)\swstation:\s(?P<timestamp>.+)\s<\d>\s:\s{1,2}STA\(MAC\s(?P<client_mac>[\w-]+)\)成功连接到AP\s(?P<ap_name>.+)\(IP\s(?P<ap_ip>[\d\.]+);MAC\s(?P<ap_mac>[\w-]+)\)的无线服务\s(?P<ap_ssid>.+)\((?P<ap_frequency>2\.4G|5G)\).",
            "wireless_client_connected"
        )

class WirelessClientDisconnectedEventMatcher(WirelessClientChangedEventMatcher):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(
            hass,
            entry,
            [7],
            r"\w{3}\s\d{1,2}\s[\d:]{6,8}\s(?P<device>.+)\swstation:\s(?P<timestamp>.+)\s<\d>\s:\s{1,2}STA\(MAC\s(?P<client_mac>[\w-]+)\)断开连接.",
            "wireless_client_disconnected"
        )

class SyslogHandler:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.matchers = [
            WebLoginEventMatcher(hass, entry),
            WirelessClientRoamedEventMatcher(hass, entry),
            WirelessClientConnectedEventMatcher(hass, entry),
            WirelessClientDisconnectedEventMatcher(hass, entry),
        ]

    async def handle(self, event):
        for matcher in self.matchers:
            matched = await matcher.process(event)
            if matched:
                break
