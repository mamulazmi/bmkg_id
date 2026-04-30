"""Binary sensor: HA home coordinate inside active BMKG alert polygon."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .nowcast_coordinator import BmkgNowcastCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import BmkgConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BmkgConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BMKG home-in-alert binary sensor."""
    async_add_entities([
        BmkgHomeAlertSensor(
            coordinator=entry.runtime_data.nowcast_coordinator,
            adm4=entry.data["adm4"],
        )
    ])


class BmkgHomeAlertSensor(CoordinatorEntity[BmkgNowcastCoordinator], BinarySensorEntity):
    """Binary sensor: True when HA home coordinates are inside an active alert polygon."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_name = "Home in Alert Area"
    _attr_device_class = BinarySensorDeviceClass.SAFETY
    _attr_icon = "mdi:home-alert"

    def __init__(self, coordinator: BmkgNowcastCoordinator, adm4: str) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{adm4}_home_in_alert_area"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, adm4)})

    @property
    def is_on(self) -> bool:
        """Return True if home is inside an active alert polygon."""
        return bool((self.coordinator.data or {}).get("home_in_alert"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return alert details when active."""
        alert = (self.coordinator.data or {}).get("home_alert")
        if not alert:
            return {}
        return {
            "title": alert.get("title"),
            "event": alert.get("event"),
            "severity": alert.get("severity"),
            "effective": alert.get("effective"),
            "expires": alert.get("expires"),
            "area_desc": alert.get("area_desc"),
            "web": alert.get("web"),
            "cap_code": alert.get("cap_code"),
        }
