"""DataUpdateCoordinator for BMKG weather warning (nowcast) data."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BmkgApiClientCommunicationError, BmkgApiClientError
from .const import (
    CONF_NOWCAST_INTERVAL,
    DEFAULT_NOWCAST_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    LOGGER,
)

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
        self._cap_cache: dict[str, dict] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch warnings, filter by user's province."""
        interval = int(
            self.config_entry.options.get(
                CONF_NOWCAST_INTERVAL, DEFAULT_NOWCAST_UPDATE_INTERVAL_MINUTES
            )
        )
        new_interval = timedelta(minutes=interval)
        if self.update_interval != new_interval:
            self.update_interval = new_interval

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

        # Cleanup stale cap_codes from cache
        current_codes = {w["cap_code"] for w in warnings if w.get("cap_code")}
        for stale in set(self._cap_cache) - current_codes:
            del self._cap_cache[stale]

        # Fetch CAP XML detail for province warnings only (cache misses only)
        nowcast_client = self.config_entry.runtime_data.nowcast_client
        for warning in province_warnings:
            code = warning.get("cap_code")
            link = warning.get("link")
            if code and link and code not in self._cap_cache:
                cap_data = await nowcast_client.async_get_cap_xml(link)
                if cap_data:
                    self._cap_cache[code] = cap_data
            if code and code in self._cap_cache:
                warning.update(self._cap_cache[code])

        return {
            "all_warnings": warnings,
            "province_warnings": province_warnings,
            "province_warning_count": len(province_warnings),
            "total_warning_count": len(warnings),
            "latest_province": latest_province,
            "latest_all": latest_all,
            "province": province,
        }
