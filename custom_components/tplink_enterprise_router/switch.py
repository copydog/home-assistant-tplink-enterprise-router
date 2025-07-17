from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TPLinkEnterpriseRouterCoordinator


@dataclass
class TPLinkEnterpriseRouterSwitchEntityDescriptionMixin:
    method: Callable[[TPLinkEnterpriseRouterCoordinator, bool], Any]
    property: str


@dataclass
class TPLinkEnterpriseRouterSwitchEntityDescription(
    SwitchEntityDescription,
    TPLinkEnterpriseRouterSwitchEntityDescriptionMixin
):
    pass


SWITCH_TYPES = (
    TPLinkEnterpriseRouterSwitchEntityDescription(
        key="polling",
        translation_key="polling",
        name="Polling",
        property="polling",
        entity_category=EntityCategory.CONFIG,
        method=lambda coordinator, value: coordinator.set_polling(value),
    ),
)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]

    switches = []

    for description in SWITCH_TYPES:
        switches.append(TPLinkEnterpriseRouterSwitchEntity(coordinator, description))

    async_add_entities(switches, False)


class TPLinkEnterpriseRouterSwitchEntity(
    CoordinatorEntity[TPLinkEnterpriseRouterCoordinator], SwitchEntity
):
    entity_description: TPLinkEnterpriseRouterSwitchEntityDescription

    def __init__(
            self,
            coordinator: TPLinkEnterpriseRouterCoordinator,
            description: TPLinkEnterpriseRouterSwitchEntityDescription,
    ) -> None:
        super().__init__(coordinator)

        self.entity_id = f"switch.{DOMAIN}_{description.key}_{coordinator.unique_id}"
        self._attr_unique_id = f"{DOMAIN}_{description.key}_{coordinator.unique_id}"
        self._attr_device_info = coordinator.device_info
        self.entity_description = description
        self._attr_has_entity_name = True

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self.coordinator.status[self.entity_description.property]

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self.entity_description.method(self.coordinator, True)
        self.coordinator.status[self.entity_description.property] = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self.entity_description.method(self.coordinator, False)
        self.coordinator.status[self.entity_description.property] = False
        self.async_write_ha_state()
