"""Geo location platform for BMKG earthquake data — shows quakes as map pins."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.geo_location import GeolocationEvent
from homeassistant.const import UnitOfLength
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import BmkgEarthquakeApiClient
from .const import ATTRIBUTION, DOMAIN
from .earthquake_coordinator import SHAKEMAP_BASE_URL, BmkgEarthquakeCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import BmkgConfigEntry

GEO_LOCATION_SOURCE = "BMKG Earthquake"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BmkgConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up geo_location entities for each earthquake in the API list."""
    coordinator = entry.runtime_data.earthquake_coordinator
    adm4 = entry.data.get("adm4", "unknown")
    quakes = coordinator.data.get("earthquakes", [])
    async_add_entities(
        BmkgEarthquakeGeoLocation(coordinator=coordinator, quake=q, adm4=adm4)
        for q in quakes
        if BmkgEarthquakeApiClient.parse_coordinates(q.get("Coordinates", ""))
    )


class BmkgEarthquakeGeoLocation(CoordinatorEntity[BmkgEarthquakeCoordinator], GeolocationEvent):
    """A single earthquake event shown as a pin on the HA map."""

    _attr_attribution = ATTRIBUTION
    _attr_should_poll = False
    _attr_source = GEO_LOCATION_SOURCE
    _attr_icon = "mdi:pulse"
    _attr_unit_of_measurement = UnitOfLength.KILOMETERS

    def __init__(
        self,
        coordinator: BmkgEarthquakeCoordinator,
        quake: dict[str, Any],
        adm4: str,
    ) -> None:
        """Initialize geo location entity."""
        super().__init__(coordinator)
        coords = BmkgEarthquakeApiClient.parse_coordinates(quake.get("Coordinates", ""))
        self._lat, self._lon = coords if coords else (None, None)
        self._quake = quake
        self._attr_unique_id = f"{adm4}_geo_{quake.get('DateTime', quake.get('Jam', ''))}"
        magnitude = quake.get("Magnitude", "")
        wilayah = quake.get("Wilayah", "Unknown")
        self._attr_name = f"M{magnitude} · {wilayah}" if magnitude else f"Gempa {wilayah}"

    @property
    def latitude(self) -> float | None:
        return self._lat

    @property
    def longitude(self) -> float | None:
        return self._lon

    @property
    def distance(self) -> float | None:
        return self._quake.get("_distance_km")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        shakemap = self._quake.get("Shakemap", "")
        return {
            "magnitude": self._quake.get("Magnitude"),
            "kedalaman": self._quake.get("Kedalaman"),
            "wilayah": self._quake.get("Wilayah"),
            "datetime": self._quake.get("DateTime"),
            "dirasakan": self._quake.get("Dirasakan"),
            "shakemap_url": f"{SHAKEMAP_BASE_URL}{shakemap}" if shakemap else None,
        }
