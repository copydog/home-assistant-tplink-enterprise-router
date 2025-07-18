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
        update_interval = entry.data.get('update_interval') or 60
        self.status = {
            "polling": True,
        }
        self.device_info = None
        self.unique_id = entry.entry_id
        self.client = TPLinkEnterpriseRouterClient(hass, self.host, username, password)
        self.force_update = False

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

    async def set_ap_light(self, status: str) -> None:
        await self.client.set_ap_light(status)

    async def set_polling(self, value: bool) -> None:
        self.set_status({
            "polling": value
        })

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

        """ Update status """
        data = await self.client.get_status()

        self.set_status(data)

        """ Build DeviceInfo """
        if data['device_info'].get('model'):
            self.router_name = f"TP-Link {data['device_info']['model']} ({self.host})"

        if data['device_info'].get('firmware_version'):
            self.firmware_version = unquote(data['device_info']['firmware_version'])

        self.device_info = DeviceInfo(
            configuration_url=self.host,
            connections={(CONNECTION_NETWORK_MAC, data['device_info']['mac'])},
            identifiers={(DOMAIN, data['device_info']['mac'])},
            manufacturer="TP-LINK",
            model=data['device_info']['model'],
            name=self.router_name,
            sw_version=self.firmware_version,
            hw_version=data['device_info']['hardware_version'],
        )
