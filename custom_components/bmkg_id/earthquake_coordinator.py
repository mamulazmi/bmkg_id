"""DataUpdateCoordinator for BMKG earthquake data."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BmkgApiClientCommunicationError, BmkgApiClientError
from .const import DEFAULT_EARTHQUAKE_UPDATE_INTERVAL_MINUTES, DOMAIN, LOGGER

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import BmkgConfigEntry

SHAKEMAP_BASE_URL = "https://static.bmkg.go.id/"


class BmkgEarthquakeCoordinator(DataUpdateCoordinator):
    """Fetch BMKG earthquake data on a schedule."""

    config_entry: BmkgConfigEntry

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=f"{DOMAIN}_earthquake",
            update_interval=timedelta(minutes=DEFAULT_EARTHQUAKE_UPDATE_INTERVAL_MINUTES),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch earthquake list, find nearest to HA coordinates."""
        try:
            earthquakes = (
                await self.config_entry.runtime_data.earthquake_client.async_get_earthquakes()
            )
        except BmkgApiClientCommunicationError as exception:
            raise UpdateFailed(exception) from exception
        except BmkgApiClientError as exception:
            raise UpdateFailed(exception) from exception

        ha_lat: float = self.hass.config.latitude
        ha_lon: float = self.hass.config.longitude

        client = self.config_entry.runtime_data.earthquake_client
        nearest = client.find_nearest(earthquakes, ha_lat, ha_lon)

        # Latest = first in list (API returns newest first)
        latest = earthquakes[0] if earthquakes else None

        def with_shakemap(quake: dict[str, Any] | None) -> dict[str, Any] | None:
            if quake is None:
                return None
            shakemap_code = quake.get("Shakemap", "")
            result = dict(quake)
            if shakemap_code:
                result["_shakemap_url"] = f"{SHAKEMAP_BASE_URL}{shakemap_code}"
            return result

        return {
            "earthquakes": earthquakes,
            "nearest": with_shakemap(nearest),
            "latest": with_shakemap(latest),
            "ha_lat": ha_lat,
            "ha_lon": ha_lon,
        }
