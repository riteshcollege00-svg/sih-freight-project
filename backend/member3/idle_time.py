"""
Idle-time and alternative-employment estimation module.
Estimates vessel waiting times at destination ports and suggests backhaul employment options.

Data source:
- avg_turnaround_days: real database via data.db (Member 1's data layer).
- backhaul_suggestions: local backhaul_suggestions.json (no DB equivalent in schema).
"""

import sys
from pathlib import Path
import json
from typing import Any, Dict, Optional, Union

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.db import db

DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_BACKHAUL_FILE = DATA_DIR / "backhaul_suggestions.json"


def _load_backhaul(filepath: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    path = Path(filepath) if filepath else DEFAULT_BACKHAUL_FILE
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_avg_turnaround(destination_port: str) -> tuple:
    """Fetch avg_turnaround_days for a port by name (case-insensitive) from the DB."""
    rows = db.fetch_all("SELECT port_name, avg_turnaround_days FROM ports")
    normalized = destination_port.strip().lower()
    for row in rows:
        if row[0].strip().lower() == normalized:
            return row[0], float(row[1])
    available = [row[0] for row in rows]
    raise ValueError(
        f"Destination port '{destination_port}' not found in ports table. "
        f"Available ports: {available}"
    )


def estimate_idle_time(
    destination_port: str,
    num_voyages: int,
    port_idle_path: Optional[Union[str, Path]] = None,
    backhaul_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """
    Estimate expected idle days and suggest alternative backhaul employment.

    Args:
        destination_port: Name of the destination port.
        num_voyages: Number of voyages planned.
        port_idle_path: Deprecated (accepted for backward compat, ignored — DB used).
        backhaul_path: Optional custom path to backhaul_suggestions.json.

    Returns:
        Dict matching exact shape:
        {
            "expected_idle_days": 2.5,
            "alternative_employment": "backhaul option on Indonesia route"
        }

    Raises:
        ValueError: If destination_port is not found in the database.
    """
    # avg_turnaround_days from real database
    port_name_db, avg_turnaround = _get_avg_turnaround(destination_port)
    expected_idle_days = round(avg_turnaround * num_voyages, 1)

    # Backhaul suggestions remain from local JSON (no DB equivalent)
    backhaul_data = _load_backhaul(backhaul_path)
    normalized = destination_port.strip().lower()
    backhaul_key = next(
        (k for k in backhaul_data.keys() if k.strip().lower() == normalized), None
    )

    if not backhaul_key:
        # Fallback: no suggestion available
        alternative_employment = "no backhaul suggestion available"
    else:
        backhaul_origin = backhaul_data[backhaul_key]["nearest_origin"]
        alternative_employment = f"backhaul option on {backhaul_origin} route"

    return {
        "expected_idle_days": expected_idle_days,
        "alternative_employment": alternative_employment,
    }
