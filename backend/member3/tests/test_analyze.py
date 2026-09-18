"""
Unit tests for the analyze_vessel_optimization orchestration function.
Structural/relational assertions used throughout — no hardcoded mocked values.
"""

import sys
from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.member3.analyze import analyze_vessel_optimization

EXPECTED_TOP_LEVEL_KEYS = {"vessel_feasibility", "voyage_cost", "idle_management"}


class TestAnalyzeVesselOptimization(unittest.TestCase):

    def test_paradip_feasible_scenario(self):
        """Case 1: Paradip, 50000t from Australia, 1 voyage — at least one feasible vessel,
        non-null voyage_cost, and total_usd == sum of breakdown."""
        result = analyze_vessel_optimization(
            cargo_tonnage=50000.0,
            commodity="coal",
            origin="Australia",
            destination_port="Paradip",
            required_date="2026-10-01",
            num_voyages=1,
            freight_rate_usd_per_tonne=14.2,
        )

        self.assertEqual(set(result.keys()), EXPECTED_TOP_LEVEL_KEYS)

        # At least one vessel must be feasible
        self.assertIsNotNone(result["voyage_cost"])
        self.assertGreater(len(result["vessel_feasibility"]["feasible"]), 0)

        # total_usd must equal exact sum of breakdown
        vc = result["voyage_cost"]
        self.assertEqual(
            vc["total_usd"],
            vc["breakdown"]["freight"]
            + vc["breakdown"]["fuel"]
            + vc["breakdown"]["port"]
            + vc["breakdown"]["waiting"],
        )
        self.assertGreater(vc["total_usd"], 0)

        # idle_management populated
        self.assertIn("expected_idle_days", result["idle_management"])
        self.assertIn("alternative_employment", result["idle_management"])
        self.assertGreater(result["idle_management"]["expected_idle_days"], 0)

    def test_haldia_no_vessel_fits(self):
        """Case 2: Haldia — all vessels exceed max_draft of 8.5m, so no feasible vessel,
        voyage_cost is None, but idle_management still populated."""
        result = analyze_vessel_optimization(
            cargo_tonnage=30000.0,
            commodity="coal",
            origin="Australia",
            destination_port="Haldia",
            required_date="2026-10-01",
            num_voyages=1,
            freight_rate_usd_per_tonne=14.2,
        )

        self.assertEqual(set(result.keys()), EXPECTED_TOP_LEVEL_KEYS)

        # No feasible vessels at Haldia
        self.assertEqual(result["vessel_feasibility"]["feasible"], [])
        self.assertGreater(len(result["vessel_feasibility"]["infeasible"]), 0)

        # voyage_cost must be None
        self.assertIsNone(result["voyage_cost"])

        # idle_management always populated
        idle = result["idle_management"]
        self.assertIn("expected_idle_days", idle)
        self.assertIn("alternative_employment", idle)
        self.assertIsInstance(idle["alternative_employment"], str)
        self.assertGreater(len(idle["alternative_employment"]), 0)
        self.assertGreater(idle["expected_idle_days"], 0)

    def test_response_has_exactly_3_top_level_keys(self):
        """Case 3: Strict contract test — response must have EXACTLY the 3 keys:
        vessel_feasibility, voyage_cost, idle_management."""
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

        extra_keys = set(result.keys()) - EXPECTED_TOP_LEVEL_KEYS
        self.assertEqual(extra_keys, set(), f"Unexpected extra keys: {extra_keys}")

    def test_invalid_num_voyages(self):
        """Test num_voyages=0 raises ValueError."""
        with self.assertRaises(ValueError):
            analyze_vessel_optimization(
                cargo_tonnage=50000.0,
                commodity="iron_ore",
                origin="Australia",
                destination_port="Gangavaram",
                required_date="2026-11-15",
                num_voyages=0,
                freight_rate_usd_per_tonne=12.0,
            )

    def test_empty_origin(self):
        """Test empty string origin raises ValueError."""
        with self.assertRaises(ValueError):
            analyze_vessel_optimization(
                cargo_tonnage=50000.0,
                commodity="iron_ore",
                origin="",
                destination_port="Gangavaram",
                required_date="2026-11-15",
                num_voyages=1,
                freight_rate_usd_per_tonne=12.0,
            )


if __name__ == "__main__":
    unittest.main()
