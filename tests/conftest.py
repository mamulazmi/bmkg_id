"""Fixtures for BMKG integration tests."""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bmkg_id.const import (
    BMKG_API_URL,
    BMKG_EARTHQUAKE_URL,
    BMKG_NOWCAST_RSS_URL,
    CONF_ADM4,
    DOMAIN,
)

from .const import (
    MOCK_ADM4,
    MOCK_HA_LAT,
    MOCK_HA_LON,
    MOCK_RSS_XML,
    MOCK_WEATHER_RESPONSE,
    MOCK_EARTHQUAKE_RESPONSE,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield




@pytest.fixture(autouse=True)
def set_hass_location(hass):
    """Set HA home coordinates to Jakarta mock location so earthquake distance works."""
    hass.config.latitude = MOCK_HA_LAT
    hass.config.longitude = MOCK_HA_LON


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_ADM4: MOCK_ADM4},
        title="BMKG Gambir",
    )


@pytest.fixture
def mock_weather_api(aioclient_mock):
    """Mock BMKG weather forecast API."""
    aioclient_mock.get(BMKG_API_URL, json=MOCK_WEATHER_RESPONSE)


@pytest.fixture
def mock_earthquake_api(aioclient_mock):
    """Mock BMKG earthquake API."""
    aioclient_mock.get(BMKG_EARTHQUAKE_URL, json=MOCK_EARTHQUAKE_RESPONSE)


@pytest.fixture
def mock_nowcast_api(aioclient_mock):
    """Mock BMKG nowcast RSS feed."""
    aioclient_mock.get(BMKG_NOWCAST_RSS_URL, text=MOCK_RSS_XML)


@pytest.fixture
def mock_all_apis(mock_weather_api, mock_earthquake_api, mock_nowcast_api):
    """Mock all three BMKG APIs at once."""


@pytest.fixture
async def setup_integration(hass, mock_config_entry, mock_all_apis):
    """Set up BMKG integration with all APIs mocked."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry
