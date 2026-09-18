"""
Voyage cost estimation model.
Calculates costs and returns a detailed breakdown.
"""

import json
from pathlib import Path
from typing import Dict, Any

DATA_DIR = Path(__file__).resolve().parent / "data"

BUNKER_PRICE_USD_PER_TONNE = 650


def _load_json(filename: str) -> dict:
    path = DATA_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def estimate_voyage_cost(
    cargo_tonnage: float,
    origin: str,
    destination_port: str,
    vessel_class: str,
    freight_rate_usd_per_tonne: float,
    waiting_days: float = 0,
    num_voyages: int = 1
) -> Dict[str, Any]:
    """
    Estimate the total voyage cost and breakdown based on reference data.
    """
    if num_voyages < 1:
        raise ValueError("num_voyages must be at least 1")
    if cargo_tonnage <= 0:
        raise ValueError("cargo_tonnage must be positive")

    routes = _load_json("route_distances.json")
    vessels = _load_json("vessel_ops.json")
    ports = _load_json("port_costs.json")

    # Validate origin and get distances
    # Handle case insensitivity where possible for robust API
    origin_key = next((k for k in routes.keys() if k.lower() == origin.lower() and k != "note"), None)
    if not origin_key:
        raise ValueError(f"Origin '{origin}' not found in route distances.")
    
    port_distances = routes[origin_key]
    dest_key_dist = next((k for k in port_distances.keys() if k.lower() == destination_port.lower()), None)
    if not dest_key_dist:
        raise ValueError(f"Destination port '{destination_port}' not found for origin '{origin}'.")
    distance_nm = port_distances[dest_key_dist]

    # Validate vessel class
    vessel_key = next((k for k in vessels.keys() if k.lower() == vessel_class.lower()), None)
    if not vessel_key:
        raise ValueError(f"Vessel class '{vessel_class}' not found in vessel ops.")
    vessel_data = vessels[vessel_key]
    speed_knots = vessel_data["speed_knots"]
    fuel_consumption = vessel_data["fuel_consumption_tonnes_per_day"]
    daily_hire = vessel_data["daily_hire_cost_usd"]

    # Validate port costs
    port_key = next((k for k in ports.keys() if k.lower() == destination_port.lower()), None)
    if not port_key:
        raise ValueError(f"Destination port '{destination_port}' not found in port costs.")
    port_dues_usd = ports[port_key]["port_dues_usd"]

    # Calculations
    freight = cargo_tonnage * freight_rate_usd_per_tonne
    voyage_days = distance_nm / (speed_knots * 24)
    fuel = voyage_days * fuel_consumption * BUNKER_PRICE_USD_PER_TONNE
    port = port_dues_usd
    waiting = waiting_days * daily_hire

    # Round to nearest whole number
    freight_rounded = round(freight)
    fuel_rounded = round(fuel)
    port_rounded = round(port)
    waiting_rounded = round(waiting)

    total_usd = freight_rounded + fuel_rounded + port_rounded + waiting_rounded

    return {
        "total_usd": total_usd * num_voyages,
        "breakdown": {
            "freight": freight_rounded * num_voyages,
            "fuel": fuel_rounded * num_voyages,
            "port": port_rounded * num_voyages,
            "waiting": waiting_rounded * num_voyages
        }
    }
