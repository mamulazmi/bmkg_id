"""Tests for BMKG config flow and options flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bmkg_id.api import (
    BmkgApiClientCommunicationError,
    BmkgApiClientError,
)
from custom_components.bmkg_id.const import CONF_ADM4, DOMAIN

from .const import MOCK_ADM4, MOCK_WEATHER_RESPONSE


@pytest.fixture
def mock_api_client():
    """Patch BmkgApiClient and session creation to avoid real HTTP in config flow."""
    with patch("custom_components.bmkg_id.config_flow.BmkgApiClient") as mock_cls, \
         patch("custom_components.bmkg_id.config_flow.async_create_clientsession"):
        instance = mock_cls.return_value
        instance.async_get_forecast = AsyncMock(return_value=MOCK_WEATHER_RESPONSE)
        yield mock_cls, instance


class TestConfigFlowUserStep:
    async def test_success_creates_entry(self, hass, mock_api_client):
        # Patch setup_entry so we only test flow, not full coordinator boot
        with patch("custom_components.bmkg_id.async_setup_entry", return_value=True):
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            assert result["type"] == "form"
            assert result["step_id"] == "user"

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={CONF_ADM4: MOCK_ADM4},
            )
            await hass.async_block_till_done()

        assert result["type"] == "create_entry"
        assert result["data"][CONF_ADM4] == MOCK_ADM4
        assert "Gambir" in result["title"]

    async def test_connection_error_shows_form(self, hass, mock_api_client):
        _, instance = mock_api_client
        instance.async_get_forecast.side_effect = BmkgApiClientCommunicationError("fail")

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_ADM4: MOCK_ADM4},
        )
        assert result["type"] == "form"
        assert result["errors"]["base"] == "connection"

    async def test_unknown_error_shows_form(self, hass, mock_api_client):
        _, instance = mock_api_client
        instance.async_get_forecast.side_effect = BmkgApiClientError("fail")

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_ADM4: MOCK_ADM4},
        )
        assert result["type"] == "form"
        assert result["errors"]["base"] == "unknown"

    async def test_duplicate_adm4_aborts(self, hass, mock_api_client):
        existing = MockConfigEntry(
            domain=DOMAIN,
            data={CONF_ADM4: MOCK_ADM4},
            unique_id=MOCK_ADM4,
        )
        existing.add_to_hass(hass)

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_ADM4: MOCK_ADM4},
        )
        assert result["type"] == "abort"
        assert result["reason"] == "already_configured"


class TestOptionsFlow:
    async def test_change_adm4_success(self, hass, mock_api_client):
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={CONF_ADM4: MOCK_ADM4},
            unique_id=MOCK_ADM4,
        )
        entry.add_to_hass(hass)

        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["type"] == "form"
        assert result["step_id"] == "init"

        new_adm4 = "31.74.01.1001"
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_ADM4: new_adm4},
        )
        assert result["type"] == "create_entry"
        assert entry.data[CONF_ADM4] == new_adm4

    async def test_options_connection_error(self, hass, mock_api_client):
        _, instance = mock_api_client
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={CONF_ADM4: MOCK_ADM4},
            unique_id=MOCK_ADM4,
        )
        entry.add_to_hass(hass)

        result = await hass.config_entries.options.async_init(entry.entry_id)
        instance.async_get_forecast.side_effect = BmkgApiClientCommunicationError("fail")
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_ADM4: "99.99.99.9999"},
        )
        assert result["type"] == "form"
        assert result["errors"]["base"] == "connection"
