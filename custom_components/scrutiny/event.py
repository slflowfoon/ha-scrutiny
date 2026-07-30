"""Event platform for Scrutiny SMART attribute degradation."""

from typing import Any

from homeassistant.components.event import EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, EVENT_TYPE_SMART_ATTRIBUTE_DEGRADED
from .helpers import (
    find_degraded_attributes,
    get_all_attribute_statuses,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Scrutiny event entity."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ScrutinySmartAttributeDegradedEvent(coordinator, entry)])


class ScrutinySmartAttributeDegradedEvent(CoordinatorEntity, EventEntity):
    """Report SMART attributes that move to a worse status."""

    _attr_event_types = [EVENT_TYPE_SMART_ATTRIBUTE_DEGRADED]
    _attr_has_entity_name = False
    _attr_name = "Scrutiny SMART Attribute Degraded"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the event entity with the current state as its baseline."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_smart_attribute_degraded"
        self._previous_statuses = get_all_attribute_statuses(coordinator.data)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Emit one event per drive containing all newly degraded attributes."""
        current_statuses = get_all_attribute_statuses(self.coordinator.data)
        entity_registry = er.async_get(self.hass)

        for wwn, device_details in self.coordinator.data.items():
            previous_statuses = self._previous_statuses.get(wwn)
            if previous_statuses is None:
                continue

            degraded_attributes = find_degraded_attributes(
                previous_statuses,
                device_details,
            )
            if not degraded_attributes:
                continue

            device_data: dict[str, Any] = device_details.get("data", {}).get(
                "device", {}
            )
            sensor_entity_id = entity_registry.async_get_entity_id(
                "sensor",
                DOMAIN,
                f"scrutiny_{wwn}",
            )
            self._trigger_event(
                EVENT_TYPE_SMART_ATTRIBUTE_DEGRADED,
                {
                    "sensor_entity_id": sensor_entity_id,
                    "wwn": wwn,
                    "host_id": device_data.get("host_id"),
                    "drive_name": device_data.get("model_name"),
                    "degraded_attributes": degraded_attributes,
                },
            )
            self.async_write_ha_state()

        self._previous_statuses = current_statuses
