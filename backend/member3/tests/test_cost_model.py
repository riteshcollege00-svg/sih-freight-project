"""
Unit tests for the voyage cost estimation model.
"""

import sys
from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.member3.cost_model import estimate_voyage_cost

class TestCostModel(unittest.TestCase):
    def test_australia_paradip_panamax(self):
        """Case 1: Australia -> Paradip, Panamax, 50000t, waiting_days=2"""
        result = estimate_voyage_cost(
            cargo_tonnage=50000.0,
            origin="Australia",
            destination_port="Paradip",
            vessel_class="Panamax",
            freight_rate_usd_per_tonne=15.0,
            waiting_days=2
        )
        
        total = result["total_usd"]
        breakdown = result["breakdown"]
        
        # Assert total equals sum of breakdown
        self.assertEqual(total, breakdown["freight"] + breakdown["fuel"] + breakdown["port"] + breakdown["waiting"])
        
        # Assert non-negative
        for val in breakdown.values():
            self.assertGreaterEqual(val, 0)
            
    def test_usa_paradip_capesize(self):
        """Case 2: USA -> Paradip, Capesize, 150000t, waiting_days=0"""
        result = estimate_voyage_cost(
            cargo_tonnage=150000.0,
            origin="USA",
            destination_port="Paradip",
            vessel_class="Capesize",
            freight_rate_usd_per_tonne=22.0,
            waiting_days=0
        )
        
        total = result["total_usd"]
        breakdown = result["breakdown"]
        
        # Assert total equals sum of breakdown
        self.assertEqual(total, breakdown["freight"] + breakdown["fuel"] + breakdown["port"] + breakdown["waiting"])
        
        # Assert non-negative
        for val in breakdown.values():
            self.assertGreaterEqual(val, 0)

    def test_invalid_lookups(self):
        """Ensure ValueErrors are raised for invalid inputs."""
        with self.assertRaises(ValueError):
            estimate_voyage_cost(10000, "UnknownOrigin", "Paradip", "Panamax", 10.0)
        
        with self.assertRaises(ValueError):
            estimate_voyage_cost(10000, "Australia", "UnknownPort", "Panamax", 10.0)
            
        with self.assertRaises(ValueError):
            estimate_voyage_cost(10000, "Australia", "Paradip", "UnknownClass", 10.0)

if __name__ == "__main__":
    unittest.main()
