"""
Unit tests for the idle-time and alternative-employment estimator.
Assertions are structural rather than exact mocked values — idle days
now come from the real database avg_turnaround_days.
"""

import sys
from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.member3.idle_time import estimate_idle_time


class TestIdleTime(unittest.TestCase):

    def test_paradip_single_voyage(self):
        """Case 1: Paradip, num_voyages=1 — check structure and positivity."""
        result = estimate_idle_time(destination_port="Paradip", num_voyages=1)

        self.assertIn("expected_idle_days", result)
        self.assertIn("alternative_employment", result)

        self.assertGreater(result["expected_idle_days"], 0)
        self.assertIsInstance(result["alternative_employment"], str)
        self.assertGreater(len(result["alternative_employment"]), 0)
        self.assertIn("backhaul", result["alternative_employment"])

    def test_paradip_multiple_voyages(self):
        """Case 2: Paradip, num_voyages=3 — idle_days must be exactly 3x single voyage."""
        result_1 = estimate_idle_time(destination_port="Paradip", num_voyages=1)
        result_3 = estimate_idle_time(destination_port="Paradip", num_voyages=3)

        self.assertAlmostEqual(
            result_3["expected_idle_days"],
            round(result_1["expected_idle_days"] * 3, 1),
            places=1,
        )
        self.assertGreater(result_3["expected_idle_days"], 0)
        self.assertIn("backhaul", result_3["alternative_employment"])

    def test_unknown_port_raises_error(self):
        """Case 3: Unknown port raises descriptive ValueError."""
        with self.assertRaises(ValueError):
            estimate_idle_time(destination_port="NonExistentPort", num_voyages=1)


if __name__ == "__main__":
    unittest.main()
