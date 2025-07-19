import logging
from urllib.parse import unquote

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers import translation

from custom_components.tplink_enterprise_router.client import TPLinkEnterpriseRouterClient
from custom_components.tplink_enterprise_router.const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class EventMatcher:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, severities: list, _type: str):
        self.hass = hass
        self.entry = entry
        self.severities = severities
        self.type = _type
        self.translations = None

        pass

    async def process(self, event: dict) -> bool:
        if self.translations is None:
            self.translations = await translation.async_get_translations(
                self.hass,
                self.hass.config.language,
                "component",
                [DOMAIN],
            )

        if event['severity'] not in self.severities:
            return False

        message = event['message']
        if not self.match(message):
            return False

        matched_object = self.parse(event)

        if matched_object is None:
            return False

        self._process(matched_object)

        return True

    def build_readable_message(self, data: dict) -> str:
        template = self.translations.get(
            f"component.tplink_enterprise_router.component.tplink_enterprise_router.event.{self.type}")

        if template is not None:
            return template.format_map(data)

        return ""

    def match(self, message: str) -> bool:
        raise NotImplementedError()

    def parse(self, event: dict):
        raise NotImplementedError()

    def _process(self, data) -> None:
        final_data = {
            **data,
            "type": self.type,
        }
        self.hass.bus.fire(f"{DOMAIN}_{self.type}", final_data)
        self.hass.bus.fire(f"{DOMAIN}_syslog", final_data)


class WebLoginEventMatcher(EventMatcher):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(
            hass,
            entry,
            [3, 5],
            "web_login"
        )

    def _process(self, data) -> None:
        """ skip home assistant login """
        if self.hass.data[DOMAIN][self.entry.entry_id].status['local_ip'] == data['ip']:
            return

        super()._process(data)

    def match(self, message: str) -> bool:
        return "成功登录设备Web管理系统" in message

    def parse(self, event: dict):
        segments = event['message'].split(" ")
        _seg = segments[0].replace("(IP:", " ").replace(")", "").split(" ")

        return {
            "source_ip": event['source_ip'],
            "timestamp": event['timestamp'],
            "ip": _seg[1],
            "username": _seg[0],
        }


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
            }
        elif self.type == "wireless_client_connected":
            final_data = {
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
            }
        elif self.type == "wireless_client_disconnected":
            final_data = {
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
            }
        self.hass.bus.fire(f"{DOMAIN}_wireless_client_changed", final_data)
        self.hass.bus.fire(f"{DOMAIN}_syslog", {
            **final_data,
            "type": "wireless_client_changed",
        })


class WirelessClientRoamedEventMatcher(WirelessClientChangedEventMatcher):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(
            hass,
            entry,
            [1, 7],
            "wireless_client_roamed"
        )

    def match(self, message: str) -> bool:
        return "成功漫游到AP" in message

    def parse(self, event: dict):
        segments = event['message'].split(" ")

        previous_ssid_groups = segments[3].replace(")", "(").split("(")
        current_ssid_groups = segments[6].replace(")", "(").split("(")

        return {
            "source_ip": event['source_ip'],
            "timestamp": event['timestamp'],
            "client_mac": segments[1][:17],
            "previous_ap_name": segments[2].split("的")[0],
            "previous_ap_ssid": previous_ssid_groups[0],
            "previous_ap_frequency": previous_ssid_groups[1],
            "current_ap_name": segments[5].split("的")[0],
            "current_ap_ssid": current_ssid_groups[0],
            "current_ap_frequency": current_ssid_groups[1],
        }


class WirelessClientConnectedEventMatcher(WirelessClientChangedEventMatcher):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(
            hass,
            entry,
            [1, 7],
            "wireless_client_connected"
        )

    def match(self, message: str) -> bool:
        return "成功连接到AP" in message

    def parse(self, event: dict):
        segments = event['message'].split(" ")

        ssid_groups = segments[5].split("(")

        return {
            "source_ip": event['source_ip'],
            "timestamp": event['timestamp'],
            "client_mac": segments[1][:17],
            "ap_name": segments[2].replace("(IP", ""),
            "ap_ip": segments[3][:17].replace(";MAC", ""),
            "ap_mac": segments[4][:17],
            "ap_ssid": ssid_groups[0],
            "ap_frequency": ssid_groups[1].replace(").", ""),
        }


