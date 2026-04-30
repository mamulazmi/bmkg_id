"""Constants for BMKG Weather integration."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "bmkg_id"
ATTRIBUTION = "Data provided by BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)"

CONF_ADM4 = "adm4"
CONF_NOWCAST_LANGUAGE = "nowcast_language"
CONF_NOWCAST_INTERVAL = "nowcast_update_interval"

DEFAULT_UPDATE_INTERVAL_HOURS = 3

BMKG_API_URL = "https://api.bmkg.go.id/publik/prakiraan-cuaca"
BMKG_EARTHQUAKE_URL = "https://data.bmkg.go.id/DataMKG/TEWS/gempadirasakan.json"

DEFAULT_EARTHQUAKE_UPDATE_INTERVAL_MINUTES = 5

BMKG_NOWCAST_RSS_URL = "https://www.bmkg.go.id/alerts/nowcast/id"
BMKG_NOWCAST_RSS_URL_EN = "https://www.bmkg.go.id/alerts/nowcast/en"
BMKG_NOWCAST_CAP_BASE_URL = "https://www.bmkg.go.id/alerts/nowcast/id/"
DEFAULT_NOWCAST_UPDATE_INTERVAL_MINUTES = 15
DEFAULT_NOWCAST_LANGUAGE = "id"
MIN_NOWCAST_UPDATE_INTERVAL_MINUTES = 10
MAX_NOWCAST_UPDATE_INTERVAL_MINUTES = 60
