"""BMKG Weather custom integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BmkgApiClient, BmkgEarthquakeApiClient, BmkgNowcastApiClient
from .const import CONF_ADM4, CONF_NOWCAST_LANGUAGE, DEFAULT_NOWCAST_LANGUAGE, DOMAIN  # noqa: F401
from .coordinator import BmkgDataUpdateCoordinator
from .data import BmkgData
from .earthquake_coordinator import BmkgEarthquakeCoordinator
from .nowcast_coordinator import BmkgNowcastCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import BmkgConfigEntry

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR, Platform.WEATHER]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BmkgConfigEntry,
) -> bool:
    """Set up BMKG Weather from a config entry."""
    session = async_get_clientsession(hass)

    coordinator = BmkgDataUpdateCoordinator(hass=hass)
    earthquake_coordinator = BmkgEarthquakeCoordinator(hass=hass)
    nowcast_coordinator = BmkgNowcastCoordinator(hass=hass)

    entry.runtime_data = BmkgData(
        client=BmkgApiClient(adm4=entry.data[CONF_ADM4], session=session),
        coordinator=coordinator,
        earthquake_client=BmkgEarthquakeApiClient(session=session),
        earthquake_coordinator=earthquake_coordinator,
        nowcast_client=BmkgNowcastApiClient(
            session=session,
            language=entry.options.get(CONF_NOWCAST_LANGUAGE, DEFAULT_NOWCAST_LANGUAGE),
        ),
        nowcast_coordinator=nowcast_coordinator,
    )

    coordinator.config_entry = entry
    earthquake_coordinator.config_entry = entry
    nowcast_coordinator.config_entry = entry

    # Weather must load first — nowcast coordinator reads lokasi.provinsi from it
    await coordinator.async_config_entry_first_refresh()
    await earthquake_coordinator.async_config_entry_first_refresh()
    await nowcast_coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: BmkgConfigEntry,
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: BmkgConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
