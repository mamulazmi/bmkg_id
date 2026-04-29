"""Weather platform for BMKG integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.const import (
    UnitOfPrecipitationDepth,
    UnitOfSpeed,
    UnitOfTemperature,
)

from .entity import BmkgEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import BmkgConfigEntry

BMKG_CONDITION_MAP: dict[int, str] = {
    0: "sunny",
    1: "partlycloudy",
    2: "partlycloudy",
    3: "cloudy",
    4: "cloudy",
    5: "fog",
    10: "exceptional",
    45: "fog",
    60: "rainy",
    61: "rainy",
    63: "pouring",
    80: "rainy",
    95: "lightning-rainy",
    97: "lightning-rainy",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BmkgConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BMKG weather entity."""
    async_add_entities([BmkgWeatherEntity(entry.runtime_data.coordinator)])


class BmkgWeatherEntity(BmkgEntity, WeatherEntity):
    """BMKG weather entity — exposes current conditions and 3-hourly forecasts."""

    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS
    _attr_supported_features = WeatherEntityFeature.FORECAST_HOURLY
    _attr_name = None  # device name is the entity name

    def __init__(self, coordinator) -> None:
        """Initialize weather entity."""
        super().__init__(coordinator)
        adm4 = coordinator.config_entry.data.get("adm4", "unknown")
        self._attr_unique_id = f"{adm4}_weather"

    @property
    def condition(self) -> str | None:
        """Return HA condition string mapped from BMKG weather code."""
        code = (self.coordinator.data.get("current") or {}).get("weather")
        return BMKG_CONDITION_MAP.get(code)

    @property
    def native_temperature(self) -> float | None:
        """Return current temperature."""
        return (self.coordinator.data.get("current") or {}).get("t")

    @property
    def humidity(self) -> float | None:
        """Return current humidity."""
        return (self.coordinator.data.get("current") or {}).get("hu")

    @property
    def native_wind_speed(self) -> float | None:
        """Return current wind speed in km/h."""
        return (self.coordinator.data.get("current") or {}).get("ws")

    @property
    def wind_bearing(self) -> float | None:
        """Return wind bearing in degrees."""
        return (self.coordinator.data.get("current") or {}).get("wd_deg")

    @property
    def cloud_coverage(self) -> int | None:
        """Return total cloud cover percentage."""
        return (self.coordinator.data.get("current") or {}).get("tcc")

    @property
    def native_visibility(self) -> float | None:
        """Return visibility in meters."""
        return (self.coordinator.data.get("current") or {}).get("vs")

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        """Return 3-hourly forecast list."""
        result = [
            Forecast(
                datetime=f.get("datetime", ""),
                condition=BMKG_CONDITION_MAP.get(f.get("weather")),
                native_temperature=f.get("t"),
                humidity=f.get("hu"),
                native_precipitation=f.get("tp"),
                native_wind_speed=f.get("ws"),
                wind_bearing=f.get("wd_deg"),
                cloud_coverage=f.get("tcc"),
            )
            for f in self.coordinator.data.get("forecasts", [])
        ]
        return result or None
