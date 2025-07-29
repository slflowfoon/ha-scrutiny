"""Platform for sensor integration."""
import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Scrutiny sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    new_entities = [
        ScrutinySensor(coordinator, wwn) for wwn in coordinator.data
    ]
    if new_entities:
        async_add_entities(new_entities)


class ScrutinySensor(CoordinatorEntity, SensorEntity):
    """Representation of a Scrutiny Sensor."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, wwn):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._wwn = wwn
        self._attr_unique_id = f"scrutiny_{wwn}"

        device_details = self.coordinator.data.get(self._wwn, {})
        device_data = device_details.get("data", {}).get("device", {})
        model_name = device_data.get("model_name", f"Scrutiny Drive {self._wwn}")
        base_url = self.coordinator.base_url

        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._wwn)},
            "name": model_name,
            "model": model_name,
            "manufacturer": "Scrutiny",
            "configuration_url": f"{base_url}/web/device/{self._wwn}",
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Temperature"

    @property
    def device_class(self) -> SensorDeviceClass:
        """Return the class of this entity."""
        return SensorDeviceClass.TEMPERATURE

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return UnitOfTemperature.CELSIUS

    @property
    def state(self):
        """Return the state of the sensor (temperature)."""
        if self._wwn in self.coordinator.data:
            smart_results = self.coordinator.data[self._wwn].get("data", {}).get("smart_results", [])
            if smart_results:
                return smart_results[0].get("temp")
        return None

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the device."""
        if self._wwn not in self.coordinator.data:
            return {}

        device_details = self.coordinator.data[self._wwn]
        device_data = device_details.get("data", {}).get("device", {})
        smart_results = device_details.get("data", {}).get("smart_results", [])
        latest_smart_data = smart_results[0] if smart_results else {}
        metadata = device_details.get("metadata", {})

        attributes = {
            "WWN": self._wwn,
            "Host ID": device_data.get("host_id"),
            "Serial Number": device_data.get("serial_number"),
            "Device Status": device_data.get("device_status"),
            "Power On Hours": latest_smart_data.get("power_on_hours"),
        }
        
        smart_attrs = latest_smart_data.get("attrs", {})
        for attr_id, attr_data in smart_attrs.items():
            attr_info = metadata.get(str(attr_id), {})
            if "display_name" in attr_info and attr_info["display_name"]:
                attr_name = attr_info["display_name"]
            else:
                attr_name = f"Unknown Attribute Name {attr_id}"
            
            status_value = attr_data.get("status")
            attributes[attr_name] = status_value
            
        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and self._wwn in self.coordinator.data
