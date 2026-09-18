"""
Idle-time and alternative-employment estimation module.
Estimates vessel waiting times at destination ports and suggests backhaul employment options.
"""

from pathlib import Path
import json
from typing import Any, Dict, Optional, Union

DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_PORT_IDLE_FILE = DATA_DIR / "port_idle_estimates.json"
DEFAULT_BACKHAUL_FILE = DATA_DIR / "backhaul_suggestions.json"


def _load_json(filepath: Path) -> Dict[str, Any]:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def _find_case_insensitive_key(data: Dict[str, Any], key: str) -> Optional[str]:
    normalized = key.strip().lower()
    for k in data.keys():
        if k.strip().lower() == normalized:
            return k
    return None


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
        port_idle_path: Optional custom path to port_idle_estimates.json.
        backhaul_path: Optional custom path to backhaul_suggestions.json.

    Returns:
        Dict matching exact shape:
        {
            "expected_idle_days": 2.5,
            "alternative_employment": "backhaul option on Indonesia route"
        }

    Raises:
        ValueError: If destination_port is not found in the reference data.
    """
    idle_file = Path(port_idle_path) if port_idle_path else DEFAULT_PORT_IDLE_FILE
    backhaul_file = Path(backhaul_path) if backhaul_path else DEFAULT_BACKHAUL_FILE

    idle_data = _load_json(idle_file)
    backhaul_data = _load_json(backhaul_file)

    idle_key = _find_case_insensitive_key(idle_data, destination_port)
    if not idle_key:
        raise ValueError(
            f"Destination port '{destination_port}' not found in port idle estimates. "
            f"Available ports: {list(idle_data.keys())}"
        )

    avg_idle = idle_data[idle_key]["avg_idle_days_per_voyage"]
    expected_idle_days = round(avg_idle * num_voyages, 1)

    backhaul_key = _find_case_insensitive_key(backhaul_data, destination_port)
    if not backhaul_key:
        raise ValueError(
            f"Destination port '{destination_port}' not found in backhaul suggestions."
        )

    backhaul_origin = backhaul_data[backhaul_key]["nearest_origin"]
    alternative_employment = f"backhaul option on {backhaul_origin} route"

    return {
        "expected_idle_days": expected_idle_days,
        "alternative_employment": alternative_employment,
    }
