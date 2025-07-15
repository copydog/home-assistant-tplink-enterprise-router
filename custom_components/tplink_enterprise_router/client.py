import logging
from urllib.parse import unquote

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)


class TPLinkEnterpriseRouterClient:
    def __init__(self, hass, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.token = None
        self._session = async_get_clientsession(hass)

    async def authenticate(self) -> None:
        json = await self.request(
            {"method": "do", "login": {"username": self.username, "password": self.password}},
            self.host
        )

        if json['error_code'] != 0:
            raise HomeAssistantError(f"Invalid Credential")

        self.token = json['stok']

    async def logout(self):
        await self.request({"method": "do", "system": {"logout": None}})

    async def reboot(self):
        await self.request({"method": "do", "system": {"reboot": None}})

    async def set_ap_light(self, status: str):
        await self.request({"method": "set", "apmng_set": {"ap_led_global_switch": {"led_switch": status}}})

    async def get_wan(self):
        json = await self.request({"method": "get", "port": {"table": "port_status", "filter": [{"port_type": "WAN"}]}})

    async def get_status(self):
        json = await self.request({
            "method": "get",
            "host_management": {
                "name": "host_count_info",
                "table": "host_info"
            },
            "system": {
                "name": [
                    "cpu_usage",
                    "mem_usage",
                    "device_info"
                ]
            },
            "online_check": {
                "table": "state",
                "name": "state"
            },
            "apmng_status": {
                "name": "apmng_status"
            },
        })

        host_count_info = json['host_management']['host_count_info']
        cpu_usage = json['system']['cpu_usage']
        cpu_used = int(
            (int(cpu_usage['core1']) + int(cpu_usage['core2']) + int(cpu_usage['core3']) + int(cpu_usage['core4'])) / 4)

        """ Calculate Wan Status """
        state_dict = json.get("online_check", {}).get("state", {})
        wan_state = None
        ssid_host_count = [{"ssid": key, "count": value} for key, value in host_count_info['ssid_host_count'].items()]

        for state_key in state_dict:
            state_info = state_dict[state_key]
            if isinstance(state_info, dict) and state_info.get("if") == "WAN":
                wan_state = state_info.get("state")
                break

        """ Calculate Hosts """
        hosts = json['host_management']['host_info']
        clean_hosts = [list(item.values())[0] for item in hosts]
        for item in clean_hosts:
            ap_name = item.get("ap_name")
            connect_date = item.get("connect_date")
            connect_time = item.get("connect_time")
            ssid = item.get("ssid")
            item["ap_name"] = unquote(ap_name) if ap_name is not None else ""
            item["connect_date"] = unquote(connect_date) if connect_date is not None else ""
            item["connect_time"] = unquote(connect_time) if connect_time is not None else ""
            item["ssid"] = unquote(ssid) if ssid is not None else ""

        return {
            "wired_host_count": host_count_info['wired_host_count'],
            "wireless_host_count": host_count_info['wireless_host_count'],
            "ssid_host_count": ssid_host_count,
            "cpu_used": cpu_used,
            "memory_used": json['system']['mem_usage']['mem'],
            "wan_state": wan_state,
            "hosts": clean_hosts,
        }

    async def request(self, payload, url=None):
        url = url or f"{self.host}/stok={self.token}/ds"
        headers = {
            "Content-Type": "application/json",  # 声明JSON数据
        }

        try:
            async with self._session.post(
                    url,
                    headers=headers,
                    json=payload,
            ) as response:
                return await response.json()
        except Exception as e:
            _LOGGER.error(f"REQUEST FAILED: {e}")
            raise ValueError(f"REQUEST FAILED: {e}")
