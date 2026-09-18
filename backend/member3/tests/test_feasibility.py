"""
Unit tests for the vessel-port feasibility rule engine.
Assertions are structural/relational rather than exact mocked values,
since data now comes from the real database.
"""

import sys
from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.member3.feasibility import check_feasibility


class TestFeasibilityEngine(unittest.TestCase):

    def test_all_vessels_fit(self):
        """Case 1: Deep-water port (Gangavaram) — all 4 vessel classes should be feasible
        at 30,000t (well within cargo_capacity_mt of even Handysize=33,000t)."""
        result = check_feasibility(cargo_tonnage=30000.0, destination_port="Gangavaram")

        self.assertIn("feasible", result)
        self.assertIn("infeasible", result)

        # All 4 vessel classes should appear as feasible
        feasible_classes = [item["class"] for item in result["feasible"]]
        self.assertEqual(len(result["feasible"]), 4, f"Expected 4 feasible, got: {feasible_classes}")
        self.assertEqual(len(result["infeasible"]), 0)

        for item in result["feasible"]:
            self.assertEqual(item["notes"], "meets all port limits")

    def test_only_small_vessels_fit(self):
        """Case 2: Restricted port (Sagar/Sandheads) — only Handysize fits the port limits."""
        result = check_feasibility(cargo_tonnage=30000.0, destination_port="Sagar/Sandheads")

        feasible_classes = [item["class"] for item in result["feasible"]]
        self.assertIn("Handysize", feasible_classes)

        # Supramax, Panamax, Capesize should be infeasible (exceed draft/LOA/beam)
        infeasible_classes = [item["class"] for item in result["infeasible"]]
        for cls in ["Supramax", "Panamax", "Capesize"]:
            self.assertIn(cls, infeasible_classes, f"Expected {cls} to be infeasible at Sagar")

        # Reason strings must mention what was exceeded and by how much
        for item in result["infeasible"]:
            self.assertIn("> ", item["reason"], f"Reason for {item['class']} missing '>' limit comparison")

    def test_no_vessels_fit(self):
        """Case 3: Shallow port (Haldia) — all vessels exceed max_draft of 8.5m."""
        result = check_feasibility(cargo_tonnage=30000.0, destination_port="Haldia")

        self.assertEqual(len(result["feasible"]), 0)
        self.assertEqual(len(result["infeasible"]), 4)

        for item in result["infeasible"]:
            self.assertIn("exceeds max draft", item["reason"])
            self.assertIn("> 8.5m", item["reason"])

    def test_example_scenario_paradip(self):
        """Verify example scenario at Paradip: Capesize draft 18.2m vs 17.1m real limit."""
        result = check_feasibility(cargo_tonnage=70000.0, destination_port="Paradip")

        # Capesize should still be infeasible (draft 18.2m > real max_draft 17.1m)
        capesize_infeasible = [item for item in result["infeasible"] if item["class"] == "Capesize"]
        self.assertEqual(len(capesize_infeasible), 1)
        self.assertIn("exceeds max draft", capesize_infeasible[0]["reason"])

        # Panamax (draft 14.2m, capacity 78000t >= 70000t) should be feasible
        panamax_feasible = [item for item in result["feasible"] if item["class"] == "Panamax"]
        self.assertEqual(len(panamax_feasible), 1)
        self.assertEqual(panamax_feasible[0]["notes"], "meets all port limits")

    def test_unknown_port_raises_error(self):
        """Verify that an unregistered port raises a descriptive ValueError."""
        with self.assertRaises(ValueError):
            check_feasibility(cargo_tonnage=50000.0, destination_port="NonExistentPort")


if __name__ == "__main__":
    unittest.main()
