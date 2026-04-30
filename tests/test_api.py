"""Unit tests for BMKG API client logic (no HA needed)."""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import pytest

from custom_components.bmkg_id.api import (
    BmkgEarthquakeApiClient,
    BmkgNowcastApiClient,
    BmkgApiClient,
)

from .const import (
    MOCK_RSS_XML,
    MOCK_RSS_XML_EMPTY,
    MOCK_RSS_XML_MALFORMED,
    MOCK_CAP_XML,
    MOCK_CAP_XML_NO_POLYGON,
    MOCK_CAP_XML_MALFORMED,
    MOCK_POLYGON_STR,
)


# ---------------------------------------------------------------------------
# BmkgApiClient static methods
# ---------------------------------------------------------------------------


class TestGetCurrentForecast:
    """Tests for BmkgApiClient.get_current_forecast."""

    def _make_data(self, dt_iso: str) -> dict:
        return {
            "data": [{"cuaca": [[{"datetime": dt_iso, "t": 25, "hu": 90}]]}]
        }

    def test_returns_nearest_entry(self):
        now = datetime.now(tz=timezone.utc)
        past = (now - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        future_close = (now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        future_far = (now + timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%SZ")

        data = {
            "data": [
                {
                    "cuaca": [
                        [{"datetime": past, "t": 20}],
                        [{"datetime": future_close, "t": 25}],
                        [{"datetime": future_far, "t": 30}],
                    ]
                }
            ]
        }
        result = BmkgApiClient.get_current_forecast(data)
        assert result is not None
        assert result["t"] == 25

    def test_returns_none_if_empty_cuaca(self):
        data = {"data": [{"cuaca": []}]}
        assert BmkgApiClient.get_current_forecast(data) is None

    def test_returns_none_if_data_key_missing(self):
        assert BmkgApiClient.get_current_forecast({}) is None

    def test_handles_empty_data_list(self):
        # Bug 3: {"data": []} must not raise IndexError
        assert BmkgApiClient.get_current_forecast({"data": []}) is None

    def test_skips_malformed_datetime(self):
        now = datetime.now(tz=timezone.utc)
        good = (now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        data = {
            "data": [
                {
                    "cuaca": [
                        [{"datetime": "NOT-A-DATE", "t": 99}],
                        [{"datetime": good, "t": 25}],
                    ]
                }
            ]
        }
        result = BmkgApiClient.get_current_forecast(data)
        assert result is not None
        assert result["t"] == 25

    def test_handles_entry_without_datetime_key(self):
        data = {"data": [{"cuaca": [[{"t": 25}]]}]}
        assert BmkgApiClient.get_current_forecast(data) is None


class TestGetAllForecasts:
    """Tests for BmkgApiClient.get_all_forecasts."""

    def test_flattens_nested_periods(self):
        data = {
            "data": [
                {
                    "cuaca": [
                        [{"t": 25}, {"t": 26}],
                        [{"t": 27}],
                    ]
                }
            ]
        }
        result = BmkgApiClient.get_all_forecasts(data)
        assert len(result) == 3
        assert result[0]["t"] == 25

    def test_empty_cuaca_returns_empty_list(self):
        data = {"data": [{"cuaca": []}]}
        assert BmkgApiClient.get_all_forecasts(data) == []

    def test_empty_data_list_no_crash(self):
        assert BmkgApiClient.get_all_forecasts({"data": []}) == []


# ---------------------------------------------------------------------------
# BmkgEarthquakeApiClient static methods
# ---------------------------------------------------------------------------


class TestParseCoordinates:
    def test_valid_south_lat(self):
        result = BmkgEarthquakeApiClient.parse_coordinates("-2.54,121.06")
        assert result == (-2.54, 121.06)

    def test_valid_north_lat(self):
        result = BmkgEarthquakeApiClient.parse_coordinates("0.80,127.40")
        assert result == (0.80, 127.40)

    def test_empty_string_returns_none(self):
        assert BmkgEarthquakeApiClient.parse_coordinates("") is None

    def test_invalid_string_returns_none(self):
        assert BmkgEarthquakeApiClient.parse_coordinates("invalid") is None

    def test_single_value_returns_none(self):
        assert BmkgEarthquakeApiClient.parse_coordinates("123") is None

    def test_extra_whitespace_handled(self):
        # split(",") → ["−2.54", " 121.06"] — float() handles spaces? No. This should return None.
        result = BmkgEarthquakeApiClient.parse_coordinates("-2.54, 121.06")
        # " 121.06" → float strips leading space → valid
        assert result is not None


class TestHaversineKm:
    def test_same_point_returns_zero(self):
        dist = BmkgEarthquakeApiClient.haversine_km(-3.3, 114.6, -3.3, 114.6)
        assert dist == pytest.approx(0.0, abs=0.01)

    def test_origin_to_origin(self):
        assert BmkgEarthquakeApiClient.haversine_km(0, 0, 0, 0) == pytest.approx(0.0)

    def test_known_distance_jakarta_bandung(self):
        # Jakarta (-6.2088, 106.8456) to Bandung (-6.9175, 107.6191) ≈ 120 km
        dist = BmkgEarthquakeApiClient.haversine_km(
            -6.2088, 106.8456, -6.9175, 107.6191
        )
        assert 110 < dist < 130

    def test_symmetry(self):
        d1 = BmkgEarthquakeApiClient.haversine_km(0, 0, 10, 10)
        d2 = BmkgEarthquakeApiClient.haversine_km(10, 10, 0, 0)
        assert d1 == pytest.approx(d2)


class TestFindNearest:
    def _client(self):
        return BmkgEarthquakeApiClient(session=None)  # session unused here

    def test_finds_nearest(self):
        # HA at Jakarta (-6.2088, 106.8456) — first quake is close, second is far
        quakes = [
            {"Coordinates": "-6.20,106.85", "Magnitude": "3.5"},  # near Jakarta
            {"Coordinates": "-8.09,107.74", "Magnitude": "4.0"},  # Tasikmalaya, far
        ]
        result = self._client().find_nearest(quakes, ha_lat=-6.2088, ha_lon=106.8456)
        assert result is not None
        assert result["Magnitude"] == "3.5"
        assert "_distance_km" in result
        assert result["_distance_km"] < 10  # very close

    def test_returns_none_for_empty_list(self):
        assert self._client().find_nearest([], -6.2088, 106.8456) is None

    def test_skips_invalid_coordinates(self):
        quakes = [{"Coordinates": "invalid", "Magnitude": "4.0"}]
        assert self._client().find_nearest(quakes, -6.2088, 106.8456) is None

    def test_distance_attached_to_result(self):
        quakes = [{"Coordinates": "-6.20,106.85", "Magnitude": "3.5"}]
        result = self._client().find_nearest(quakes, -6.2088, 106.8456)
        assert isinstance(result["_distance_km"], float)


# ---------------------------------------------------------------------------
# BmkgNowcastApiClient._parse_rss
# ---------------------------------------------------------------------------


class TestParseRss:
    def test_valid_rss_returns_warnings(self):
        warnings = BmkgNowcastApiClient._parse_rss(MOCK_RSS_XML)
        assert len(warnings) == 2

    def test_first_warning_fields(self):
        warnings = BmkgNowcastApiClient._parse_rss(MOCK_RSS_XML)
        w = warnings[0]
        assert w["title"] == "Hujan Lebat di DKI Jakarta"
        assert w["cap_code"] == "CJK20260429001"
        assert "Jakarta" in w["description"]
        assert w["author"] == "cuaca.ekstrem@bmkg.go.id (BMKG)"

    def test_cap_code_extraction(self):
        warnings = BmkgNowcastApiClient._parse_rss(MOCK_RSS_XML)
        assert warnings[1]["cap_code"] == "CJH20260429004"

    def test_pub_date_parsed_to_iso(self):
        warnings = BmkgNowcastApiClient._parse_rss(MOCK_RSS_XML)
        # Should be ISO 8601 format
        assert "2026" in warnings[0]["pub_date"]
        assert "T" in warnings[0]["pub_date"]

    def test_empty_channel_returns_empty_list(self):
        assert BmkgNowcastApiClient._parse_rss(MOCK_RSS_XML_EMPTY) == []

    def test_malformed_xml_returns_empty_list(self):
        assert BmkgNowcastApiClient._parse_rss(MOCK_RSS_XML_MALFORMED) == []

    def test_item_without_pubdate_uses_fallback(self):
        xml = """<?xml version="1.0"?><rss version="2.0"><channel>
        <item><title>Test</title><link>https://x.com/A_alert.xml</link>
        <description>desc</description><author>a</author></item>
        </channel></rss>"""
        warnings = BmkgNowcastApiClient._parse_rss(xml)
        assert len(warnings) == 1
        assert warnings[0]["pub_date"] == ""  # empty fallback


# ---------------------------------------------------------------------------
# BmkgNowcastApiClient.filter_by_province
# ---------------------------------------------------------------------------


class TestFilterByProvince:
    WARNINGS = [
        {"title": "Hujan Lebat di DKI Jakarta", "description": "..."},
        {"title": "Hujan Lebat di Jawa Tengah", "description": "..."},
    ]

    def test_matches_province_in_title(self):
        result = BmkgNowcastApiClient.filter_by_province(self.WARNINGS, "DKI Jakarta")
        assert len(result) == 1
        assert "DKI Jakarta" in result[0]["title"]

    def test_description_only_not_matched(self):
        # Province in description only — title doesn't contain phrase → no match
        warnings = [{"title": "Test", "description": "Hujan di DKI Jakarta"}]
        result = BmkgNowcastApiClient.filter_by_province(warnings, "DKI Jakarta")
        assert result == []

    def test_no_match_returns_empty(self):
        result = BmkgNowcastApiClient.filter_by_province(self.WARNINGS, "Bali")
        assert result == []

    def test_empty_province_returns_empty(self):
        result = BmkgNowcastApiClient.filter_by_province(self.WARNINGS, "")
        assert result == []

    def test_case_insensitive(self):
        result = BmkgNowcastApiClient.filter_by_province(self.WARNINGS, "dki jakarta")
        assert len(result) == 1

    def test_empty_warnings_list(self):
        assert BmkgNowcastApiClient.filter_by_province([], "Jawa") == []

    def test_province_with_di_prefix_matches(self):
        # "DI YOGYAKARTA" phrase "di yogyakarta" is substring of "hujan di yogyakarta"
        warnings = [{"title": "Hujan di Yogyakarta", "description": ""}]
        result = BmkgNowcastApiClient.filter_by_province(warnings, "DI YOGYAKARTA")
        assert len(result) == 1

    def test_phrase_no_false_positive_partial_word(self):
        # "SULAWESI UTARA" phrase not in "Maluku Utara" title
        warnings = [{"title": "Hujan di Maluku Utara", "description": ""}]
        result = BmkgNowcastApiClient.filter_by_province(warnings, "SULAWESI UTARA")
        assert result == []

    def test_province_kalimantan_selatan_matches(self):
        warnings = [{"title": "Hujan Lebat disertai Petir di Kalimantan Selatan", "description": ""}]
        result = BmkgNowcastApiClient.filter_by_province(warnings, "KALIMANTAN SELATAN")
        assert len(result) == 1

    def test_kalteng_not_matched_for_kalsel_province(self):
        # Real-world bug: KalTeng warning description mentions KalSel → old word-split matched falsely
        warnings = [
            {"title": "Thunderstorm in Kalimantan Tengah", "description": "...berlaku juga di Kalimantan Selatan..."},
            {"title": "Thunderstorm in Kalimantan Selatan", "description": ""},
        ]
        result = BmkgNowcastApiClient.filter_by_province(warnings, "KALIMANTAN SELATAN")
        assert len(result) == 1
        assert "Kalimantan Selatan" in result[0]["title"]

    def test_phrase_not_matched_by_partial_title_words(self):
        # "KALIMANTAN UTARA" phrase not in either title
        warnings = [
            {"title": "Hujan di Maluku Utara", "description": ""},
            {"title": "Hujan di Kalimantan Selatan", "description": ""},
        ]
        result = BmkgNowcastApiClient.filter_by_province(warnings, "KALIMANTAN UTARA")
        assert result == []


# ---------------------------------------------------------------------------
# BmkgNowcastApiClient._parse_cap_xml
# ---------------------------------------------------------------------------


class TestParseCapXml:
    def test_all_fields_extracted(self):
        result = BmkgNowcastApiClient._parse_cap_xml(MOCK_CAP_XML)
        assert result["event"] == "Hujan Lebat dan Petir"
        assert result["severity"] == "Moderate"
        assert result["urgency"] == "Immediate"
        assert result["certainty"] == "Observed"
        assert result["effective"] == "2026-04-30T08:30:00+07:00"
        assert result["expires"] == "2026-04-30T10:30:00+07:00"
        assert result["sender_name"] == "Badan Meteorologi Klimatologi dan Geofisika"
        assert result["headline"] == "Hujan Lebat disertai Petir di Jawa Timur"
        assert "hujan lebat" in result["cap_description"].lower()
        assert result["web"].startswith("https://nowcasting.bmkg.go.id")
        assert result["area_desc"] == "Jawa Timur"

    def test_polygon_extracted(self):
        result = BmkgNowcastApiClient._parse_cap_xml(MOCK_CAP_XML)
        assert isinstance(result["polygon"], list)
        assert len(result["polygon"]) == 1
        assert "-7.1,113.2" in result["polygon"][0]

    def test_no_polygon_returns_empty_list(self):
        result = BmkgNowcastApiClient._parse_cap_xml(MOCK_CAP_XML_NO_POLYGON)
        assert result["polygon"] == []

    def test_malformed_xml_returns_empty_dict(self):
        result = BmkgNowcastApiClient._parse_cap_xml(MOCK_CAP_XML_MALFORMED)
        assert result == {}

    def test_result_is_truthy(self):
        result = BmkgNowcastApiClient._parse_cap_xml(MOCK_CAP_XML)
        assert bool(result) is True

    def test_no_onset_key(self):
        result = BmkgNowcastApiClient._parse_cap_xml(MOCK_CAP_XML)
        assert "onset" not in result
        assert "effective" in result


# ---------------------------------------------------------------------------
# BmkgNowcastApiClient.parse_polygon
# ---------------------------------------------------------------------------


class TestParsePolygon:
    def test_valid_polygon_string(self):
        result = BmkgNowcastApiClient.parse_polygon(MOCK_POLYGON_STR)
        assert len(result) == 5
        assert result[0] == (-6.0, 106.0)
        assert result[2] == (-7.0, 107.0)

    def test_empty_string_returns_empty(self):
        assert BmkgNowcastApiClient.parse_polygon("") == []

    def test_malformed_pair_skipped(self):
        result = BmkgNowcastApiClient.parse_polygon("-6.0,106.0 INVALID -7.0,107.0")
        assert len(result) == 2

    def test_single_point(self):
        result = BmkgNowcastApiClient.parse_polygon("-6.5,106.5")
        assert result == [(-6.5, 106.5)]


# ---------------------------------------------------------------------------
# BmkgNowcastApiClient.point_in_polygon
# ---------------------------------------------------------------------------


class TestPointInPolygon:
    # Square: lat -6.0 to -7.0, lon 106.0 to 107.0
    SQUARE = [(-6.0, 106.0), (-6.0, 107.0), (-7.0, 107.0), (-7.0, 106.0)]

    def test_point_inside_returns_true(self):
        assert BmkgNowcastApiClient.point_in_polygon(-6.5, 106.5, self.SQUARE) is True

    def test_point_outside_returns_false(self):
        assert BmkgNowcastApiClient.point_in_polygon(-8.0, 110.0, self.SQUARE) is False

    def test_point_far_outside(self):
        assert BmkgNowcastApiClient.point_in_polygon(0.0, 0.0, self.SQUARE) is False

    def test_too_few_points_returns_false(self):
        assert BmkgNowcastApiClient.point_in_polygon(-6.5, 106.5, [(-6.0, 106.0), (-6.0, 107.0)]) is False

    def test_empty_polygon_returns_false(self):
        assert BmkgNowcastApiClient.point_in_polygon(-6.5, 106.5, []) is False
