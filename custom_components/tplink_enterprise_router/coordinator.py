from __future__ import annotations

import logging
from datetime import timedelta
from urllib.parse import unquote

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.tplink_enterprise_router.client import TPLinkEnterpriseRouterClient
from .const import DOMAIN
from .syslog_tracker import SyslogTracker

_LOGGER = logging.getLogger(__name__)


class TPLinkEnterpriseRouterCoordinator(DataUpdateCoordinator):

    def __init__(
            self,
            hass: HomeAssistant,
            entry: ConfigEntry,
    ) -> None:
        self.host = entry.data.get('host')
        username = entry.data.get('username')
        password = entry.data.get('password')
        update_interval = entry.data.get('update_interval', 30)
        unique_id = entry.data.get('unique_id', entry.entry_id)
        self.status = {
            "polling": True,
        }
        self.device_info = None
        self.unique_id = unique_id
        self.force_update = False

        self.entry = entry
        self.client = TPLinkEnterpriseRouterClient(hass, self.host, username, password)
        self.syslog_tracker = SyslogTracker(hass, entry, self.client)

        super().__init__(
            hass,
            _LOGGER,
            name="TPLinkEnterpriseRouter",
            update_interval=timedelta(seconds=update_interval),
        )

    async def reboot(self) -> None:
        await self.client.reboot()

    async def reboot_ap(self):
        ap_list = self.status.get("ap_list", [])

        if ap_list is None:
            return

        id_list = [d["entry_id"] for d in ap_list]
        await self.client.reboot_ap(id_list)

    async def reboot_ap_and_router(self):
        await self.reboot_ap()
        await self.reboot()

    async def set_ap_light(self, status: str) -> None:
        await self.client.set_ap_light(status)

    async def set_polling(self, value: bool) -> None:
        self.set_status({
            "polling": value
        })
        await self.async_refresh()

    async def set_ssid(self, serv_id: str, para) -> None:
        await self.client.set_ssid(serv_id, para)
        await self.async_refresh()

    async def refresh(self) -> None:
        self.force_update = True
        await self.async_refresh()

    def set_status(self, data) -> None:
        self.status = {
            **self.status,
            **data,
        }

    async def _async_update_data(self):
        if not self.status["polling"] and not self.force_update:
            return

        self.force_update = False

        """ Pull status """
        data = await self.client.get_status()

        """ Update ssid status """
        ssid_list = data.get("ssid_list", [])
        for ssid in ssid_list:
            serv_id = ssid.get("serv_id")
            _property = f"__SSID_{serv_id}"
            data[_property] = ssid.get("enable") == 'on'

        self.set_status(data)

        """ Build DeviceInfo """
        if self.device_info is None:
            if data['device_info'].get('model'):
                self.router_name = f"TP-Link {data['device_info']['model']} ({self.host})"

            if data['device_info'].get('firmware_version'):
                self.firmware_version = unquote(data['device_info']['firmware_version'])

            self.device_info = DeviceInfo(
                configuration_url=self.host,
                connections={(CONNECTION_NETWORK_MAC, data['device_info']['mac'])},
                identifiers={(DOMAIN, data['device_info']['mac'])},
                manufacturer="TP-Link",
                model=data['device_info']['model'],
                name=self.router_name,
                sw_version=self.firmware_version,
                hw_version=data['device_info']['hardware_version'],
            )

        """ SyslogTracker poll """
        if self.entry.data.get("enable_syslog_poll_event", False):
            await self.syslog_tracker.poll()