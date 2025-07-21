import asyncio
import logging

from homeassistant.components.device_tracker import ScannerEntity, SourceType
from homeassistant.components.device_tracker.config_entry import BaseTrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import translation
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TPLinkEnterpriseRouterCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    if not entry.data.get("enable_host_entity", False):
        return

    coordinator: TPLinkEnterpriseRouterCoordinator = hass.data[DOMAIN][entry.entry_id]
    tracker = DeviceTracker(hass, entry, coordinator, async_add_entities)

    """ Update the status of the old devices. """
    await tracker.init()
    await tracker.create_old_hosts()

    @callback
    def coordinator_updated():
        """Update the status of the devices."""
        asyncio.create_task(async_callback())

    async def async_callback():
        await tracker.update_hosts(coordinator.status['hosts_dict'])

    entry.async_on_unload(coordinator.async_add_listener(coordinator_updated))
    coordinator_updated()


class DeviceTracker:
    disconnect_text = "disconnected"

    def __init__(self,
                 hass: HomeAssistant,
                 entry: ConfigEntry,
                 coordinator: TPLinkEnterpriseRouterCoordinator,
                 async_add_entities: AddEntitiesCallback
                 ) -> None:
        self.hass = hass
        self.entry = entry
        self.store = Store(hass, version=1, key=f"{DOMAIN}_{entry.entry_id}")
        self.mac_list = []
        self.tracked: {str, TPLinkTracker} = {}
        self.coordinator = coordinator
        self.async_add_entities = async_add_entities

    async def init(self):
        self.mac_list = await self._get_tracked_mac_list()

        """ Setup translations """
        translations = await translation.async_get_translations(
            self.hass,
            self.hass.config.language,
            "component",
            [DOMAIN],
        )
        DeviceTracker.disconnect_text = translations.get(
            "component.tplink_enterprise_router.component.tplink_enterprise_router.entity.disconnected"
        )

    async def create_old_hosts(self):
        entities = []
        for mac in self.mac_list:
            entity = TPLinkTracker(mac, self.coordinator)
            entities.append(entity)
            self.tracked[mac] = entity
        self.async_add_entities(entities, False)

    async def update_hosts(self, host_dict: dict) -> None:
        new_mac_list = list(host_dict.keys())
        added = list(set(new_mac_list) - set(self.mac_list))
        removed = list(set(self.mac_list) - set(new_mac_list))

        merged_mac_list = list(set(self.mac_list + new_mac_list))
        self.mac_list = merged_mac_list
        await self._save_tracked_mac_list(merged_mac_list)

        entities = []
        for mac in added:
            entity = TPLinkTracker(mac, self.coordinator)
            entities.append(entity)
        self.async_add_entities(entities, False)

    async def _get_tracked_mac_list(self) -> list:
        data = await self._async_load_data()
        return data.get("mac_list", [])

    async def _save_tracked_mac_list(self, mac_list: list) -> None:
        await self._async_save_data({
            "mac_list": mac_list
        })

    async def _async_load_data(self) -> dict:
        data = await self.store.async_load()
        return data or {}

    async def _async_save_data(self, data: dict) -> None:
        await self.store.async_save(data)


class TPLinkTracker(CoordinatorEntity, BaseTrackerEntity):
    """Representation of network device."""

    def __init__(
            self,
            mac,
            coordinator: TPLinkEnterpriseRouterCoordinator,
    ) -> None:
        """Initialize the tracked device."""
        self.mac = mac
        self.device = coordinator.status['hosts_dict'].get(mac, {})
        mac_key = mac.replace("-", "_")
        entry_key = coordinator.entry.entry_id
        self._attr_device_info = coordinator.device_info
        _LOGGER.error(self.device_info)
        self._attr_unique_id = f"{DOMAIN}_host_{mac_key}_{entry_key}"
        self.entity_id = f"device_tracker.{DOMAIN}_host_{mac_key}_{entry_key}"

        super().__init__(coordinator)

    @property
    def is_connected(self) -> bool:
        """Return true if the client is connected to the network."""
        return self.device.get("mac") is not None

    @property
    def source_type(self) -> str:
        """Return the source type of the client."""
        return SourceType.ROUTER

    @property
    def name(self) -> str:
        """Return the name of the client."""
        hostname = self.device.get("hostname")
        return hostname if (hostname != '' and hostname != "anonymous" and hostname != "---") else self.device.get(
            "mac")

    @property
    def hostname(self) -> str:
        """Return the hostname of the client."""
        return self.device.get('hostname')

    @property
    def mac_address(self) -> str:
        """Return the mac address of the client."""
        return self.mac

    @property
    def state(self) -> str:
        return self.device.get("ap_name", DeviceTracker.disconnect_text)

    @property
    def ip_address(self) -> str:
        """Return the ip address of the client."""
        return self.device.get("ip")

    @property
    def unique_id(self) -> str:
        """Return an unique identifier for this device."""
        return f"{DOMAIN}_host_{self.mac_address}_{self.coordinator.unique_id}"

    @property
    def icon(self) -> str:
        """Return device icon."""
        return "mdi:lan-connect" if self.is_connected else "mdi:lan-disconnect"

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        return {
            'hostname': self.hostname,
            'ip_address': self.ip_address,
            'mac_address': self.mac_address,
        }

    # @property
    # def data(self) -> dict[str, str]:
    #     return dict(self.extra_state_attributes.items() | {
    #         'hostname': self.hostname,
    #         'ip_address': self.ip_address,
    #         'mac_address': self.mac_address,
    #     }.items())

    @property
    def entity_registry_enabled_default(self) -> bool:
        return True

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.device = self.coordinator.status['hosts_dict'].get(self.mac, {})
        self.async_write_ha_state()
