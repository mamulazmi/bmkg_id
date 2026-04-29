"""Earthquake sensors for BMKG integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfLength
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .earthquake_coordinator import BmkgEarthquakeCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import BmkgConfigEntry


@dataclass(frozen=True)
class BmkgEarthquakeSensorDescription(SensorEntityDescription):
    """Describe a BMKG earthquake sensor."""

    quake_source: str = "nearest"  # "nearest" or "latest"
    quake_key: str = ""


EARTHQUAKE_SENSOR_DESCRIPTIONS: tuple[BmkgEarthquakeSensorDescription, ...] = (
    # --- Nearest to HA location ---
    BmkgEarthquakeSensorDescription(
        key="nearest_magnitude",
        name="Nearest Earthquake Magnitude",
        quake_source="nearest",
        quake_key="Magnitude",
        icon="mdi:magnitude",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BmkgEarthquakeSensorDescription(
        key="nearest_distance",
        name="Nearest Earthquake Distance",
        quake_source="nearest",
        quake_key="_distance_km",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BmkgEarthquakeSensorDescription(
        key="nearest_depth",
        name="Nearest Earthquake Depth",
        quake_source="nearest",
        quake_key="Kedalaman",
        icon="mdi:arrow-collapse-down",
    ),
    BmkgEarthquakeSensorDescription(
        key="nearest_location",
        name="Nearest Earthquake Location",
        quake_source="nearest",
        quake_key="Wilayah",
        icon="mdi:map-marker",
    ),
    BmkgEarthquakeSensorDescription(
        key="nearest_felt",
        name="Nearest Earthquake Felt",
        quake_source="nearest",
        quake_key="Dirasakan",
        icon="mdi:home-alert",
    ),
    # --- Latest (most recent) ---
    BmkgEarthquakeSensorDescription(
        key="latest_magnitude",
        name="Latest Earthquake Magnitude",
        quake_source="latest",
        quake_key="Magnitude",
        icon="mdi:magnitude",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BmkgEarthquakeSensorDescription(
        key="latest_location",
        name="Latest Earthquake Location",
        quake_source="latest",
        quake_key="Wilayah",
        icon="mdi:map-marker",
    ),
    BmkgEarthquakeSensorDescription(
        key="latest_felt",
        name="Latest Earthquake Felt",
        quake_source="latest",
        quake_key="Dirasakan",
        icon="mdi:home-alert",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BmkgConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BMKG earthquake sensors."""
    coordinator = entry.runtime_data.earthquake_coordinator
    adm4 = entry.data.get("adm4", "unknown")
    async_add_entities(
        BmkgEarthquakeSensor(
            coordinator=coordinator,
            description=description,
            adm4=adm4,
        )
        for description in EARTHQUAKE_SENSOR_DESCRIPTIONS
    )


class BmkgEarthquakeSensor(CoordinatorEntity[BmkgEarthquakeCoordinator], SensorEntity):
    """A BMKG earthquake sensor."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    entity_description: BmkgEarthquakeSensorDescription

    def __init__(
        self,
        coordinator: BmkgEarthquakeCoordinator,
        description: BmkgEarthquakeSensorDescription,
        adm4: str,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{adm4}_eq_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, adm4)},
        )

    def _get_quake(self) -> dict[str, Any] | None:
        return self.coordinator.data.get(self.entity_description.quake_source)

    @property
    def native_value(self) -> Any:
        """Return sensor value."""
        quake = self._get_quake()
        if quake is None:
            return None
        val = quake.get(self.entity_description.quake_key)
        # Magnitude and distance returned as float when possible
        if self.entity_description.quake_key in ("Magnitude", "_distance_km"):
            try:
                return float(val)
            except (TypeError, ValueError):
                return val
        return val

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return full quake details as attributes."""
        quake = self._get_quake()
        if quake is None:
            return {}
        attrs: dict[str, Any] = {
            "datetime": quake.get("DateTime"),
            "tanggal": quake.get("Tanggal"),
            "jam": quake.get("Jam"),
            "coordinates": quake.get("Coordinates"),
            "lintang": quake.get("Lintang"),
            "bujur": quake.get("Bujur"),
            "magnitude": quake.get("Magnitude"),
            "kedalaman": quake.get("Kedalaman"),
            "wilayah": quake.get("Wilayah"),
            "dirasakan": quake.get("Dirasakan"),
        }
        if "_distance_km" in quake:
            attrs["distance_from_ha_km"] = quake["_distance_km"]
        if "_shakemap_url" in quake:
            attrs["shakemap_url"] = quake["_shakemap_url"]
        return attrs
