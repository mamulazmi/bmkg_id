"""BMKG API Client."""

from __future__ import annotations

import math
import socket
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import aiohttp
import async_timeout

from .const import BMKG_API_URL, BMKG_EARTHQUAKE_URL, BMKG_NOWCAST_RSS_URL


class BmkgApiClientError(Exception):
    """General API error."""


class BmkgApiClientCommunicationError(BmkgApiClientError):
    """Communication/network error."""


class BmkgApiClient:
    """BMKG API client."""

    def __init__(self, adm4: str, session: aiohttp.ClientSession) -> None:
        """Initialize client."""
        self._adm4 = adm4
        self._session = session

    async def async_get_forecast(self) -> dict[str, Any]:
        """Fetch forecast data from BMKG API."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.get(
                    url=BMKG_API_URL,
                    params={"adm4": self._adm4},
                )
                response.raise_for_status()
                return await response.json()
        except TimeoutError as exception:
            msg = f"Timeout fetching BMKG data - {exception}"
            raise BmkgApiClientCommunicationError(msg) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching BMKG data - {exception}"
            raise BmkgApiClientCommunicationError(msg) from exception
        except Exception as exception:
            msg = f"Unexpected error - {exception}"
            raise BmkgApiClientError(msg) from exception

    @staticmethod
    def get_current_forecast(data: dict[str, Any]) -> dict[str, Any] | None:
        """Return the forecast entry nearest to current time (UTC)."""
        now = datetime.now(tz=timezone.utc)
        best: dict[str, Any] | None = None
        best_delta = None

        cuaca_periods: list[list[dict]] = (data.get("data") or [{}])[0].get("cuaca", [])
        for period in cuaca_periods:
            for entry in period:
                try:
                    dt = datetime.fromisoformat(
                        entry["datetime"].replace("Z", "+00:00")
                    )
                    delta = abs((dt - now).total_seconds())
                    if best_delta is None or delta < best_delta:
                        best_delta = delta
                        best = entry
                except (KeyError, ValueError):
                    continue

        return best

    @staticmethod
    def get_all_forecasts(data: dict[str, Any]) -> list[dict[str, Any]]:
        """Return all forecast entries flattened."""
        cuaca_periods: list[list[dict]] = (data.get("data") or [{}])[0].get("cuaca", [])
        return [entry for period in cuaca_periods for entry in period]


class BmkgEarthquakeApiClient:
    """BMKG felt earthquake API client."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize client."""
        self._session = session

    async def async_get_earthquakes(self) -> list[dict[str, Any]]:
        """Fetch felt earthquake list from BMKG."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.get(url=BMKG_EARTHQUAKE_URL)
                response.raise_for_status()
                data = await response.json(content_type=None)
                return data.get("Infogempa", {}).get("gempa", [])
        except TimeoutError as exception:
            msg = f"Timeout fetching BMKG earthquake data - {exception}"
            raise BmkgApiClientCommunicationError(msg) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching BMKG earthquake data - {exception}"
            raise BmkgApiClientCommunicationError(msg) from exception
        except Exception as exception:
            msg = f"Unexpected error - {exception}"
            raise BmkgApiClientError(msg) from exception

    @staticmethod
    def parse_coordinates(coordinates_str: str) -> tuple[float, float] | None:
        """Parse 'lat,lon' string. Negative lat = south."""
        try:
            parts = coordinates_str.split(",")
            return float(parts[0]), float(parts[1])
        except (ValueError, IndexError):
            return None

    @staticmethod
    def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Great-circle distance in km between two coordinates."""
        r = 6371.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def find_nearest(
        self,
        earthquakes: list[dict[str, Any]],
        ha_lat: float,
        ha_lon: float,
    ) -> dict[str, Any] | None:
        """Return earthquake entry nearest to given HA coordinates."""
        best: dict[str, Any] | None = None
        best_distance: float | None = None

        for quake in earthquakes:
            coords = self.parse_coordinates(quake.get("Coordinates", ""))
            if coords is None:
                continue
            dist = self.haversine_km(ha_lat, ha_lon, coords[0], coords[1])
            if best_distance is None or dist < best_distance:
                best_distance = dist
                best = {**quake, "_distance_km": round(dist, 1)}

        return best


class BmkgNowcastApiClient:
    """BMKG Nowcast (weather warning) RSS + CAP client."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize client."""
        self._session = session

    async def async_get_warnings(self) -> list[dict[str, Any]]:
        """Fetch and parse RSS feed, return list of warning dicts."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.get(url=BMKG_NOWCAST_RSS_URL)
                response.raise_for_status()
                text = await response.text()
        except TimeoutError as exception:
            msg = f"Timeout fetching BMKG nowcast RSS - {exception}"
            raise BmkgApiClientCommunicationError(msg) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching BMKG nowcast RSS - {exception}"
            raise BmkgApiClientCommunicationError(msg) from exception
        except Exception as exception:
            msg = f"Unexpected error - {exception}"
            raise BmkgApiClientError(msg) from exception

        return self._parse_rss(text)

    @staticmethod
    def _parse_rss(xml_text: str) -> list[dict[str, Any]]:
        """Parse RSS XML into list of warning dicts."""
        warnings: list[dict[str, Any]] = []
        try:
            root = ET.fromstring(xml_text)
            channel = root.find("channel")
            if channel is None:
                return warnings
            for item in channel.findall("item"):
                def _text(tag: str, _item: ET.Element = item) -> str:
                    el = _item.find(tag)
                    return el.text.strip() if el is not None and el.text else ""

                link = _text("link")
                cap_code = ""
                if "_alert.xml" in link:
                    cap_code = link.rsplit("/", 1)[-1].replace("_alert.xml", "")

                pub_date_str = _text("pubDate")
                pub_dt: datetime | None = None
                try:
                    pub_dt = parsedate_to_datetime(pub_date_str)
                except Exception:
                    pass

                warnings.append({
                    "title": _text("title"),
                    "link": link,
                    "description": _text("description"),
                    "author": _text("author"),
                    "category": _text("category"),
                    "pub_date": pub_dt.isoformat() if pub_dt else pub_date_str,
                    "cap_code": cap_code,
                })
        except ET.ParseError:
            pass
        return warnings

    @staticmethod
    def filter_by_province(
        warnings: list[dict[str, Any]], province: str
    ) -> list[dict[str, Any]]:
        """Return warnings whose title or description mentions the province."""
        if not province:
            return []
        province_lower = province.lower()
        return [
            w for w in warnings
            if province_lower in w.get("title", "").lower()
            or province_lower in w.get("description", "").lower()
        ]
