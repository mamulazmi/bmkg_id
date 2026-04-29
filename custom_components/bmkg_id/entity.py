"""Base entity for BMKG integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import BmkgDataUpdateCoordinator


class BmkgEntity(CoordinatorEntity[BmkgDataUpdateCoordinator]):
    """Base class for all BMKG entities."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(self, coordinator: BmkgDataUpdateCoordinator) -> None:
        """Initialize entity."""
        super().__init__(coordinator)
        lokasi = coordinator.data.get("lokasi", {})
        adm4 = coordinator.config_entry.data.get("adm4", "unknown")

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, adm4)},
            name=f"BMKG {lokasi.get('desa', adm4)}",
            manufacturer="BMKG",
            model=lokasi.get("kotkab", ""),
            configuration_url="https://www.bmkg.go.id",
        )
