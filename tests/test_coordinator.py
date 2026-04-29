"""Tests for all three BMKG coordinators and sensor state validation."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.bmkg_id.api import (
    BmkgApiClientCommunicationError,
    BmkgApiClientError,
)

from .const import (
    MOCK_ADM4,
    MOCK_HA_LAT,
    MOCK_HA_LON,
    MOCK_EARTHQUAKE_RESPONSE,
    MOCK_WEATHER_RESPONSE,
    MOCK_RSS_XML,
)


# ---------------------------------------------------------------------------
# BmkgDataUpdateCoordinator
# ---------------------------------------------------------------------------


class TestWeatherCoordinator:
    async def test_update_success_returns_correct_keys(self, hass, setup_integration):
        """Coordinator data must have lokasi, current, forecasts keys."""
        entry = setup_integration
        coordinator = entry.runtime_data.coordinator
        data = coordinator.data

        assert "lokasi" in data
        assert "current" in data
        assert "forecasts" in data

    async def test_current_forecast_values(self, hass, setup_integration):
        """Current forecast must match mock response values."""
        entry = setup_integration
        data = entry.runtime_data.coordinator.data
        current = data["current"]

        assert current["t"] == 30
        assert current["hu"] == 80
        assert current["weather_desc_en"] == "Partly Cloudy"

    async def test_lokasi_province(self, hass, setup_integration):
        """lokasi.provinsi must match mock data."""
        entry = setup_integration
        lokasi = entry.runtime_data.coordinator.data["lokasi"]
        assert lokasi["provinsi"] == "DKI Jakarta"

    async def test_comm_error_raises_update_failed(self, hass, mock_config_entry):
        """Communication error during refresh must raise UpdateFailed."""
        from custom_components.bmkg_id.coordinator import BmkgDataUpdateCoordinator
        from custom_components.bmkg_id.api import BmkgApiClient, BmkgEarthquakeApiClient, BmkgNowcastApiClient
        from custom_components.bmkg_id.data import BmkgData
        from custom_components.bmkg_id.earthquake_coordinator import BmkgEarthquakeCoordinator
        from custom_components.bmkg_id.nowcast_coordinator import BmkgNowcastCoordinator

        coordinator = BmkgDataUpdateCoordinator(hass=hass)

        mock_client = MagicMock(spec=BmkgApiClient)
        mock_client.async_get_forecast = AsyncMock(
            side_effect=BmkgApiClientCommunicationError("timeout")
        )

        mock_config_entry.add_to_hass(hass)
        mock_config_entry.runtime_data = BmkgData(
            client=mock_client,
            coordinator=coordinator,
            earthquake_client=MagicMock(spec=BmkgEarthquakeApiClient),
            earthquake_coordinator=MagicMock(spec=BmkgEarthquakeCoordinator),
            nowcast_client=MagicMock(spec=BmkgNowcastApiClient),
            nowcast_coordinator=MagicMock(spec=BmkgNowcastCoordinator),
        )
        coordinator.config_entry = mock_config_entry

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    async def test_general_api_error_raises_update_failed(self, hass, mock_config_entry):
        """General API error must raise UpdateFailed (not ConfigEntryNotReady)."""
        from custom_components.bmkg_id.coordinator import BmkgDataUpdateCoordinator
        from custom_components.bmkg_id.api import BmkgApiClient, BmkgEarthquakeApiClient, BmkgNowcastApiClient
        from custom_components.bmkg_id.data import BmkgData
        from custom_components.bmkg_id.earthquake_coordinator import BmkgEarthquakeCoordinator
        from custom_components.bmkg_id.nowcast_coordinator import BmkgNowcastCoordinator

        coordinator = BmkgDataUpdateCoordinator(hass=hass)
        mock_client = MagicMock(spec=BmkgApiClient)
        mock_client.async_get_forecast = AsyncMock(
            side_effect=BmkgApiClientError("unexpected")
        )

        mock_config_entry.add_to_hass(hass)
        mock_config_entry.runtime_data = BmkgData(
            client=mock_client,
            coordinator=coordinator,
            earthquake_client=MagicMock(spec=BmkgEarthquakeApiClient),
            earthquake_coordinator=MagicMock(spec=BmkgEarthquakeCoordinator),
            nowcast_client=MagicMock(spec=BmkgNowcastApiClient),
            nowcast_coordinator=MagicMock(spec=BmkgNowcastCoordinator),
        )
        coordinator.config_entry = mock_config_entry

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()


# ---------------------------------------------------------------------------
# BmkgEarthquakeCoordinator
# ---------------------------------------------------------------------------


class TestEarthquakeCoordinator:
    async def test_nearest_has_distance(self, hass, setup_integration):
        """Nearest earthquake must have _distance_km computed."""
        entry = setup_integration
        data = entry.runtime_data.earthquake_coordinator.data
        nearest = data["nearest"]

        assert nearest is not None
        assert "_distance_km" in nearest
        assert isinstance(nearest["_distance_km"], float)

    async def test_nearest_is_closest_to_ha(self, hass, setup_integration):
        """First mock quake (-6.20,106.85) is closer to Jakarta HA than second."""
        entry = setup_integration
        data = entry.runtime_data.earthquake_coordinator.data
        nearest = data["nearest"]

        # First quake is near Jakarta (-6.20,106.85), HA set to (-6.2088,106.8456)
        assert nearest["Magnitude"] == "3.5"
        # Distance should be <15 km (not Tasikmalaya ~230 km away)
        assert nearest["_distance_km"] < 15

    async def test_latest_is_first_in_list(self, hass, setup_integration):
        """Latest earthquake must be first item from API (newest first)."""
        entry = setup_integration
        data = entry.runtime_data.earthquake_coordinator.data
        assert data["latest"]["Magnitude"] == "3.5"

    async def test_shakemap_url_built_correctly(self, hass, setup_integration):
        """Shakemap URL must be static.bmkg.go.id/{Shakemap}."""
        entry = setup_integration
        nearest = entry.runtime_data.earthquake_coordinator.data["nearest"]
        assert nearest["_shakemap_url"] == (
            "https://static.bmkg.go.id/20260429170904.mmi.jpg"
        )

    async def test_ha_coordinates_stored(self, hass, setup_integration):
        """Coordinator must store HA lat/lon for reference."""
        entry = setup_integration
        data = entry.runtime_data.earthquake_coordinator.data
        assert data["ha_lat"] == hass.config.latitude
        assert data["ha_lon"] == hass.config.longitude


# ---------------------------------------------------------------------------
# BmkgNowcastCoordinator
# ---------------------------------------------------------------------------


class TestNowcastCoordinator:
    async def test_province_filter_applied(self, hass, setup_integration):
        """province_warnings must only contain warnings for lokasi.provinsi."""
        entry = setup_integration
        data = entry.runtime_data.nowcast_coordinator.data
        province_warnings = data["province_warnings"]

        # Mock has "DKI Jakarta" warning + "Jawa Tengah" warning
        # lokasi.provinsi = "DKI Jakarta" → only 1 match
        assert data["province_warning_count"] == 1
        assert "DKI Jakarta" in province_warnings[0]["title"]

    async def test_total_warning_count(self, hass, setup_integration):
        """total_warning_count must reflect all RSS items."""
        data = setup_integration.runtime_data.nowcast_coordinator.data
        assert data["total_warning_count"] == 2

    async def test_latest_province_title(self, hass, setup_integration):
        """latest_province must be the first province-matching warning."""
        data = setup_integration.runtime_data.nowcast_coordinator.data
        assert data["latest_province"]["title"] == "Hujan Lebat di DKI Jakarta"

    async def test_province_name_stored(self, hass, setup_integration):
        """province key must come from weather coordinator lokasi."""
        data = setup_integration.runtime_data.nowcast_coordinator.data
        assert data["province"] == "DKI Jakarta"


# ---------------------------------------------------------------------------
# Sensor state validation via hass.states
# ---------------------------------------------------------------------------


class TestSensorStates:
    async def test_temperature_sensor_state(self, hass, setup_integration):
        state = hass.states.get(f"sensor.bmkg_gambir_temperature")
        assert state is not None
        assert state.state == "30"

    async def test_humidity_sensor_state(self, hass, setup_integration):
        state = hass.states.get(f"sensor.bmkg_gambir_humidity")
        assert state is not None
        assert state.state == "80"

    async def test_wind_speed_unit(self, hass, setup_integration):
        state = hass.states.get(f"sensor.bmkg_gambir_wind_speed")
        assert state is not None
        assert state.attributes.get("unit_of_measurement") == "km/h"

    async def test_earthquake_magnitude_sensor(self, hass, setup_integration):
        state = hass.states.get(
            f"sensor.bmkg_gambir_nearest_earthquake_magnitude"
        )
        assert state is not None
        assert float(state.state) == pytest.approx(3.5)

    async def test_nowcast_province_count_sensor(self, hass, setup_integration):
        state = hass.states.get(
            f"sensor.bmkg_gambir_active_warnings_province"
        )
        assert state is not None
        assert state.state == "1"
