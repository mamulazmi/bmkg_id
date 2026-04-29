"""Sensor platform for BMKG Weather (weather + earthquake)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    DEGREE,
    PERCENTAGE,
    UnitOfLength,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfVolumetricFlux,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .earthquake_sensor import (
    EARTHQUAKE_SENSOR_DESCRIPTIONS,
    BmkgEarthquakeSensor,
)
from .entity import BmkgEntity
from .nowcast_sensor import NOWCAST_SENSOR_DESCRIPTIONS, BmkgNowcastSensor

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import BmkgDataUpdateCoordinator
    from .data import BmkgConfigEntry


@dataclass(frozen=True)
class BmkgSensorEntityDescription(SensorEntityDescription):
    """Describe a BMKG weather sensor."""

    forecast_key: str = ""


SENSOR_DESCRIPTIONS: tuple[BmkgSensorEntityDescription, ...] = (
    BmkgSensorEntityDescription(
        key="temperature",
        name="Temperature",
        forecast_key="t",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BmkgSensorEntityDescription(
        key="humidity",
        name="Humidity",
        forecast_key="hu",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BmkgSensorEntityDescription(
        key="wind_speed",
        name="Wind Speed",
        forecast_key="ws",
        # BMKG ws field is in km/h
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BmkgSensorEntityDescription(
        key="wind_direction",
        name="Wind Direction",
        forecast_key="wd_deg",
        native_unit_of_measurement=DEGREE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:compass",
    ),
    BmkgSensorEntityDescription(
        key="precipitation",
        name="Precipitation",
        forecast_key="tp",
        native_unit_of_measurement=UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR,
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BmkgSensorEntityDescription(
        key="cloud_cover",
        name="Cloud Cover",
        forecast_key="tcc",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-cloudy",
    ),
    BmkgSensorEntityDescription(
        key="visibility",
        name="Visibility",
        forecast_key="vs",
        native_unit_of_measurement=UnitOfLength.METERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BmkgSensorEntityDescription(
        key="weather_condition",
        name="Weather Condition",
        forecast_key="weather_desc_en",
        icon="mdi:weather-partly-cloudy",
    ),
    BmkgSensorEntityDescription(
        key="weather_condition_id",
        name="Weather Code",
        forecast_key="weather",
        icon="mdi:numeric",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BmkgConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BMKG weather + earthquake sensors."""
    adm4 = entry.data.get("adm4", "unknown")

    weather_entities = [
        BmkgSensor(coordinator=entry.runtime_data.coordinator, description=desc)
        for desc in SENSOR_DESCRIPTIONS
    ]

    earthquake_entities = [
        BmkgEarthquakeSensor(
            coordinator=entry.runtime_data.earthquake_coordinator,
            description=desc,
            adm4=adm4,
        )
        for desc in EARTHQUAKE_SENSOR_DESCRIPTIONS
    ]

    nowcast_entities = [
        BmkgNowcastSensor(
            coordinator=entry.runtime_data.nowcast_coordinator,
            description=desc,
            adm4=adm4,
        )
        for desc in NOWCAST_SENSOR_DESCRIPTIONS
    ]

    async_add_entities(weather_entities + earthquake_entities + nowcast_entities)


class BmkgSensor(BmkgEntity, SensorEntity):
    """A BMKG forecast sensor."""

    entity_description: BmkgSensorEntityDescription

    def __init__(
        self,
        coordinator: BmkgDataUpdateCoordinator,
        description: BmkgSensorEntityDescription,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        adm4 = coordinator.config_entry.data.get("adm4", "unknown")
        self._attr_unique_id = f"{adm4}_{description.key}"

    @property
    def native_value(self) -> Any:
        """Return current forecast value."""
        current = self.coordinator.data.get("current") or {}
        return current.get(self.entity_description.forecast_key)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes from current forecast."""
        current = self.coordinator.data.get("current") or {}
        lokasi = self.coordinator.data.get("lokasi") or {}
        return {
            "utc_datetime": current.get("datetime"),
            "local_datetime": current.get("local_datetime"),
            "analysis_date": current.get("analysis_date"),
            "weather_desc": current.get("weather_desc"),
            "weather_icon": current.get("image"),
            "wind_direction_from": current.get("wd"),
            "visibility_text": current.get("vs_text"),
            "provinsi": lokasi.get("provinsi"),
            "kotkab": lokasi.get("kotkab"),
            "kecamatan": lokasi.get("kecamatan"),
            "desa": lokasi.get("desa"),
            "latitude": lokasi.get("lat"),
            "longitude": lokasi.get("lon"),
        }
