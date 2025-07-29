"""Constants for the Scrutiny integration."""
from datetime import timedelta

DOMAIN = "scrutiny"
DEFAULT_SCAN_INTERVAL = 15

# API Endpoints
API_SUMMARY_ENDPOINT = "/api/summary"
API_DETAILS_ENDPOINT_FORMAT = "/api/device/{wwn}/details"
