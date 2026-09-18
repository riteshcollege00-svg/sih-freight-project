# Member 3: Vessel-Port Feasibility & Voyage Cost Optimization Engine

## What This Module Does
This module evaluates vessel-port physical compatibility, selects the most size-efficient feasible vessel class, estimates comprehensive multi-voyage shipping costs, and suggests turnaround idle-time mitigations and backhaul routes.

---

## Files Overview

| File | Purpose |
| :--- | :--- |
| [`analyze.py`](file:///c:/Users/socia/sih-freight-project/backend/member3/analyze.py) | **Main orchestrator**: Combines feasibility, cost modeling, and idle-time estimation to return the complete member3 API response contract. |
| [`feasibility.py`](file:///c:/Users/socia/sih-freight-project/backend/member3/feasibility.py) | Evaluates whether vessel classes (Handysize, Supramax, Panamax, Capesize) satisfy port physical constraints (draft, LOA, beam) and cargo deadweight requirements. |
| [`cost_model.py`](file:///c:/Users/socia/sih-freight-project/backend/member3/cost_model.py) | Calculates voyage economics including freight, bunker fuel consumption, port dues, and waiting/demurrage costs for single or multi-voyage schedules. |
| [`idle_time.py`](file:///c:/Users/socia/sih-freight-project/backend/member3/idle_time.py) | Estimates port idle/turnaround waiting days and suggests geographically optimal backhaul employment corridors. |
| [`demo.py`](file:///c:/Users/socia/sih-freight-project/backend/member3/demo.py) | Standalone CLI demonstration running realistic shipment scenarios with formatted JSON output. |

---

## Main Entry Point

Member 4 (Backend API integration) only needs to call `analyze_vessel_optimization()` from [`backend/member3/analyze.py`](file:///c:/Users/socia/sih-freight-project/backend/member3/analyze.py).

### Function Signature
```python
def analyze_vessel_optimization(
    cargo_tonnage: float,
    commodity: str,
    origin: str,
    destination_port: str,
    required_date: str,
    num_voyages: int,
    freight_rate_usd_per_tonne: float,
) -> dict
```

### Example Usage
```python
from backend.member3.analyze import analyze_vessel_optimization

result = analyze_vessel_optimization(
    cargo_tonnage=50000.0,
    commodity="coal",
    origin="Australia",
    destination_port="Paradip",
    required_date="2026-10-15",
    num_voyages=1,
    freight_rate_usd_per_tonne=14.2,
)

print(result)
```

### Expected Return Shape
The response dictionary contains **exactly** these three top-level keys:
```json
{
  "vessel_feasibility": {
    "feasible": [
      {
        "class": "Supramax",
        "notes": "meets all port limits"
      },
      {
        "class": "Panamax",
        "notes": "meets all port limits"
      }
    ],
    "infeasible": [
      {
        "class": "Handysize",
        "reason": "cargo exceeds deadweight capacity (50000.0t > 35000.0t)"
      },
      {
        "class": "Capesize",
        "reason": "exceeds max draft (18.2m > 17.0m)"
      }
    ]
  },
  "voyage_cost": {
    "total_usd": 985926,
    "breakdown": {
      "freight": 710000,
      "fuel": 235926,
      "port": 40000,
      "waiting": 0
    }
  },
  "idle_management": {
    "expected_idle_days": 2.5,
    "alternative_employment": "backhaul option on Indonesia route"
  }
}
```

> **Note**: If no vessel class is physically feasible for the destination port and cargo (such as draft-restricted Haldia), `voyage_cost` will be `null` (`None`), while `vessel_feasibility` and `idle_management` remain fully populated.

---

## Mock Data Disclaimer
The following reference datasets located in `backend/member3/data/`:
- `vessel_classes.json`
- `port_limits.json`
- `route_distances.json`
- `vessel_ops.json`
- `port_costs.json`
- `port_idle_estimates.json`
- `backhaul_suggestions.json`

are all **synthetic/estimated mock values** created for the hackathon demonstration. These will be replaced with Member 1's authoritative database/pipeline post-hackathon.

---

## Known Assumptions
1. **Bunker Price**: `BUNKER_PRICE_USD_PER_TONNE` is currently hardcoded at `$650/tonne` (typical VLSFO marine fuel price).
2. **Port Dues**: Represent flat estimated port call costs per voyage rather than tiered official port tariffs.
3. **Route Distances**: Based on approximate great-circle nautical mile estimates between major international export hubs and Indian East Coast ports.
4. **Multi-Voyage Scaling**: In multi-voyage planning (`num_voyages > 1`), freight, fuel, port dues, and waiting costs scale linearly with voyage count.

---

## How to Run Tests

Run the complete test suite across all member3 modules using Python's built-in `unittest` runner:
```powershell
python -m unittest discover -s backend/member3/tests -p "test_*.py" -v
```

To run the interactive CLI demo:
```powershell
python backend/member3/demo.py
```
