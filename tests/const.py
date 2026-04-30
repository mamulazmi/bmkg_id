"""Test constants and mock data for BMKG integration.

All location data here is fictional/public — Jakarta area used as generic test location.
HA lat/lon taken from the lokasi field of the BMKG mock response itself.
"""

# Fictional ADM4 code for testing only — not a real user location
MOCK_ADM4 = "31.71.01.1001"

# HA home coordinates sourced from BMKG lokasi response below (not personal data)
MOCK_HA_LAT = -6.2088
MOCK_HA_LON = 106.8456

MOCK_WEATHER_RESPONSE = {
    "lokasi": {
        "provinsi": "DKI Jakarta",
        "kotkab": "Kota Jakarta Pusat",
        "kecamatan": "Gambir",
        "desa": "Gambir",
        "lat": -6.2088,
        "lon": 106.8456,
        "timezone": "Asia/Jakarta",
    },
    "data": [
        {
            "cuaca": [
                [
                    {
                        "datetime": "2026-04-29T15:00:00Z",
                        "t": 30,
                        "hu": 80,
                        "ws": 9.72,
                        "wd_deg": 90,
                        "tp": 0,
                        "tcc": 60,
                        "vs": 9000,
                        "weather": 1,
                        "weather_desc": "Cerah Berawan",
                        "weather_desc_en": "Partly Cloudy",
                        "wd": "E",
                        "vs_text": "9 km",
                        "local_datetime": "2026-04-29 22:00:00",
                        "image": "https://api-apps.bmkg.go.id/storage/icon/cuaca/cerah-berawan-pm.svg",
                        "analysis_date": "2026-04-29T12:00:00",
                    }
                ]
            ]
        }
    ],
}

MOCK_EARTHQUAKE_RESPONSE = {
    "Infogempa": {
        "gempa": [
            {
                "Tanggal": "29 Apr 2026",
                "Jam": "17:09:04 WIB",
                "DateTime": "2026-04-29T10:09:04+00:00",
                "Coordinates": "-6.20,106.85",  # near Jakarta (mock HA location)
                "Lintang": "6.20 LS",
                "Bujur": "106.85 BT",
                "Magnitude": "3.5",
                "Kedalaman": "10 km",
                "Wilayah": "Pusat gempa di laut 5 km Barat Jakarta",
                "Dirasakan": "II Jakarta Pusat",
                "Shakemap": "20260429170904.mmi.jpg",
            },
            {
                "Tanggal": "28 Apr 2026",
                "Jam": "10:00:00 WIB",
                "DateTime": "2026-04-28T03:00:00+00:00",
                "Coordinates": "-8.09,107.74",  # far from HA location
                "Lintang": "8.09 LS",
                "Bujur": "107.74 BT",
                "Magnitude": "4.0",
                "Kedalaman": "19 km",
                "Wilayah": "Pusat gempa di Tasikmalaya",
                "Dirasakan": "II Tasikmalaya",
                "Shakemap": "20260428100000.mmi.jpg",
            },
        ]
    }
}

MOCK_RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Peringatan Dini Cuaca BMKG</title>
    <item>
      <title>Hujan Lebat di DKI Jakarta</title>
      <link>https://www.bmkg.go.id/alerts/nowcast/id/CJK20260429001_alert.xml</link>
      <description>Hujan lebat di Jakarta Pusat dan sekitarnya</description>
      <author>cuaca.ekstrem@bmkg.go.id (BMKG)</author>
      <category>Met</category>
      <pubDate>Wed, 29 Apr 2026 21:40:00 +0700</pubDate>
    </item>
    <item>
      <title>Hujan Lebat di Jawa Tengah</title>
      <link>https://www.bmkg.go.id/alerts/nowcast/id/CJH20260429004_alert.xml</link>
      <description>Hujan lebat di sebagian wilayah Jawa Tengah</description>
      <author>cuaca.ekstrem@bmkg.go.id (BMKG)</author>
      <category>Met</category>
      <pubDate>Wed, 29 Apr 2026 20:00:00 +0700</pubDate>
    </item>
  </channel>
</rss>"""

MOCK_RSS_XML_EMPTY = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel/></rss>"""

MOCK_RSS_XML_MALFORMED = "NOT VALID XML <<<"

MOCK_CAP_XML = """<?xml version="1.0"?>
<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
  <info>
    <event>Hujan Lebat dan Petir</event>
    <urgency>Immediate</urgency>
    <severity>Moderate</severity>
    <certainty>Observed</certainty>
    <effective>2026-04-30T08:30:00+07:00</effective>
    <expires>2026-04-30T10:30:00+07:00</expires>
    <senderName>Badan Meteorologi Klimatologi dan Geofisika</senderName>
    <headline>Hujan Lebat disertai Petir di Jawa Timur</headline>
    <description>Hujan lebat disertai petir akan terjadi di sebagian wilayah Jawa Timur.</description>
    <web>https://nowcasting.bmkg.go.id/infografis/CJT/2026/04/30/infografis.jpg</web>
    <area>
      <areaDesc>Jawa Timur</areaDesc>
      <polygon>-7.1,113.2 -7.2,113.3 -7.3,113.1 -7.1,113.2</polygon>
    </area>
  </info>
</alert>"""

MOCK_CAP_XML_NO_POLYGON = """<?xml version="1.0"?>
<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
  <info>
    <event>Hujan Lebat</event>
    <severity>Minor</severity>
    <urgency>Expected</urgency>
    <certainty>Possible</certainty>
    <effective>2026-04-30T08:00:00+07:00</effective>
    <expires>2026-04-30T10:00:00+07:00</expires>
    <senderName>BMKG</senderName>
    <headline>Hujan</headline>
    <description>Hujan.</description>
    <web>https://example.com/img.jpg</web>
    <area><areaDesc>Sulawesi Tengah</areaDesc></area>
  </info>
</alert>"""

MOCK_CAP_XML_MALFORMED = "NOT VALID XML <<<"

# Simple square polygon: lat -6.0 to -7.0, lon 106.0 to 107.0
# Inside: (-6.5, 106.5) — Outside: (-8.0, 110.0)
MOCK_POLYGON_STR = "-6.0,106.0 -6.0,107.0 -7.0,107.0 -7.0,106.0 -6.0,106.0"
