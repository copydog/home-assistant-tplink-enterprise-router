from __future__ import annotations
from datetime import timedelta, datetime
import logging

from collections.abc import Callable
from urllib.parse import unquote

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from .const import DOMAIN

from custom_components.tplink_enterprise_router.client import TPLinkEnterpriseRouterClient

_LOGGER = logging.getLogger(__name__)


class TPLinkEnterpriseRouterCoordinator(DataUpdateCoordinator):

    def __init__(
            self,
            hass: HomeAssistant,
            entry: ConfigEntry,
    ) -> None:
        update_interval = entry.data.get('update_interval') or 30
        self.host = entry.data.get('host')
        username = entry.data.get('username')
        password = entry.data.get('password')
        self.status = {
            "running": True,
            "device_info": {}
        }
        self.device_info = None

        self.unique_id = entry.entry_id
        self.client = TPLinkEnterpriseRouterClient(hass, self.host, username, password)
        self.scan_stopped_at: datetime | None = None

        super().__init__(
            hass,
            _LOGGER,
            name="TPLinkEnterpriseRouter",
            update_interval=timedelta(seconds=update_interval),
        )

    async def reboot(self) -> None:
        await self.client.authenticate()
        await self.client.reboot()

    async def set_ap_light(self, status: str) -> None:
        await self.client.authenticate()
        await self.client.set_ap_light(status)

    async def set_running(self, value: bool) -> None:
        self.set_status({
            "running": value
        })

    def set_status(self, data) -> None:
        self.status = {
            **self.status,
            **data,
        }

    async def _async_update_data(self):
        if not self.status["running"]:
            return

        await self.client.authenticate()
        data = await self.client.get_status()
        """ Get Host Count """
        self.set_status({
            **data,
            "host_count": data['wireless_host_count'] + data['wired_host_count'],
        })

        self.last_update_success = True

        self.device_info = DeviceInfo(
            configuration_url=self.host,
            connections={(CONNECTION_NETWORK_MAC, data['device_info']['mac'])},
            identifiers={(DOMAIN, data['device_info']['mac'])},
            manufacturer="TP-Link",
            model=data['device_info']['model'],
            name="TP-Link",
            sw_version=unquote(data['device_info']['firmware_version']),
            hw_version=data['device_info']['hardware_version'],
        )