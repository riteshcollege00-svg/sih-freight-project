"""
Demo script showcasing member3 vessel optimization capabilities.
Demonstrates feasibility checks, voyage cost estimation, and idle time analysis
across realistic shipping scenarios.
"""

import sys
from pathlib import Path
import json

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.member3.analyze import analyze_vessel_optimization


def run_demo():
    scenarios = [
        {
            "name": "Scenario A: Standard Feasible Route (Panamax to Paradip)",
            "params": {
                "cargo_tonnage": 50000.0,
                "commodity": "coal",
                "origin": "Australia",
                "destination_port": "Paradip",
                "required_date": "2026-10-15",
                "num_voyages": 1,
                "freight_rate_usd_per_tonne": 14.2,
            },
        },
        {
            "name": "Scenario B: Infeasible Route (Draft-Restricted Port - Haldia)",
            "params": {
                "cargo_tonnage": 30000.0,
                "commodity": "coal",
                "origin": "Australia",
                "destination_port": "Haldia",
                "required_date": "2026-10-15",
                "num_voyages": 1,
                "freight_rate_usd_per_tonne": 14.2,
            },
        },
        {
            "name": "Scenario C: Multi-Voyage Large Volume Route (Capesize to Gangavaram, 3 Voyages)",
            "params": {
                "cargo_tonnage": 150000.0,
                "commodity": "coal",
                "origin": "Australia",
                "destination_port": "Gangavaram",
                "required_date": "2026-10-15",
                "num_voyages": 3,
                "freight_rate_usd_per_tonne": 14.2,
            },
        },
    ]

    print("=" * 80)
    print("MEMBER 3: VESSEL OPTIMIZATION DEMO")
    print("=" * 80)

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n[{i}] {scenario['name']}")
        print("-" * 80)
        print("Inputs:")
        for k, v in scenario["params"].items():
            print(f"  {k}: {v}")
        print("\nOutput:")

        result = analyze_vessel_optimization(**scenario["params"])
        print(json.dumps(result, indent=2))
        print("-" * 80)


if __name__ == "__main__":
    run_demo()
