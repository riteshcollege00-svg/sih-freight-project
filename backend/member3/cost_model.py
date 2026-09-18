"""
Voyage cost estimation model.
Calculates costs and returns a detailed breakdown.

Data source: real database via data.db (Member 1's data layer).
Bunker price is fetched live from market_data; 650 USD/t is used only as an
emergency fallback if market_data is empty (edge case / demo safeguard).
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.db import db

# Fallback constant — only used when market_data table is empty
BUNKER_PRICE_USD_PER_TONNE = 650


def _get_port_id(destination_port: str) -> str:
    """Resolve destination port name (case-insensitive) to port_id from the DB."""
    rows = db.fetch_all("SELECT port_id, port_name, demurrage_rate_usd_day FROM ports")
    normalized = destination_port.strip().lower()
    for row in rows:
        if row[1].strip().lower() == normalized:
            return row[0], float(row[2])
    available = [row[1] for row in rows]
    raise ValueError(
        f"Destination port '{destination_port}' not found in ports table. "
        f"Available ports: {available}"
    )


def _get_live_bunker_price() -> float:
    """Fetch the most recent bunker price from market_data, falling back to constant."""
    row = db.fetch_one(
        "SELECT bunker_price_vlsfo_usd_per_t FROM market_data ORDER BY market_date DESC LIMIT 1"
    )
    if row and row[0]:
        return float(row[0])
    return float(BUNKER_PRICE_USD_PER_TONNE)


def estimate_voyage_cost(
    cargo_tonnage: float,
    origin: str,
    destination_port: str,
    vessel_class: str,
    freight_rate_usd_per_tonne: float,
    waiting_days: float = 0,
    num_voyages: int = 1,
) -> Dict[str, Any]:
    """
    Estimate the total voyage cost and breakdown based on real database data.

    Args:
        cargo_tonnage: Cargo weight in tonnes.
        origin: Origin country (e.g. "Australia", "USA").
        destination_port: Destination port name (e.g. "Paradip").
        vessel_class: Vessel class name (e.g. "Panamax").
        freight_rate_usd_per_tonne: Freight rate in USD/tonne.
        waiting_days: Additional waiting/demurrage days per voyage (default 0).
        num_voyages: Number of voyages; scales all costs linearly (default 1).
    """
    if num_voyages < 1:
        raise ValueError("num_voyages must be at least 1")
    if cargo_tonnage <= 0:
        raise ValueError("cargo_tonnage must be positive")

    # Resolve port_id and port dues from ports table
    port_id, demurrage_rate = _get_port_id(destination_port)

    # Look up route: origin_country + destination_port_id
    route_row = db.fetch_one(
        "SELECT distance_nm, bunker_consumption_factor FROM routes "
        "WHERE origin_country = ? AND destination_port_id = ?",
        (origin, port_id),
    )
    if not route_row:
        raise ValueError(
            f"No route found for origin '{origin}' → destination '{destination_port}' (port_id={port_id})."
        )
    distance_nm = float(route_row[0])
    bunker_consumption_factor = float(route_row[1])

    # Look up vessel operating profile
    vessel_row = db.fetch_one(
        "SELECT service_speed_knots, fuel_consumption_tpd FROM vessels WHERE vessel_class = ?",
        (vessel_class,),
    )
    if not vessel_row:
        rows = db.fetch_all("SELECT vessel_class FROM vessels")
        available = [r[0] for r in rows]
        raise ValueError(
            f"Vessel class '{vessel_class}' not found in vessels table. "
            f"Available: {available}"
        )
    speed_knots = float(vessel_row[0])
    fuel_consumption_tpd = float(vessel_row[1])

    # Live bunker price (fallback to constant if market_data empty)
    bunker_price = _get_live_bunker_price()

    # Port cost estimate: one day of demurrage rate as a simplified port-call cost.
    # This is a hackathon-scope simplification; real tariffs are multi-tiered.
    port_due_usd = demurrage_rate * 1.0

    # Waiting cost: per-voyage waiting days at the vessel's daily hire equivalent,
    # approximated as demurrage_rate (closest available daily cost figure in schema)
    daily_hire_usd = demurrage_rate

    # Calculations
    freight = cargo_tonnage * freight_rate_usd_per_tonne
    voyage_days = distance_nm / (speed_knots * 24)
    # Apply route-specific bunker consumption factor
    fuel = voyage_days * fuel_consumption_tpd * bunker_consumption_factor * bunker_price
    port = port_due_usd
    waiting = waiting_days * daily_hire_usd

    # Round each component first, then sum — this guarantees total == sum(breakdown)
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
            "waiting": waiting_rounded * num_voyages,
        },
    }
