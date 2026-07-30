"""Tests for Scrutiny API data helpers."""

import importlib.util
from pathlib import Path
import sys
import types
import unittest

PACKAGE_PATH = Path(__file__).parents[1] / "custom_components" / "scrutiny"
PACKAGE_NAME = "scrutiny_test"

package = types.ModuleType(PACKAGE_NAME)
package.__path__ = [str(PACKAGE_PATH)]
sys.modules[PACKAGE_NAME] = package


def load_module(name: str):
    """Load an integration module without importing Home Assistant."""
    spec = importlib.util.spec_from_file_location(
        f"{PACKAGE_NAME}.{name}",
        PACKAGE_PATH / f"{name}.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


load_module("const")
helpers = load_module("helpers")


def device_details(attributes):
    """Build the relevant subset of a Scrutiny device details response."""
    return {
        "data": {"smart_results": [{"attrs": attributes}]},
        "metadata": {
            "5": {"display_name": "Reallocated Sectors", "critical": True},
            "197": {"display_name": "Current Pending Sector", "critical": True},
        },
    }


class ScrutinyHelpersTest(unittest.TestCase):
    """Verify status decoding and degradation detection."""

    def test_status_severity_uses_scrutiny_bit_flags(self):
        self.assertEqual(0, helpers.status_severity(0))
        self.assertEqual(1, helpers.status_severity(2))
        self.assertEqual(2, helpers.status_severity(1))
        self.assertEqual(2, helpers.status_severity(4))
        self.assertEqual(2, helpers.status_severity(6))

    def test_groups_multiple_degraded_attributes(self):
        details = device_details(
            {
                "5": {
                    "status": 4,
                    "status_reason": "Failure rate exceeded",
                },
                "197": {
                    "status": 2,
                    "status_reason": "Failure rate elevated",
                },
            }
        )

        degraded = helpers.find_degraded_attributes(
            {"5": 0, "197": 0},
            details,
        )

        self.assertEqual(2, len(degraded))
        self.assertEqual("Scrutiny failure", degraded[0]["status_name"])
        self.assertEqual("Scrutiny warning", degraded[1]["status_name"])
        self.assertTrue(degraded[0]["critical"])

    def test_only_reports_worse_severity(self):
        details = device_details(
            {
                "5": {"status": 2},
                "197": {"status": 0},
            }
        )

        degraded = helpers.find_degraded_attributes(
            {"5": 4, "197": 2},
            details,
        )

        self.assertEqual([], degraded)

    def test_new_attribute_is_added_to_baseline_without_alerting(self):
        details = device_details({"5": {"status": 4}})

        degraded = helpers.find_degraded_attributes({}, details)

        self.assertEqual([], degraded)

    def test_unknown_nonzero_status_is_failure(self):
        self.assertEqual(2, helpers.status_severity(8))
        self.assertEqual("unknown status flag 8", helpers.status_name(8))

    def test_active_issues_are_grouped_by_drive(self):
        devices = {
            "drive-1": {
                **device_details(
                    {
                        "5": {"status": 4, "status_reason": "Failed"},
                        "197": {"status": 0},
                    }
                ),
                "data": {
                    "device": {
                        "host_id": "host-1",
                        "model_name": "Drive One",
                    },
                    "smart_results": [
                        {
                            "attrs": {
                                "5": {
                                    "status": 4,
                                    "status_reason": "Failed",
                                },
                                "197": {"status": 0},
                            }
                        }
                    ],
                },
            },
            "drive-2": {
                **device_details({"197": {"status": 2}}),
                "data": {
                    "device": {
                        "host_id": "host-2",
                        "model_name": "Drive Two",
                    },
                    "smart_results": [
                        {"attrs": {"197": {"status": 2}}}
                    ],
                },
            },
        }

        issues = helpers.get_active_issues(devices)

        self.assertEqual(2, len(issues))
        self.assertEqual("Drive One", issues[0]["drive_name"])
        self.assertEqual(1, len(issues[0]["attributes"]))
        self.assertEqual(
            "Scrutiny failure",
            issues[0]["attributes"][0]["status_name"],
        )
        self.assertEqual(
            "Scrutiny warning",
            issues[1]["attributes"][0]["status_name"],
        )


if __name__ == "__main__":
    unittest.main()
