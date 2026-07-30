"""Helpers for interpreting Scrutiny API data."""

from typing import Any

from .const import (
    ATTRIBUTE_STATUS_FAILED_SCRUTINY,
    ATTRIBUTE_STATUS_FAILED_SMART,
    ATTRIBUTE_STATUS_KNOWN_MASK,
    ATTRIBUTE_STATUS_PASSED,
    ATTRIBUTE_STATUS_WARNING_SCRUTINY,
)


def get_latest_smart_data(device_details: dict[str, Any]) -> dict[str, Any]:
    """Return the latest SMART result from a device details response."""
    smart_results = device_details.get("data", {}).get("smart_results", [])
    return smart_results[0] if smart_results else {}


def get_attribute_statuses(device_details: dict[str, Any]) -> dict[str, int]:
    """Return the current status bit flags keyed by SMART attribute ID."""
    attributes = get_latest_smart_data(device_details).get("attrs", {})
    return {
        str(attribute_id): int(attribute.get("status") or ATTRIBUTE_STATUS_PASSED)
        for attribute_id, attribute in attributes.items()
    }


def get_all_attribute_statuses(
    devices: dict[str, dict[str, Any]],
) -> dict[str, dict[str, int]]:
    """Return current SMART attribute status snapshots for all drives."""
    return {
        wwn: get_attribute_statuses(device_details)
        for wwn, device_details in devices.items()
    }


def get_attribute_name(
    device_details: dict[str, Any],
    attribute_id: str,
) -> str:
    """Return Scrutiny's display name for a SMART attribute."""
    metadata = device_details.get("metadata", {}).get(str(attribute_id), {})
    return (
        metadata.get("display_name")
        or metadata.get("name")
        or f"Unknown Attribute Name {attribute_id}"
    )


def status_severity(status: int) -> int:
    """Return 0 for passed, 1 for warning, and 2 for failure."""
    if status == ATTRIBUTE_STATUS_PASSED:
        return 0
    if status & (ATTRIBUTE_STATUS_FAILED_SMART | ATTRIBUTE_STATUS_FAILED_SCRUTINY):
        return 2
    if status & ATTRIBUTE_STATUS_WARNING_SCRUTINY:
        return 1

    # Treat future non-zero flags as failures until their meaning is known.
    return 2


def status_name(status: int) -> str:
    """Return a readable representation of Scrutiny's status bit flags."""
    if status == ATTRIBUTE_STATUS_PASSED:
        return "passed"

    labels = []
    if status & ATTRIBUTE_STATUS_FAILED_SMART:
        labels.append("SMART failure")
    if status & ATTRIBUTE_STATUS_WARNING_SCRUTINY:
        labels.append("Scrutiny warning")
    if status & ATTRIBUTE_STATUS_FAILED_SCRUTINY:
        labels.append("Scrutiny failure")

    unknown_flags = status & ~ATTRIBUTE_STATUS_KNOWN_MASK
    if unknown_flags:
        labels.append(f"unknown status flag {unknown_flags}")

    return ", ".join(labels)


def get_active_issues(
    devices: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return all currently active SMART warnings and failures by drive."""
    active_drives = []

    for wwn, device_details in devices.items():
        latest_data = get_latest_smart_data(device_details)
        attributes = latest_data.get("attrs", {})
        metadata = device_details.get("metadata", {})
        active_attributes = []

        for attribute_id, attribute in attributes.items():
            attribute_id = str(attribute_id)
            status = int(attribute.get("status") or ATTRIBUTE_STATUS_PASSED)
            if status_severity(status) == 0:
                continue

            attribute_metadata = metadata.get(attribute_id, {})
            active_attributes.append(
                {
                    "attribute_id": attribute_id,
                    "name": get_attribute_name(device_details, attribute_id),
                    "status": status,
                    "status_name": status_name(status),
                    "status_reason": attribute.get("status_reason"),
                    "critical": bool(attribute_metadata.get("critical", False)),
                }
            )

        if not active_attributes:
            continue

        device_data = device_details.get("data", {}).get("device", {})
        active_drives.append(
            {
                "wwn": wwn,
                "host_id": device_data.get("host_id"),
                "drive_name": device_data.get("model_name"),
                "attributes": active_attributes,
            }
        )

    return active_drives


def find_degraded_attributes(
    previous_statuses: dict[str, int],
    device_details: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return attributes whose current severity is worse than the snapshot."""
    latest_data = get_latest_smart_data(device_details)
    attributes = latest_data.get("attrs", {})
    metadata = device_details.get("metadata", {})
    degraded = []

    for attribute_id, attribute in attributes.items():
        attribute_id = str(attribute_id)
        if attribute_id not in previous_statuses:
            continue

        old_status = previous_statuses[attribute_id]
        new_status = int(attribute.get("status") or ATTRIBUTE_STATUS_PASSED)
        if status_severity(new_status) <= status_severity(old_status):
            continue

        attribute_metadata = metadata.get(attribute_id, {})
        degraded.append(
            {
                "attribute_id": attribute_id,
                "name": get_attribute_name(device_details, attribute_id),
                "old_status": old_status,
                "old_status_name": status_name(old_status),
                "status": new_status,
                "status_name": status_name(new_status),
                "status_reason": attribute.get("status_reason"),
                "critical": bool(attribute_metadata.get("critical", False)),
            }
        )

    return degraded
