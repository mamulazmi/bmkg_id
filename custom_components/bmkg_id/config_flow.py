"""Config flow for BMKG Weather integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import BmkgApiClient, BmkgApiClientCommunicationError, BmkgApiClientError
from .const import (
    CONF_ADM4,
    CONF_NOWCAST_INTERVAL,
    CONF_NOWCAST_LANGUAGE,
    DEFAULT_NOWCAST_LANGUAGE,
    DEFAULT_NOWCAST_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    LOGGER,
    MAX_NOWCAST_UPDATE_INTERVAL_MINUTES,
    MIN_NOWCAST_UPDATE_INTERVAL_MINUTES,
)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ADM4): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
        ),
    }
)


class BmkgConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for BMKG Weather."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            adm4 = user_input[CONF_ADM4].strip()
            try:
                client = BmkgApiClient(
                    adm4=adm4,
                    session=async_create_clientsession(self.hass),
                )
                data = await client.async_get_forecast()
                lokasi = data.get("lokasi", {})
                desa = lokasi.get("desa", adm4)
            except BmkgApiClientCommunicationError:
                errors["base"] = "connection"
            except BmkgApiClientError:
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(adm4)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"BMKG {desa}",
                    data={CONF_ADM4: adm4},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
            description_placeholders={
                "example_adm4": "63.71.04.1006",
            },
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> BmkgOptionsFlow:
        """Return options flow."""
        return BmkgOptionsFlow(config_entry)


class BmkgOptionsFlow(config_entries.OptionsFlow):
    """Handle options for BMKG (change adm4 code)."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle options update."""
        errors: dict[str, str] = {}
        current_adm4 = self._config_entry.data.get(CONF_ADM4, "")

        if user_input is not None:
            adm4 = user_input[CONF_ADM4].strip()
            try:
                client = BmkgApiClient(
                    adm4=adm4,
                    session=async_create_clientsession(self.hass),
                )
                await client.async_get_forecast()
            except BmkgApiClientCommunicationError:
                errors["base"] = "connection"
            except BmkgApiClientError:
                errors["base"] = "unknown"
            else:
                self.hass.config_entries.async_update_entry(
                    self._config_entry,
                    data={CONF_ADM4: adm4},
                )
                return self.async_create_entry(title="", data={
                    CONF_NOWCAST_LANGUAGE: user_input.get(CONF_NOWCAST_LANGUAGE, DEFAULT_NOWCAST_LANGUAGE),
                    CONF_NOWCAST_INTERVAL: user_input.get(CONF_NOWCAST_INTERVAL, DEFAULT_NOWCAST_UPDATE_INTERVAL_MINUTES),
                })

        current_language = self._config_entry.options.get(CONF_NOWCAST_LANGUAGE, DEFAULT_NOWCAST_LANGUAGE)
        current_interval = self._config_entry.options.get(CONF_NOWCAST_INTERVAL, DEFAULT_NOWCAST_UPDATE_INTERVAL_MINUTES)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADM4, default=current_adm4): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                    ),
                    vol.Optional(CONF_NOWCAST_LANGUAGE, default=current_language): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=["id", "en"],
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    ),
                    vol.Optional(CONF_NOWCAST_INTERVAL, default=current_interval): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=MIN_NOWCAST_UPDATE_INTERVAL_MINUTES,
                            max=MAX_NOWCAST_UPDATE_INTERVAL_MINUTES,
                            step=5,
                            unit_of_measurement="minutes",
                            mode=selector.NumberSelectorMode.SLIDER,
                        )
                    ),
                }
            ),
            errors=errors,
        )
