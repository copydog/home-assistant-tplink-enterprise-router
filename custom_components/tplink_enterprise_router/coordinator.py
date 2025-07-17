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
            "polling": True,
        }
        self.device_info = None

        self.unique_id = entry.entry_id
        self.client = TPLinkEnterpriseRouterClient(hass, self.host, username, password)
        self.scan_stopped_at: datetime | None = None
        self.client_log_sensor = None
        self.debug_log_sensor = None

        super().__init__(
            hass,
            _LOGGER,
            name="TPLinkEnterpriseRouter",
            update_interval=timedelta(seconds=update_interval),
        )

    @staticmethod
    def request(router: TPLinkEnterpriseRouterClient, callback: Callable):
        router.authenticate()
        data = callback()

        return data

    async def reboot(self) -> None:
        await self.client.authenticate()
        await self.client.reboot()

    async def set_ap_light(self, status: str) -> None:
        await self.client.authenticate()
        await self.client.set_ap_light(status)

    async def set_polling(self, value: bool) -> None:
        self.set_status({
            "polling": value
        })

    def set_status(self, data) -> None:
        self.status = {
            **self.status,
            **data,
        }

    async def _async_update_data(self):
        if not self.status["polling"]:
            return

        await self.client.authenticate()

        data = await self.client.get_status()
        ap_data = await self.client.get_ap_status()

        self.set_status({
            **data,
            **ap_data,
            "host_count": data['wireless_host_count'] + data['wired_host_count'],
        })


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
