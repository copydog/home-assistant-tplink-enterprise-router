import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers import translation

from custom_components.tplink_enterprise_router.client import TPLinkEnterpriseRouterClient
from custom_components.tplink_enterprise_router.const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class EventMatcher:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, severities: list, type: str):
        self.hass = hass
        self.entry = entry
        self.severities = severities
        self.type = type
        self.translations = None

        pass

    async def process(self, event: Event) -> bool:
        if self.translations is None:
            self.translations = await translation.async_get_translations(
                self.hass,
                self.hass.config.language,
                "component",
                [DOMAIN],
            )

        if event.data.get('severity') not in self.severities:
            return False

        message = event.data.get('message')
        if not self.match(message):
            return False

        matched_object = self.parse(message)

        if matched_object is None:
            return False

        self._process(matched_object)

        return True

    def build_readable_message(self, data: dict) -> str:
        template = self.translations.get(f"component.tplink_enterprise_router.component.tplink_enterprise_router.event.{self.type}")

        if template is not None:
            return template.format_map(data)

        return ""

    def match(self, message: str) -> bool:
        raise NotImplementedError()

    def parse(self, event: str):
        raise NotImplementedError()

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
        self.hass.bus.fire(f"{DOMAIN}_syslog", final_data)

class WirelessClientRoamedEventMatcher(WirelessClientChangedEventMatcher):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(
            hass,
            entry,
            [7],
            "wireless_client_roamed"
        )

    def match(self, message: str) -> bool:
        return "成功漫游到AP" in message

    def parse(self, message: str):
        segments = message.split(" ")

        previous_ssid_groups = segments[13].replace(")", "(").split("(")
        current_ssid_groups = segments[16].replace(")", "(").split("(")

        return {
            "device": segments[3],
            "timestamp": f"{segments[5]} {segments[6]}",
            "client_mac": segments[11][:17],
            "previous_ap_name": segments[12].split("的")[0],
            "previous_ap_ssid": previous_ssid_groups[0],
            "previous_ap_frequency": previous_ssid_groups[1],
            "current_ap_name": segments[15].split("的")[0],
            "current_ap_ssid": current_ssid_groups[0],
            "current_ap_frequency": current_ssid_groups[1],
        }

class WirelessClientConnectedEventMatcher(WirelessClientChangedEventMatcher):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(
            hass,
            entry,
            [7],
            "wireless_client_connected"
        )

    def match(self, message: str) -> bool:
        return "成功连接到AP" in message

    def parse(self, message: str):
        segments = message.split(" ")

        ssid_groups = segments[15].split("(")

        return {
            "device": segments[3],
            "timestamp": f"{segments[5]} {segments[6]}",
            "client_mac": segments[11][:17],
            "ap_name": segments[12].replace("(IP", ""),
            "ap_ip": segments[11][:17].replace(";MAC", ""),
            "ap_mac": segments[14][:17],
            "ap_ssid": ssid_groups[0],
            "ap_frequency": ssid_groups[1].replace(").", ""),
        }

class WirelessClientDisconnectedEventMatcher(WirelessClientChangedEventMatcher):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(
            hass,
            entry,
            [7],
            "wireless_client_disconnected"
        )

    def match(self, message: str) -> bool:
        return "断开连接." in message

    def parse(self, message: str):
        segments = message.split(" ")

        return {
            "device": segments[3],
            "timestamp": f"{segments[5]} {segments[6]}",
            "client_mac": segments[11][:17]
        }


class SyslogTracker:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: TPLinkEnterpriseRouterClient):
        self.matchers = [
            WebLoginEventMatcher(hass, entry),
            WirelessClientRoamedEventMatcher(hass, entry),
            WirelessClientConnectedEventMatcher(hass, entry),
            WirelessClientDisconnectedEventMatcher(hass, entry),
        ]
        self.index_message = None
        self.last_received_time = None
        self.received_messages = []
        self.client = client

    async def handle(self, event):
        for matcher in self.matchers:
            process_ok = await matcher.process(event)
            if process_ok:
                break

    async def _initialize(self):
        json = await self.client.get_syslog(1)
        _messages = json.get("syslog", [])

        self.index_message = _messages[0].get("syslog_1", None) if len(_messages) > 0 else None

    async def check(self):
        if self.index_message is None:
            await self._initialize()

        json = await self.client.get_syslog(50)
        _messages = json.get("syslog", [])