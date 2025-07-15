"""Component providing support for TPLinkRouter button entities."""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TPLinkEnterpriseRouterCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass
class TPLinkEnterpriseRouterButtonEntityDescriptionMixin:
    method: Callable[[TPLinkEnterpriseRouterCoordinator], Any]


@dataclass
class TPLinkButtonEntityDescription(
    ButtonEntityDescription, TPLinkEnterpriseRouterButtonEntityDescriptionMixin
):
    """A class that describes button entities for the host."""


BUTTON_TYPES = (
    TPLinkButtonEntityDescription(
        key="reboot",
        name="Reboot",
        device_class=ButtonDeviceClass.RESTART,
        entity_category=EntityCategory.CONFIG,
        method=lambda coordinator: coordinator.reboot(),
    ),
    TPLinkButtonEntityDescription(
        key="turn_on_ap_light",
        name="Turn On AP Light",
        device_class=ButtonDeviceClass.UPDATE,
        entity_category=EntityCategory.CONFIG,
        method=lambda coordinator: coordinator.set_ap_light("on"),
    ),
    TPLinkButtonEntityDescription(
        key="turn_off_ap_light",
        name="Turn Off AP Light",
        device_class=ButtonDeviceClass.UPDATE,
        entity_category=EntityCategory.CONFIG,
        method=lambda coordinator: coordinator.set_ap_light("off"),
    ),
)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]

    buttons = []

    for description in BUTTON_TYPES:
        buttons.append(TPLinkEnterpriseRouterButtonEntity(coordinator, description))
    async_add_entities(buttons, False)

class TPLinkEnterpriseRouterButtonEntity(CoordinatorEntity[TPLinkEnterpriseRouterCoordinator], ButtonEntity):
    entity_description: TPLinkButtonEntityDescription

    def __init__(
            self,
            coordinator: TPLinkEnterpriseRouterCoordinator,
            description: TPLinkButtonEntityDescription,
    ) -> None:
        super().__init__(coordinator)

        self.entity_id = f"button.{DOMAIN}_{description.key}_{coordinator.unique_id}"
        self._attr_unique_id = f"{DOMAIN}_{description.key}_{coordinator.unique_id}"
        self._attr_device_info = coordinator.device_info
        self.entity_description = description

    async def async_press(self) -> None:
        await self.entity_description.method(self.coordinator)
