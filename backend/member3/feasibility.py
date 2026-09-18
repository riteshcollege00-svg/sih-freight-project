"""
Feasibility module for vessel-port compatibility.
Evaluates whether vessel classes satisfy port dimensions and cargo requirements.

Data source: real database via data.db (Member 1's data layer).
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.db import db


def _format_dim(val: Union[int, float]) -> str:
    """Format dimension value with 'm' suffix."""
    return f"{val}m"


def _format_tonnage(val: Union[int, float]) -> str:
    """Format weight/tonnage value with 't' suffix."""
    return f"{val}t"


def _load_vessels() -> List[Dict[str, Any]]:
    """Fetch vessel class specifications from the database."""
    rows = db.fetch_all(
        "SELECT vessel_class, dwt, cargo_capacity_mt, loa_m, beam_m, draft_m FROM vessels"
    )
    return [
        {
            "class": row[0],
            "dwt": float(row[1]),
            "cargo_capacity_mt": float(row[2]),
            "loa_m": float(row[3]),
            "beam_m": float(row[4]),
            "draft_m": float(row[5]),
        }
        for row in rows
    ]


def _load_port(destination_port: str) -> Optional[Dict[str, Any]]:
    """Fetch port physical limits from the database (case-insensitive name match)."""
    rows = db.fetch_all(
        "SELECT port_id, port_name, max_draft_m, max_loa_m, max_beam_m FROM ports"
    )
    normalized = destination_port.strip().lower()
    for row in rows:
        if row[1].strip().lower() == normalized:
            return {
                "port_id": row[0],
                "port_name": row[1],
                "max_draft_m": float(row[2]),
                "max_loa_m": float(row[3]),
                "max_beam_m": float(row[4]),
            }
    return None


def load_vessel_classes(filepath=None) -> List[Dict[str, Any]]:
    """Load vessel class definitions from the database.

    The filepath parameter is accepted for backward compatibility but ignored —
    data is always fetched from the real database.
    """
    return _load_vessels()


def check_feasibility(cargo_tonnage: float, destination_port: str, **kwargs) -> Dict[str, List[Dict[str, str]]]:
    """
    Check vessel-port compatibility based on port physical constraints and cargo tonnage.

    Args:
        cargo_tonnage: Required cargo weight in tonnes.
        destination_port: Name of the destination port.

    Returns:
        Dict matching exact shape:
        {
            "feasible": [{"class": ..., "notes": "meets all port limits"}],
            "infeasible": [{"class": ..., "reason": ...}]
        }
    """
    vessels = _load_vessels()
    port_data = _load_port(destination_port)

    if not port_data:
        available = [
            row[0] for row in db.fetch_all("SELECT port_name FROM ports")
        ]
        raise ValueError(
            f"Destination port '{destination_port}' not found in ports table. "
            f"Available ports: {available}"
        )

    max_draft = port_data["max_draft_m"]
    max_loa = port_data["max_loa_m"]
    max_beam = port_data["max_beam_m"]

    feasible: List[Dict[str, str]] = []
    infeasible: List[Dict[str, str]] = []

    for vessel in vessels:
        vessel_class = vessel["class"]
        draft = vessel["draft_m"]
        loa = vessel["loa_m"]
        beam = vessel["beam_m"]
        capacity = vessel["cargo_capacity_mt"]

        reasons = []

        if draft > max_draft:
            reasons.append(f"exceeds max draft ({_format_dim(draft)} > {_format_dim(max_draft)})")
        if loa > max_loa:
            reasons.append(f"exceeds max LOA ({_format_dim(loa)} > {_format_dim(max_loa)})")
        if beam > max_beam:
            reasons.append(f"exceeds max beam ({_format_dim(beam)} > {_format_dim(max_beam)})")
        if cargo_tonnage > capacity:
            reasons.append(
                f"cargo exceeds cargo capacity ({_format_tonnage(cargo_tonnage)} > {_format_tonnage(capacity)})"
            )

        if reasons:
            infeasible.append({"class": vessel_class, "reason": ", ".join(reasons)})
        else:
            feasible.append({"class": vessel_class, "notes": "meets all port limits"})

    return {
        "feasible": feasible,
        "infeasible": infeasible,
    }
