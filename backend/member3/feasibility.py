"""
Feasibility module for vessel-port compatibility.
Evaluates whether vessel classes satisfy port dimensions and cargo requirements.
"""

from pathlib import Path
import json
from typing import Any, Dict, List, Optional, Union

DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_VESSEL_CLASSES_FILE = DATA_DIR / "vessel_classes.json"
DEFAULT_PORT_LIMITS_FILE = DATA_DIR / "port_limits.json"


def _format_dim(val: Union[int, float]) -> str:
    """Format dimension value with 'm' suffix."""
    return f"{val}m"


def _format_tonnage(val: Union[int, float]) -> str:
    """Format weight/tonnage value with 't' suffix."""
    return f"{val}t"


def load_vessel_classes(filepath: Optional[Union[str, Path]] = None) -> List[Dict[str, Any]]:
    """Load vessel class definitions from JSON file."""
    path = Path(filepath) if filepath else DEFAULT_VESSEL_CLASSES_FILE
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_port_limits(filepath: Optional[Union[str, Path]] = None) -> Dict[str, Dict[str, Any]]:
    """Load port limits from JSON file."""
    path = Path(filepath) if filepath else DEFAULT_PORT_LIMITS_FILE
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return {item["port"]: item for item in data}
    return data


def check_feasibility(
    cargo_tonnage: float,
    destination_port: str,
    vessel_classes_path: Optional[Union[str, Path]] = None,
    port_limits_path: Optional[Union[str, Path]] = None,
) -> Dict[str, List[Dict[str, str]]]:
    """
    Check vessel-port compatibility based on physical port constraints and cargo tonnage.

    Args:
        cargo_tonnage: Required cargo tonnage to be transported.
        destination_port: Name of the destination port.
        vessel_classes_path: Optional custom path to vessel_classes.json.
        port_limits_path: Optional custom path to port_limits.json.

    Returns:
        Dict with exact shape:
        {
            "feasible": [{"class": ..., "notes": "meets all port limits"}],
            "infeasible": [{"class": ..., "reason": ...}]
        }
    """
    vessels = load_vessel_classes(vessel_classes_path)
    ports = load_port_limits(port_limits_path)

    port_data = ports.get(destination_port)
    if not port_data:
        normalized_name = destination_port.strip().lower()
        for p_name, p_limits in ports.items():
            if p_name.strip().lower() == normalized_name:
                port_data = p_limits
                break

    if not port_data:
        raise ValueError(
            f"Destination port '{destination_port}' not found in port limits reference data. "
            f"Available ports: {list(ports.keys())}"
        )

    max_draft = port_data["max_draft_m"]
    max_loa = port_data["max_loa_m"]
    max_beam = port_data["max_beam_m"]

    feasible: List[Dict[str, str]] = []
    infeasible: List[Dict[str, str]] = []

    for vessel in vessels:
        vessel_class = vessel.get("class", vessel.get("name", "Unknown"))
        draft = vessel["draft_m"]
        loa = vessel["loa_m"]
        beam = vessel["beam_m"]
        dwt = vessel["dwt_tonnes"]

        reasons = []

        if draft > max_draft:
            reasons.append(f"exceeds max draft ({_format_dim(draft)} > {_format_dim(max_draft)})")
        if loa > max_loa:
            reasons.append(f"exceeds max LOA ({_format_dim(loa)} > {_format_dim(max_loa)})")
        if beam > max_beam:
            reasons.append(f"exceeds max beam ({_format_dim(beam)} > {_format_dim(max_beam)})")
        if cargo_tonnage > dwt:
            reasons.append(
                f"cargo exceeds deadweight capacity ({_format_tonnage(cargo_tonnage)} > {_format_tonnage(dwt)})"
            )

        if reasons:
            infeasible.append({
                "class": vessel_class,
                "reason": ", ".join(reasons)
            })
        else:
            feasible.append({
                "class": vessel_class,
                "notes": "meets all port limits"
            })

    return {
        "feasible": feasible,
        "infeasible": infeasible
    }
