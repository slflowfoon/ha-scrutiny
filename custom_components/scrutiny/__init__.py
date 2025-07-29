"""The Scrutiny integration."""
import asyncio
import async_timeout
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, API_SUMMARY_ENDPOINT, API_DETAILS_ENDPOINT_FORMAT

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Scrutiny from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    base_url = entry.data["base_url"]
    verify_ssl = entry.data.get("verify_ssl", True)

    scan_interval_minutes = entry.options.get("scan_interval", DEFAULT_SCAN_INTERVAL)
    update_interval = timedelta(minutes=scan_interval_minutes)

    coordinator = ScrutinyDataUpdateCoordinator(hass, base_url, verify_ssl, update_interval)
    await coordinator.async_config_entry_first_refresh()

    entry.async_on_unload(entry.add_update_listener(update_listener))

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


class ScrutinyDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Scrutiny data."""

    def __init__(self, hass: HomeAssistant, base_url: str, verify_ssl: bool, update_interval: timedelta) -> None:
        """Initialize."""
        self.base_url = base_url
        self.verify_ssl = verify_ssl
        self.websession = async_get_clientsession(hass)

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            async with async_timeout.timeout(30):
                summary_url = f"{self.base_url}{API_SUMMARY_ENDPOINT}"
                summary_resp = await self.websession.get(summary_url, ssl=self.verify_ssl)
                summary_resp.raise_for_status()
                summary_data = await summary_resp.json()
                
                wwns = list(summary_data.get("data", {}).get("summary", {}).keys())
                if not wwns:
                    _LOGGER.warning("Scrutiny summary returned no devices.")
                    return {}

                tasks = []
                for wwn in wwns:
                    details_url = f"{self.base_url}{API_DETAILS_ENDPOINT_FORMAT.format(wwn=wwn)}"
                    tasks.append(self._async_get_json(details_url))
                
                responses = await asyncio.gather(*tasks)
                
                all_device_details = {}
                for detail_data in responses:
                    wwn = detail_data.get("data", {}).get("device", {}).get("wwn")
                    if wwn:
                        all_device_details[wwn] = detail_data
                    
                return all_device_details

        except Exception as err:
            raise UpdateFailed(f"Error communicating with Scrutiny API: {err}")

    async def _async_get_json(self, url):
        """Helper to get json from a URL, respecting the SSL setting."""
        response = await self.websession.get(url, ssl=self.verify_ssl)
        response.raise_for_status()
        return await response.json()
