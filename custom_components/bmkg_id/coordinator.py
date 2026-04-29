"""DataUpdateCoordinator for BMKG Weather."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BmkgApiClientCommunicationError, BmkgApiClientError
from .const import DEFAULT_UPDATE_INTERVAL_HOURS, DOMAIN, LOGGER

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import BmkgConfigEntry


class BmkgDataUpdateCoordinator(DataUpdateCoordinator):
    """Fetch BMKG data on a schedule."""

    config_entry: BmkgConfigEntry

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=DEFAULT_UPDATE_INTERVAL_HOURS),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch raw API data and extract current forecast."""
        try:
            raw = await self.config_entry.runtime_data.client.async_get_forecast()
        except BmkgApiClientCommunicationError as exception:
            raise UpdateFailed(exception) from exception
        except BmkgApiClientError as exception:
            raise UpdateFailed(exception) from exception

        from .api import BmkgApiClient  # noqa: PLC0415

        current = BmkgApiClient.get_current_forecast(raw)
        all_forecasts = BmkgApiClient.get_all_forecasts(raw)

        return {
            "lokasi": raw.get("lokasi", {}),
            "current": current,
            "forecasts": all_forecasts,
        }
