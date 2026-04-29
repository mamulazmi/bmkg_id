"""Custom types for BMKG integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry

if TYPE_CHECKING:
    from .api import BmkgApiClient, BmkgEarthquakeApiClient, BmkgNowcastApiClient
    from .coordinator import BmkgDataUpdateCoordinator
    from .earthquake_coordinator import BmkgEarthquakeCoordinator
    from .nowcast_coordinator import BmkgNowcastCoordinator

type BmkgConfigEntry = ConfigEntry[BmkgData]


@dataclass
class BmkgData:
    """Data stored in config entry runtime_data."""

    client: BmkgApiClient
    coordinator: BmkgDataUpdateCoordinator
    earthquake_client: BmkgEarthquakeApiClient
    earthquake_coordinator: BmkgEarthquakeCoordinator
    nowcast_client: BmkgNowcastApiClient
    nowcast_coordinator: BmkgNowcastCoordinator
