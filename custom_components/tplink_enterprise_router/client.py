import logging
from urllib.parse import unquote
from aiohttp import ClientTimeout

from homeassistant.exceptions import HomeAssistantError, IntegrationError, ConfigEntryAuthFailed
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
        try:
            json = await self.request(
                self.host,
                {"method": "do", "login": {"username": self.username, "password": self.password}},
            )

            if json['error_code'] != 0:
                raise ConfigEntryAuthFailed(f"Failed to authenticate, check host, username and password")

            self.token = json['stok']
        except Exception as e:
            raise IntegrationError(f"Cannot connect router {e}")

    async def logout(self):
        if self.token is None:
            return

        await self.request(f"{self.host}/stok={self.token}/ds", {"method": "do", "system": {"logout": None}})

    async def reboot(self):
        if self.token is None:
            await self.authenticate()

        json = await self.request(f"{self.host}/stok={self.token}/ds", {"method": "do", "system": {"reboot": None}})

        if json.get("error_code") == -40401:
            self.token = None
            await self.reboot()

    async def set_ap_light(self, status: str):
        if self.token is None:
            await self.authenticate()

        json = await self.request(
            f"{self.host}/stok={self.token}/ds",
            {"method": "set", "apmng_set": {"ap_led_global_switch": {"led_switch": status}}}
        )

        if json.get("error_code") == -40401:
            self.token = None
            await self.set_ap_light(status)

    async def reboot_ap(self, id_list: list):
        if self.token is None:
            await self.authenticate()

        json = await self.request(
            f"{self.host}/stok={self.token}/ds",
            {"method": "do", "apmng_status": {"ap_reboot": {"entry_id": id_list}}}
        )

        if json.get("error_code") == -40401:
            self.token = None
            await self.reboot_ap(id_list)

    async def set_ssid(self, serv_id, para):
        if self.token is None:
            await self.authenticate()

        json = await self.request(
            f"{self.host}/stok={self.token}/ds",
            {
                "method": "set",
                "apmng_wserv": {"table": "wlan_serv", "filter": [{"serv_id": str(serv_id)}], "para": para}
            }
        )

        if json.get("error_code") == -40401:
            self.token = None
            await self.set_ssid(serv_id, para)

    async def get_status(self):
        if self.token is None:
            await self.authenticate()

        json = await self.request(
            f"{self.host}/stok={self.token}/ds",
            {
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
                "online_check": {"table": "state", "name": "state"},
                "apmng_status": {
                    "name": "apmng_status"
                },
                "apmng_set": {
                    "table": "ap_list",
                    "filter": [
                        {"group_id": "0", "ap_role": "re_all"}, {"group_id": "0"}
                    ],
                    "para": {"start": 0, "end": 499}
                },
                "apmng_wserv": {
                    "table": "wlan_serv", "filter": {"network_type": ["1", "2", "3"]},
                    "para": {"start": 0, "end": 9}
                }
            })

        """ Authenticate before request """
        if json.get("error_code") == -40401:
            self.token = None
            return await self.get_status()

        return self.process_data(json)

    def process_data(self, json):
        system = json.get("system", {})

        """ Calculate cpu used """
        cpu_usage = system.get('cpu_usage')
        cpu_usages = [int(v) for v in cpu_usage.values()]
        cpu_used = sum(cpu_usages) / len(cpu_usages) if cpu_usages else 0

        """ Calculate Wan count and status """
        _online_check = json.get("online_check", {})
        state_dict = _online_check.get("state", {})
        wan_states = [
            {"key": k.replace("state_", ""), **v}
            for k, v in state_dict.items()
        ]
        wan_count = _online_check.get("count", {}).get("state", None)

        """ Calculate hosts """
        hosts = json['host_management']['host_info']
        clean_hosts = [list(item.values())[0] for item in hosts]
        clean_hosts = [
            {key: unquote(item.get(key, ''))
             for key in
             ['connect_date', 'rssi', 'ip', 'hostname', 'connect_time', 'mac', 'type', 'ssid', 'freq_name', 'ap_name']
             if key in item} for item in clean_hosts
        ]
        wireless_hosts = [
            {k: v for k, v in host.items() if k != "type"}
            for host in clean_hosts if host.get("type") == "wireless"
        ]
        wired_hosts = [
            {k: v for k, v in host.items() if k != "type"}
            for host in clean_hosts if host.get("type") == "wired"
        ]

        """ Calculate SSID count """
        host_count_info = json['host_management']['host_count_info']
        if 'ssid_host_count' in host_count_info and host_count_info['ssid_host_count']:
            ssid_host_count = [{"ssid": key, "count": value} for key, value in
                               host_count_info['ssid_host_count'].items()]
        else:
            ssid_counts = {}
            for host_info in clean_hosts:
                if host_info.get("type") == "wireless" and host_info.get("ssid"):
                    ssid = host_info.get("ssid")
                    if ssid in ssid_counts:
                        ssid_counts[ssid] += 1
                    else:
                        ssid_counts[ssid] = 1
            ssid_host_count = [{"ssid": ssid, "count": count} for ssid, count in ssid_counts.items()]

        if ('wired_host_count' in host_count_info and
                'wireless_host_count' in host_count_info):
            wired_host_count = host_count_info['wired_host_count']
            wireless_host_count = host_count_info['wireless_host_count']
        else:
            wired_host_count = len(wired_hosts)
            wireless_host_count = len(wireless_hosts)

        ap_list = json.get("apmng_set", {}).get("ap_list", [])
        ap_list = [inner_dict for item in ap_list for inner_dict in item.values()]
        ap_list = [{key: item[key] for key in ['entry_name', 'entry_id', 'mac', 'status', 'led'] if key in item} for
                   item in ap_list]
        ap_count = len(ap_list)
        ap_online_count = sum(1 for ap in ap_list if ap.get("status") == "2")
        ap_offline_count = sum(1 for ap in ap_list if ap.get("status") != "2")
        ap_online_list = [ap for ap in ap_list if ap.get("status") == "2"]
        ap_offline_list = [ap for ap in ap_list if ap.get("status") != "2"]

        """ Get SSID List """
        ssid_list = json.get("apmng_wserv", {}).get("wlan_serv", [])
        ssid_list = [{key: item[key] for key in ['ssid', 'enable', 'serv_id'] if key in item} for dict in ssid_list for
                     item in dict.values()]

        return {
            "hosts": clean_hosts,
            "wireless_hosts": wireless_hosts,
            "wired_hosts": wired_hosts,
            "host_count": len(hosts),
            "wired_host_count": wired_host_count,
            "wireless_host_count": wireless_host_count,
            "ssid_host_count": ssid_host_count,
            "cpu_used": cpu_used,
            "memory_used": system.get("mem_usage", {}).get("mem"),
            "wan_states": wan_states,
            "wan_count": wan_count,
            "device_info": system.get("device_info"),
            "ap_count": ap_count,
            "ap_list": ap_list,
            "ap_online_count": ap_online_count,
            "ap_online_list": ap_online_list,
            "ap_offline_count": ap_offline_count,
            "ap_offline_list": ap_offline_list,
            "ssid_list": ssid_list,
        }

    async def request(self, url, payload):
        headers = {
            "Content-Type": "application/json",
        }
        timeout = ClientTimeout(total=5)

        try:
            async with self._session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=timeout,
            ) as response:
                return await response.json()

        except Exception as e:
            raise IntegrationError(f"Fail to request host: {self.host} payload: {payload} error: {e}")