class WirelessClientDisconnectedEventMatcher(WirelessClientChangedEventMatcher):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(
            hass,
            entry,
            [1, 7],
            "wireless_client_disconnected"
        )

    def match(self, message: str) -> bool:
        return "断开连接." in message

    def parse(self, event: dict):
        segments = event['message'].split(" ")

        return {
            "source_ip": event['source_ip'],
            "timestamp": event['timestamp'],
            "client_mac": segments[1][:17]
        }


class DHCPIpAssignedEventMatcher(EventMatcher):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(
            hass, entry,
            [3],
            "dhcp_ip_assigned"
        )

    def match(self, message: str) -> bool:
        return "分配了IP地址" in message

    def parse(self, event: dict):
        segments = event['message'].split(" ")

        return {
            "source_ip": event['source_ip'],
            "timestamp": event['timestamp'],
            "client_mac": segments[1],
            "ip": segments[2].replace("分配了IP地址", ""),
        }


class SyslogTracker:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: TPLinkEnterpriseRouterClient):
        self.matchers = [
            WebLoginEventMatcher(hass, entry),
            DHCPIpAssignedEventMatcher(hass, entry),
            WirelessClientRoamedEventMatcher(hass, entry),
            WirelessClientConnectedEventMatcher(hass, entry),
            WirelessClientDisconnectedEventMatcher(hass, entry),
        ]
        self.tracking_dict = {}
        self.client = client
        self.first_poll = True
        self.last_log = None
        self.source_ip = client.host.replace("http://", "").replace("https://", "")

    async def handle(self, event):
        event_data = SyslogTracker.get_event_data(event)
        """ Skip old log """
        if SyslogTracker.should_track(event):
            key = SyslogTracker.get_track_key(event_data)
            old_tracking_data = self.tracking_dict.get(key)

            if old_tracking_data is not None and old_tracking_data['timestamp'] >= event_data['timestamp']:
                return

            self.tracking_dict[key] = event_data

        if self.first_poll:
            return

        for matcher in self.matchers:
            process_ok = await matcher.process(event_data)
            if process_ok:
                break

    async def poll(self):
        json = await self.client.get_syslog(50)
        _messages = [list(d.values())[0] for d in json.get("syslog", [])]

        for message in _messages:
            if self.last_log is not None and message == self.last_log:
                break

            severity = int(message[1:2])
            await self.handle(
                Event(
                    '',
                    {
                        "message": unquote(message),
                        "severity": severity,
                        "source_ip": self.source_ip
                    }
                )
            )

        self.last_log = _messages[0] if len(_messages) > 0 else self.last_log

        if self.first_poll:
            self.first_poll = False

    @staticmethod
    def should_track(event) -> bool:
        message = event.data.get("message")
        return "[WSTATION]" in message or "wstation:" in message

    @staticmethod
    def get_track_key(event_data: dict):
        message = event_data['message']
        segments = message.split(" ")

        # TODO: use scope
        if "断开连接." in message:
            return segments[1][:17]
        elif "成功连接到AP" in message:
            return segments[1][:17]
        elif "成功漫游到AP" in message:
            return segments[1][:17],
        else:
            return ""

    @staticmethod
    def get_event_data(event) -> dict:
        message = event.data.get("message")
        if message.startswith("<"):
            timestamp = message[3:22]
            scope = message[23:].split("]")[0]
            message = message.split(f"[{scope}]", 1)[1]

            return {
                "message": message,
                "source_ip": event.data.get("source_ip"),
                "severity": event.data.get("severity"),
                "timestamp": timestamp,
            }
        else:
            segments = message.split(" ", 7)
            timestamp = f"{segments[5]} {segments[6]}"
            message = message.split("> : ", 1)[1].strip()

            return {
                "message": message,
                "source_ip": event.data.get("source_ip"),
                "severity": event.data.get("severity"),
                "timestamp": timestamp,
            }
