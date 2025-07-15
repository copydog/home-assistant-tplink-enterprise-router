"""The integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import IntegrationError

from .const import (DOMAIN, PLATFORMS)
from .coordinator import TPLinkEnterpriseRouterCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """ Check register status """
    if entry.entry_id in hass.data.get(DOMAIN, {}):
        _LOGGER.warning("Integration already loaded, skipping reload")
        return True

    """ Register coordinator """
    _coordinator = TPLinkEnterpriseRouterCoordinator(hass, entry)
    await _coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = _coordinator

    """ Forward setup """
    await hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """ Unload the platform """
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    )

    """ Unload the data """
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return True