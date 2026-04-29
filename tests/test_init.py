"""Tests for BMKG integration setup and teardown."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bmkg_id.const import CONF_ADM4, DOMAIN

from .const import MOCK_ADM4


async def test_setup_entry_success(hass, setup_integration):
    """Test successful setup creates config entry in loaded state."""
    entry = setup_integration
    assert entry.state == ConfigEntryState.LOADED


async def test_setup_entry_loads_sensors(hass, setup_integration):
    """Test that sensor entities are created after setup."""
    states = hass.states.async_all()
    bmkg_states = [s for s in states if s.entity_id.startswith("sensor.bmkg")]
    assert len(bmkg_states) > 0


async def test_unload_entry(hass, setup_integration):
    """Test config entry unloads cleanly."""
    entry = setup_integration
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state == ConfigEntryState.NOT_LOADED


async def test_setup_entry_weather_api_failure(hass, mock_config_entry, aioclient_mock):
    """Test setup raises ConfigEntryNotReady when weather API fails."""
    from custom_components.bmkg_id.const import BMKG_API_URL

    aioclient_mock.get(BMKG_API_URL, exc=Exception("connection failed"))
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # UpdateFailed from first_refresh causes SETUP_RETRY (HA retries coordinator errors)
    assert mock_config_entry.state == ConfigEntryState.SETUP_RETRY


async def test_reload_entry(hass, setup_integration, mock_all_apis):
    """Test that reloading entry works without errors."""
    entry = setup_integration
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state == ConfigEntryState.LOADED
