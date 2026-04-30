"""Tests for BMKG home-in-alert binary sensor."""

from __future__ import annotations

from unittest.mock import MagicMock

from custom_components.bmkg_id.binary_sensor import BmkgHomeAlertSensor
from custom_components.bmkg_id.const import DOMAIN


def _make_sensor(coordinator_data: dict | None) -> BmkgHomeAlertSensor:
    coordinator = MagicMock()
    coordinator.data = coordinator_data
    sensor = BmkgHomeAlertSensor.__new__(BmkgHomeAlertSensor)
    sensor.coordinator = coordinator
    sensor._attr_unique_id = "test_home_in_alert"
    sensor._attr_device_info = MagicMock()
    return sensor


MOCK_ALERT = {
    "title": "Hujan Lebat di Kalimantan Selatan",
    "event": "Hujan Lebat dan Petir",
    "severity": "Moderate",
    "effective": "2026-04-30T08:30:00+07:00",
    "expires": "2026-04-30T10:30:00+07:00",
    "area_desc": "Kalimantan Selatan",
    "web": "https://nowcasting.bmkg.go.id/infografis/CKS/2026/04/30/infografis.jpg",
    "cap_code": "CKS20260430001",
}


class TestBmkgHomeAlertSensor:
    def test_is_on_when_home_in_alert(self):
        sensor = _make_sensor({"home_in_alert": True, "home_alert": MOCK_ALERT})
        assert sensor.is_on is True

    def test_is_off_when_not_in_alert(self):
        sensor = _make_sensor({"home_in_alert": False, "home_alert": None})
        assert sensor.is_on is False

    def test_is_off_when_no_data(self):
        sensor = _make_sensor({})
        assert sensor.is_on is False

    def test_is_off_when_data_is_none(self):
        sensor = _make_sensor(None)
        assert sensor.is_on is False

    def test_attributes_when_active(self):
        sensor = _make_sensor({"home_in_alert": True, "home_alert": MOCK_ALERT})
        attrs = sensor.extra_state_attributes
        assert attrs["event"] == "Hujan Lebat dan Petir"
        assert attrs["severity"] == "Moderate"
        assert attrs["cap_code"] == "CKS20260430001"
        assert attrs["area_desc"] == "Kalimantan Selatan"
        assert "web" in attrs
        assert "effective" in attrs
        assert "expires" in attrs

    def test_attributes_empty_when_no_alert(self):
        sensor = _make_sensor({"home_in_alert": False, "home_alert": None})
        assert sensor.extra_state_attributes == {}

    def test_attributes_empty_when_data_none(self):
        sensor = _make_sensor(None)
        assert sensor.extra_state_attributes == {}
