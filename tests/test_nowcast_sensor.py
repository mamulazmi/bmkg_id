"""Tests for BMKG nowcast sensor state and attributes."""

from __future__ import annotations

from unittest.mock import MagicMock

from custom_components.bmkg_id.nowcast_sensor import NOWCAST_SENSOR_DESCRIPTIONS, BmkgNowcastSensor


def _make_sensor(key: str, coordinator_data: dict) -> BmkgNowcastSensor:
    desc = next(d for d in NOWCAST_SENSOR_DESCRIPTIONS if d.key == key)
    coordinator = MagicMock()
    coordinator.data = coordinator_data
    sensor = BmkgNowcastSensor.__new__(BmkgNowcastSensor)
    sensor.coordinator = coordinator
    sensor.entity_description = desc
    return sensor


class TestNativeValueTruncation:
    LONG_DESC = "A" * 300  # 300 chars > 255 HA state limit

    def test_description_truncated_to_255(self):
        warning = {"title": "Test", "description": self.LONG_DESC, "cap_code": "X"}
        sensor = _make_sensor("warning_province_description", {"latest_province": warning})
        value = sensor.native_value
        assert value is not None
        assert len(str(value)) <= 255

    def test_title_short_not_truncated(self):
        warning = {"title": "Hujan di Jakarta", "description": "short"}
        sensor = _make_sensor("warning_province_title", {"latest_province": warning})
        assert sensor.native_value == "Hujan di Jakarta"

    def test_no_warning_returns_empty(self):
        sensor = _make_sensor("warning_province_description", {"latest_province": None})
        assert sensor.native_value == ""

    def test_no_data_returns_none(self):
        sensor = _make_sensor("warning_province_description", None)
        assert sensor.native_value is None

    def test_title_exactly_255_passes_through(self):
        title = "B" * 255
        warning = {"title": title, "description": ""}
        sensor = _make_sensor("warning_province_title", {"latest_province": warning})
        assert sensor.native_value == title

    def test_title_256_truncated(self):
        title = "C" * 256
        warning = {"title": title, "description": ""}
        sensor = _make_sensor("warning_province_title", {"latest_province": warning})
        assert len(sensor.native_value) == 255
