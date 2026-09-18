"""
Unit tests for the vessel-port feasibility rule engine.
"""

import sys
from pathlib import Path
import unittest

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.member3.feasibility import check_feasibility


class TestFeasibilityEngine(unittest.TestCase):
    def test_all_vessels_fit(self):
        """Case 1: Deep water port (Gangavaram) where all vessel classes fit."""
        cargo_tonnage = 30000.0
        result = check_feasibility(cargo_tonnage=cargo_tonnage, destination_port="Gangavaram")

        self.assertIn("feasible", result)
        self.assertIn("infeasible", result)

        feasible_classes = [item["class"] for item in result["feasible"]]
        expected_classes = ["Handysize", "Supramax", "Panamax", "Capesize"]

        self.assertEqual(feasible_classes, expected_classes)
        self.assertEqual(len(result["infeasible"]), 0)

        for item in result["feasible"]:
            self.assertEqual(item["notes"], "meets all port limits")

    def test_only_small_vessels_fit(self):
        """Case 2: Restricted port (Sagar) where only Handysize fits."""
        cargo_tonnage = 30000.0
        result = check_feasibility(cargo_tonnage=cargo_tonnage, destination_port="Sagar")

        feasible_classes = [item["class"] for item in result["feasible"]]
        self.assertEqual(feasible_classes, ["Handysize"])

        infeasible_classes = [item["class"] for item in result["infeasible"]]
        self.assertIn("Supramax", infeasible_classes)
        self.assertIn("Panamax", infeasible_classes)
        self.assertIn("Capesize", infeasible_classes)

        # Check reason format explains limit exceeded + by how much
        for item in result["infeasible"]:
            self.assertIn("exceeds max draft", item["reason"])
            self.assertIn("m > ", item["reason"])

    def test_no_vessels_fit(self):
        """Case 3: Shallow port (Haldia) where no vessel classes fit due to draft limits."""
        cargo_tonnage = 30000.0
        result = check_feasibility(cargo_tonnage=cargo_tonnage, destination_port="Haldia")

        self.assertEqual(len(result["feasible"]), 0)
        self.assertEqual(len(result["infeasible"]), 4)

        for item in result["infeasible"]:
            self.assertIn("exceeds max draft", item["reason"])
            self.assertIn("> 8.5m", item["reason"])

    def test_example_scenario_paradip(self):
        """Verify prompt example scenario with 70,000t at Paradip."""
        cargo_tonnage = 70000.0
        result = check_feasibility(cargo_tonnage=cargo_tonnage, destination_port="Paradip")

        # Panamax should be feasible with notes "meets all port limits"
        panamax_matches = [item for item in result["feasible"] if item["class"] == "Panamax"]
        self.assertEqual(len(panamax_matches), 1)
        self.assertEqual(panamax_matches[0]["notes"], "meets all port limits")

        # Capesize should be infeasible with exact reason
        capesize_matches = [item for item in result["infeasible"] if item["class"] == "Capesize"]
        self.assertEqual(len(capesize_matches), 1)
        self.assertEqual(capesize_matches[0]["reason"], "exceeds max draft (18.2m > 17.0m)")

    def test_unknown_port_raises_error(self):
        """Verify that an unregistered port raises a descriptive ValueError."""
        with self.assertRaises(ValueError):
            check_feasibility(cargo_tonnage=50000.0, destination_port="NonExistentPort")


if __name__ == "__main__":
    unittest.main()
