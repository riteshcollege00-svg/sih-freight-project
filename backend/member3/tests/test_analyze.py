"""
Unit tests for the analyze_vessel_optimization orchestration function.
"""

import sys
from pathlib import Path
import unittest

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.member3.analyze import analyze_vessel_optimization

EXPECTED_TOP_LEVEL_KEYS = {"vessel_feasibility", "voyage_cost", "idle_management"}


class TestAnalyzeVesselOptimization(unittest.TestCase):

    def test_paradip_feasible_scenario(self):
        """
        Case 1: Paradip, 50000t from Australia, 1 voyage.
        Expects at least one feasible vessel, non-null voyage_cost,
        and total_usd == sum of breakdown.
        """
        result = analyze_vessel_optimization(
            cargo_tonnage=50000.0,
            commodity="coal",
            origin="Australia",
            destination_port="Paradip",
            required_date="2026-10-01",
            num_voyages=1,
            freight_rate_usd_per_tonne=14.2,
        )

        # All 3 top-level keys must be present
        self.assertEqual(set(result.keys()), EXPECTED_TOP_LEVEL_KEYS)

        # voyage_cost must not be null when feasible vessels exist
        self.assertIsNotNone(result["voyage_cost"])
        self.assertGreater(len(result["vessel_feasibility"]["feasible"]), 0)

        # total_usd must equal exact sum of breakdown values
        vc = result["voyage_cost"]
        self.assertEqual(
            vc["total_usd"],
            vc["breakdown"]["freight"]
            + vc["breakdown"]["fuel"]
            + vc["breakdown"]["port"]
            + vc["breakdown"]["waiting"],
        )

        # idle_management must be populated
        self.assertIn("expected_idle_days", result["idle_management"])
        self.assertIn("alternative_employment", result["idle_management"])
        self.assertGreater(result["idle_management"]["expected_idle_days"], 0)

    def test_haldia_no_vessel_fits(self):
        """
        Case 2: Haldia is too shallow for all vessel classes (all drafts exceed 8.5m).
        Expects empty feasible list, null voyage_cost,
        and idle_management still populated.
        """
        result = analyze_vessel_optimization(
            cargo_tonnage=30000.0,
            commodity="coal",
            origin="Australia",
            destination_port="Haldia",
            required_date="2026-10-01",
            num_voyages=1,
            freight_rate_usd_per_tonne=14.2,
        )

        # All 3 top-level keys must be present
        self.assertEqual(set(result.keys()), EXPECTED_TOP_LEVEL_KEYS)

        # No feasible vessels at Haldia
        self.assertEqual(result["vessel_feasibility"]["feasible"], [])
        self.assertGreater(len(result["vessel_feasibility"]["infeasible"]), 0)

        # voyage_cost must be None when no vessel is feasible
        self.assertIsNone(result["voyage_cost"])

        # idle_management must always be populated (port-based, not vessel-based)
        idle = result["idle_management"]
        self.assertIn("expected_idle_days", idle)
        self.assertIn("alternative_employment", idle)
        self.assertIsInstance(idle["alternative_employment"], str)
        self.assertGreater(len(idle["alternative_employment"]), 0)
        self.assertGreater(idle["expected_idle_days"], 0)

    def test_response_has_exactly_3_top_level_keys(self):
        """
        Case 3: Strict contract test — response must have EXACTLY 3 top-level
        keys: vessel_feasibility, voyage_cost, idle_management.
        Catches typos, extra fields, or missing keys.
        """
        result = analyze_vessel_optimization(
            cargo_tonnage=50000.0,
            commodity="iron_ore",
            origin="Australia",
            destination_port="Gangavaram",
            required_date="2026-11-15",
            num_voyages=2,
            freight_rate_usd_per_tonne=12.0,
        )

        self.assertEqual(len(result), 3, "Response must have exactly 3 top-level keys")
        self.assertIn("vessel_feasibility", result)
        self.assertIn("voyage_cost", result)
        self.assertIn("idle_management", result)

        # Must NOT contain any other keys
        extra_keys = set(result.keys()) - EXPECTED_TOP_LEVEL_KEYS
        self.assertEqual(extra_keys, set(), f"Unexpected extra keys: {extra_keys}")


if __name__ == "__main__":
    unittest.main()
