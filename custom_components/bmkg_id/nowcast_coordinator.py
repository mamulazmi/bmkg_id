"""DataUpdateCoordinator for BMKG weather warning (nowcast) data."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BmkgApiClientCommunicationError, BmkgApiClientError
from .const import DEFAULT_NOWCAST_UPDATE_INTERVAL_MINUTES, DOMAIN, LOGGER

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import BmkgConfigEntry


class BmkgNowcastCoordinator(DataUpdateCoordinator):
    """Fetch BMKG nowcast warning RSS on a schedule."""

    config_entry: BmkgConfigEntry

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=f"{DOMAIN}_nowcast",
            update_interval=timedelta(minutes=DEFAULT_NOWCAST_UPDATE_INTERVAL_MINUTES),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch warnings, filter by user's province."""
        try:
            warnings = (
                await self.config_entry.runtime_data.nowcast_client.async_get_warnings()
            )
        except BmkgApiClientCommunicationError as exception:
            raise UpdateFailed(exception) from exception
        except BmkgApiClientError as exception:
            raise UpdateFailed(exception) from exception

        # Get province from weather coordinator data (already fetched)
        weather_data = self.config_entry.runtime_data.coordinator.data or {}
        province: str = weather_data.get("lokasi", {}).get("provinsi", "")

        from .api import BmkgNowcastApiClient  # noqa: PLC0415

        province_warnings = BmkgNowcastApiClient.filter_by_province(warnings, province)
        latest_province = province_warnings[0] if province_warnings else None
        latest_all = warnings[0] if warnings else None

        return {
            "all_warnings": warnings,
            "province_warnings": province_warnings,
            "province_warning_count": len(province_warnings),
            "total_warning_count": len(warnings),
            "latest_province": latest_province,
            "latest_all": latest_all,
            "province": province,
        }
