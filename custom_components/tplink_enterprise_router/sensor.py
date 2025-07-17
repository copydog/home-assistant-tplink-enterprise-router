from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote

from homeassistant.components.sensor import (
    SensorStateClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TPLinkEnterpriseRouterCoordinator


@dataclass
class TPLinkEnterpriseRouterSensorRequiredKeysMixin:
    value: Callable[[Any], Any]
    attrs: Callable[[Any], Any]


@dataclass
class TPLinkEnterpriseRouterSensorEntityDescription(
    SensorEntityDescription, TPLinkEnterpriseRouterSensorRequiredKeysMixin
):
    pass


SENSOR_TYPES: tuple[TPLinkEnterpriseRouterSensorEntityDescription, ...] = (
    TPLinkEnterpriseRouterSensorEntityDescription(
        key="wireless_clients_total",
        name="Total Wireless Clients",
        translation_key="wireless_clients_total",
        icon="mdi:account-multiple",
        state_class=SensorStateClass.TOTAL,
        value=lambda status: status['wireless_host_count'],
        attrs=lambda status: {}
    ),
    TPLinkEnterpriseRouterSensorEntityDescription(
        key="wired_clients_total",
        name="Total Wired Clients",
        translation_key="wired_clients_total",
        icon="mdi:account-multiple",
        state_class=SensorStateClass.TOTAL,
        value=lambda status: len([
            host for host in status['hosts']
            if host.get('ap_name') and host.get('type') == 'wireless' and host.get('ip')
        ]),
        attrs=lambda status: {}
    ),
    TPLinkEnterpriseRouterSensorEntityDescription(
        key="clients_total",
        name="Total Clients",
        translation_key="clients_total",
        icon="mdi:account-multiple",
        state_class=SensorStateClass.TOTAL,
        value=lambda status: status['host_count'],
        attrs=lambda status: {}
    ),
    TPLinkEnterpriseRouterSensorEntityDescription(
        key="cpu_used",
        name="CPU Used",
        translation_key="cpu_used",
        icon="mdi:cpu-64-bit",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
        value=lambda status: status['cpu_used'],
        attrs=lambda status: {}
    ),
    TPLinkEnterpriseRouterSensorEntityDescription(
        key="memory_used",
        name="Memory Used",
        translation_key="memory_used",
        icon="mdi:memory",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
        value=lambda status: status['memory_used'],
        attrs=lambda status: {}
    ),
    TPLinkEnterpriseRouterSensorEntityDescription(
        key="wan_state",
        name="WAN State",
        translation_key="wan_state",
        icon="mdi:wan",
        value=lambda status: status['wan_state'],
        attrs=lambda status: {}
    ),
    TPLinkEnterpriseRouterSensorEntityDescription(
        key="ap_connected_devices",
        translation_key="ap_connected_devices",
        name="AP Connected Devices",
        icon="mdi:access-point-network",
        value=lambda status: len([
            host for host in status['hosts']
            if host.get('ap_name') and host.get('type') == 'wireless' and host.get('ip')
        ]),
        attrs=lambda status: {
            ap_name: [
                {
                    "name": (lambda h:
                             h.get('name', h.get('mac', 'Unknown'))
                             if not h.get('hostname') or unquote(h.get('hostname')) == '---'
                             else unquote(h.get('hostname'))
                             )(host),
                    "mac": host.get('mac', ''),
                    "ip": host.get('ip', ''),
                    "ssid": host.get('ssid', ''),
                    "rssi": host.get('rssi', ''),
                    "ap_name": host.get('ap_name', ''),
                    "connect_date": host.get('connect_date', ''),
                    "connect_time": host.get('connect_time', ''),
                    "connection_type": host.get('type', '')
                }
                for host in status['hosts']
                if host.get('ap_name') == ap_name and host.get('type') == 'wireless' and host.get('ip')
            ]
            for ap_name in set(
                host.get('ap_name', '')
                for host in status['hosts']
                if host.get('ap_name') and host.get('type') == 'wireless' and host.get('ip')
            )
        }
    ),
    TPLinkEnterpriseRouterSensorEntityDescription(
        key="data",
        name="Data",
        icon="mdi:database",
        value=lambda status: len(status['hosts']),
        attrs=lambda status: {
            "host": status['hosts'],
            "ssid": status['ssid_host_count']
        }
    ),
)


async def async_setup_entry(
        hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = []

    for description in SENSOR_TYPES:
        sensors.append(TPLinkEnterpriseRouterSensor(coordinator, description))

    async_add_entities(sensors, False)


class TPLinkEnterpriseRouterSensor(
    CoordinatorEntity[TPLinkEnterpriseRouterCoordinator], SensorEntity
):
    _attr_has_entity_name = True
    entity_description: TPLinkEnterpriseRouterSensorEntityDescription

    def __init__(
            self,
            coordinator: TPLinkEnterpriseRouterCoordinator,
            description: TPLinkEnterpriseRouterSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)

        self.entity_id = f"sensor.{DOMAIN}_{description.key}_{coordinator.unique_id}"
        self._attr_unique_id = f"{DOMAIN}_{description.key}_{coordinator.unique_id}"
        self._attr_device_info = coordinator.device_info
        self.entity_description = description
        self._attr_has_entity_name = True

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.entity_description.value(self.coordinator.status)
        self._attr_extra_state_attributes = self.entity_description.attrs(self.coordinator.status)
        self.async_write_ha_state()