"""Constants for the Scrutiny integration."""
from datetime import timedelta

DOMAIN = "scrutiny"
SCAN_INTERVAL = timedelta(minutes=15)

# API Endpoints
API_SUMMARY_ENDPOINT = "/api/summary"
API_DETAILS_ENDPOINT_FORMAT = "/api/device/{wwn}/details"