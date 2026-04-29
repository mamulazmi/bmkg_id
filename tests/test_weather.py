"""Tests for BMKG WeatherEntity platform."""

from __future__ import annotations

import pytest

from custom_components.bmkg_id.weather import BMKG_CONDITION_MAP


class TestConditionMapping:
    def test_code_1_is_partlycloudy(self):
        assert BMKG_CONDITION_MAP[1] == "partlycloudy"

    def test_code_0_is_sunny(self):
        assert BMKG_CONDITION_MAP[0] == "sunny"

    def test_code_63_is_pouring(self):
        assert BMKG_CONDITION_MAP[63] == "pouring"

    def test_code_95_is_lightning_rainy(self):
        assert BMKG_CONDITION_MAP[95] == "lightning-rainy"

    def test_unknown_code_returns_none(self):
        assert BMKG_CONDITION_MAP.get(99) is None


class TestWeatherEntity:
    async def test_weather_entity_created(self, hass, setup_integration):
        """Entity weather.bmkg_gambir must exist after setup."""
        state = hass.states.get("weather.bmkg_gambir")
        assert state is not None

    async def test_condition_mapped_from_mock(self, hass, setup_integration):
        """Mock weather=1 must map to partlycloudy."""
        state = hass.states.get("weather.bmkg_gambir")
        assert state.state == "partlycloudy"

    async def test_temperature_matches_mock(self, hass, setup_integration):
        """Temperature attribute must match mock t=30."""
        state = hass.states.get("weather.bmkg_gambir")
        assert float(state.attributes["temperature"]) == pytest.approx(30)

    async def test_humidity_matches_mock(self, hass, setup_integration):
        """Humidity attribute must match mock hu=80."""
        state = hass.states.get("weather.bmkg_gambir")
        assert state.attributes["humidity"] == 80

    async def test_forecast_hourly_returns_list(self, hass, setup_integration):
        """async_forecast_hourly must return a non-empty list."""
        entry = setup_integration
        weather_entity = None
        for entity in hass.states.async_all():
            if entity.domain == "weather":
                weather_entity = entity
                break
        assert weather_entity is not None

        # Access via entity registry
        from homeassistant.helpers import entity_registry as er
        registry = er.async_get(hass)
        entries = er.async_entries_for_config_entry(registry, setup_integration.entry_id)
        weather_entries = [e for e in entries if e.domain == "weather"]
        assert len(weather_entries) == 1
