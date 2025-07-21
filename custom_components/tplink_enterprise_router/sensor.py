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
        icon="mdi:access-point-network",
        state_class=SensorStateClass.TOTAL,
        value=lambda status: status['wireless_host_count'],
        attrs=lambda status: {
            "hosts": status['wireless_hosts'],
            "ap_connected_hosts": status['ap_connected_hosts'],
        }
    ),
    TPLinkEnterpriseRouterSensorEntityDescription(
        key="wired_clients_total",
        name="Total Wired Clients",
        translation_key="wired_clients_total",
        icon="mdi:cable-data",
        state_class=SensorStateClass.TOTAL,
        value=lambda status: status['wired_host_count'],
        attrs=lambda status: {
            "hosts": status['wired_hosts'],
        }
    ),
    TPLinkEnterpriseRouterSensorEntityDescription(
        key="clients_total",
        name="Total Clients",
        translation_key="clients_total",
        icon="mdi:account-multiple",
        state_class=SensorStateClass.TOTAL,
        value=lambda status: status['host_count'],
        attrs=lambda status: {
            "hosts": status['hosts'],
            "ssid_host_count": status['ssid_host_count'],
        }
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
        key="wan_count",
        name="WAN Count",
        translation_key="wan_count",
        icon="mdi:wan",
        value=lambda status: status['wan_count'],
        attrs=lambda status: {}
    ),
    TPLinkEnterpriseRouterSensorEntityDescription(
        key="ap_count",
        name="AP Count",
        translation_key="ap_count",
        icon="mdi:access-point",
        value=lambda status: status['ap_count'],
        attrs=lambda status: {
            "list": status['ap_list'],
        }
    ),
    TPLinkEnterpriseRouterSensorEntityDescription(
        key="ap_online_count",
        name="AP Online Count",
        translation_key="ap_online_count",
        icon="mdi:access-point-check",
        value=lambda status: status['ap_online_count'],
        attrs=lambda status: {
            "list": status['ap_online_list'],
        }
    ),
TPLinkEnterpriseRouterSensorEntityDescription(
        key="ap_offline_count",
        name="AP Offline Count",
        translation_key="ap_offline_count",
        icon="mdi:access-point-remove",
        value=lambda status: status['ap_offline_count'],
        attrs=lambda status: {
            "list": status['ap_offline_list'],
        }
    ),
)


async def async_setup_entry(
        hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: TPLinkEnterpriseRouterCoordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = []

    for description in SENSOR_TYPES:
        sensors.append(TPLinkEnterpriseRouterSensor(coordinator, description))

    """ Create dynamic Wan sensors """
    wan_states = coordinator.status.get("wan_states", [])
    for wan_state in wan_states:
        key = wan_state.get("key")
        sensors.append(TPLinkEnterpriseRouterSensor(
            coordinator,
            TPLinkEnterpriseRouterSensorEntityDescription(
                key=f"wan_state_{key}",
                name=f"WAN{key} State",
                translation_key=f"wan_{key}_state",
                icon="mdi:wan",
                value=lambda status: wan_state.get("state"),
                attrs=lambda status: {}
            ),
        ))

    async_add_entities(sensors, False)


class TPLinkEnterpriseRouterSensor(
    CoordinatorEntity[TPLinkEnterpriseRouterCoordinator], SensorEntity
):
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
        self._attr_native_value = self.entity_description.value(self.coordinator.status)
        self._attr_extra_state_attributes = self.entity_description.attrs(self.coordinator.status)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.entity_description.value(self.coordinator.status)
        self._attr_extra_state_attributes = self.entity_description.attrs(self.coordinator.status)
        self.async_write_ha_state()
