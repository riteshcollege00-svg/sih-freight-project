"""
Orchestration module for member3 vessel optimization analysis.
Composes feasibility, cost estimation, and idle-time results into
the master API contract response shape.

Does NOT modify feasibility.py, cost_model.py, or idle_time.py.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.member3.feasibility import check_feasibility, load_vessel_classes
from backend.member3.cost_model import estimate_voyage_cost
from backend.member3.idle_time import estimate_idle_time


def _find_most_efficient_vessel(
    feasible_vessels: List[Dict[str, Any]],
    cargo_tonnage: float,
) -> Optional[str]:
    """
    From the list of feasible vessel dicts (each has "class" key),
    select the vessel class whose dwt_tonnes is closest to cargo_tonnage.
    Since all feasible vessels already have dwt >= cargo_tonnage, this
    picks the most size-efficient (smallest excess capacity) option.

    Returns the vessel class name string, or None if the list is empty.
    """
    if not feasible_vessels:
        return None

    # Load vessel classes to compare dwt_tonnes values
    vessel_classes = load_vessel_classes()
    dwt_lookup: Dict[str, float] = {
        v["class"]: v["dwt_tonnes"] for v in vessel_classes
    }

    feasible_class_names = {item["class"] for item in feasible_vessels}

    best_class = None
    best_excess = float("inf")

    for class_name in feasible_class_names:
        dwt = dwt_lookup.get(class_name)
        if dwt is None:
            continue
        excess = dwt - cargo_tonnage  # guaranteed >= 0 by feasibility check
        if excess < best_excess:
            best_excess = excess
            best_class = class_name

    return best_class


def analyze_vessel_optimization(
    cargo_tonnage: float,
    commodity: str,
    origin: str,
    destination_port: str,
    required_date: str,
    num_voyages: int,
    freight_rate_usd_per_tonne: float,
) -> Dict[str, Any]:
    """
    Orchestrate feasibility, voyage cost, and idle-time estimation for a
    given shipment requirement.

    Args:
        cargo_tonnage: Required cargo weight in tonnes.
        commodity: Commodity type (informational, not used in calculations).
        origin: Load port country/region (e.g. "Australia", "Indonesia").
        destination_port: Destination port name (e.g. "Paradip").
        required_date: Required arrival date string (informational).
        num_voyages: Number of voyages to estimate idle time over.
        freight_rate_usd_per_tonne: Freight rate per tonne in USD.

    Returns:
        Dict with exactly 3 top-level keys:
        {
            "vessel_feasibility": {...},   # output of check_feasibility
            "voyage_cost": {...} or None,  # output of estimate_voyage_cost
            "idle_management": {...}       # output of estimate_idle_time
        }
    """
    if num_voyages < 1:
        raise ValueError("num_voyages must be at least 1")
    if cargo_tonnage <= 0:
        raise ValueError("cargo_tonnage must be positive")
    if not destination_port or not origin:
        raise ValueError("destination_port and origin are required")

    # Step 1: Vessel-port feasibility check
    vessel_feasibility = check_feasibility(
        cargo_tonnage=cargo_tonnage,
        destination_port=destination_port,
    )

    # Step 2: Select the most size-efficient feasible vessel
    selected_vessel_class = _find_most_efficient_vessel(
        feasible_vessels=vessel_feasibility["feasible"],
        cargo_tonnage=cargo_tonnage,
    )

    # Step 3: Voyage cost estimation (only if a vessel was selected)
    if selected_vessel_class is not None:
        voyage_cost = estimate_voyage_cost(
            cargo_tonnage=cargo_tonnage,
            origin=origin,
            destination_port=destination_port,
            vessel_class=selected_vessel_class,
            freight_rate_usd_per_tonne=freight_rate_usd_per_tonne,
            waiting_days=0,
            num_voyages=num_voyages,
        )
    else:
        voyage_cost = None

    # Step 4: Idle-time estimation (always computed regardless of feasibility)
    idle_management = estimate_idle_time(
        destination_port=destination_port,
        num_voyages=num_voyages,
    )

    # Step 5: Return exactly 3 top-level keys
    return {
        "vessel_feasibility": vessel_feasibility,
        "voyage_cost": voyage_cost,
        "idle_management": idle_management,
    }
