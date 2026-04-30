"""Weather warning (nowcast) sensors for BMKG integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .nowcast_coordinator import BmkgNowcastCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import BmkgConfigEntry


@dataclass(frozen=True)
class BmkgNowcastSensorDescription(SensorEntityDescription):
    """Describe a BMKG nowcast sensor."""

    data_key: str = ""
    warning_source: str = ""  # "province" or "all"


NOWCAST_SENSOR_DESCRIPTIONS: tuple[BmkgNowcastSensorDescription, ...] = (
    BmkgNowcastSensorDescription(
        key="warning_province_count",
        name="Active Warnings (Province)",
        data_key="province_warning_count",
        icon="mdi:weather-lightning-rainy",
    ),
    BmkgNowcastSensorDescription(
        key="warning_total_count",
        name="Active Warnings (National)",
        data_key="total_warning_count",
        icon="mdi:weather-lightning-rainy",
    ),
    BmkgNowcastSensorDescription(
        key="warning_province_title",
        name="Province Warning Title",
        data_key="title",
        warning_source="latest_province",
        icon="mdi:alert-circle",
    ),
    BmkgNowcastSensorDescription(
        key="warning_province_description",
        name="Province Warning Description",
        data_key="description",
        warning_source="latest_province",
        icon="mdi:text-box-outline",
    ),
    BmkgNowcastSensorDescription(
        key="warning_latest_title",
        name="Latest National Warning Title",
        data_key="title",
        warning_source="latest_all",
        icon="mdi:alert-circle-outline",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BmkgConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BMKG nowcast sensors."""
    coordinator = entry.runtime_data.nowcast_coordinator
    adm4 = entry.data.get("adm4", "unknown")
    async_add_entities(
        BmkgNowcastSensor(coordinator=coordinator, description=desc, adm4=adm4)
        for desc in NOWCAST_SENSOR_DESCRIPTIONS
    )


class BmkgNowcastSensor(CoordinatorEntity[BmkgNowcastCoordinator], SensorEntity):
    """A BMKG nowcast warning sensor."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    entity_description: BmkgNowcastSensorDescription

    def __init__(
        self,
        coordinator: BmkgNowcastCoordinator,
        description: BmkgNowcastSensorDescription,
        adm4: str,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{adm4}_nowcast_{description.key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, adm4)})

    @property
    def native_value(self) -> Any:
        """Return sensor value."""
        data = self.coordinator.data
        if not data:
            return None

        # Count sensors — direct key
        if not self.entity_description.warning_source:
            return data.get(self.entity_description.data_key)

        # Warning-detail sensors — drill into warning dict
        warning = data.get(self.entity_description.warning_source)
        if warning is None:
            return ""
        return warning.get(self.entity_description.data_key) or ""

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return full warning details as attributes."""
        data = self.coordinator.data
        if not data:
            return {}

        source = self.entity_description.warning_source
        if not source:
            # Count sensor: expose province name and all province warning titles
            province_warnings = data.get("province_warnings", [])
            return {
                "province": data.get("province"),
                "province_warning_titles": [w.get("title") for w in province_warnings],
            }

        warning = data.get(source)
        if not warning:
            return {}
        return {
            "title": warning.get("title"),
            "description": warning.get("description"),
            "author": warning.get("author"),
            "pub_date": warning.get("pub_date"),
            "cap_code": warning.get("cap_code"),
            "link": warning.get("link"),
            "event": warning.get("event"),
            "headline": warning.get("headline"),
            "cap_description": warning.get("cap_description"),
            "severity": warning.get("severity"),
            "urgency": warning.get("urgency"),
            "certainty": warning.get("certainty"),
            "effective": warning.get("effective"),
            "expires": warning.get("expires"),
            "sender_name": warning.get("sender_name"),
            "web": warning.get("web"),
            "area_desc": warning.get("area_desc"),
            "polygon": warning.get("polygon"),
        }
