"""
Charter Timing Recommendation Engine.

Evaluates historical freight rates against trailing 60-day medians and short-term
volatility to generate actionable, plain-English chartering recommendations.
"""

from typing import Dict, Any
import numpy as np
import pandas as pd

from .schemas import CharterTimingResult
from .forecasting_model import _compute_volatility


def get_charter_timing(
    commodity: str,
    origin: str,
    destination_port: str,
    history_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Computes charter timing recommendation based on trailing 60-day median rate
    and recent volatility.

    Parameters:
    -----------
    commodity : str
        Bulk commodity name.
    origin : str
        Origin port or country.
    destination_port : str
        Destination port name.
    history_df : pd.DataFrame
        Historical DataFrame containing at least ["date", "rate"] columns.

    Returns:
    --------
    dict
        Dict matching exact CharterTimingResult JSON shape:
        {
            "condition": "rates below 60-day median",
            "suggested_window": "next 7-10 days",
            "reason": "Current freight rate is 4.5% below the trailing 60-day median..."
        }
    """
    if history_df.empty:
        raise ValueError("Historical rates DataFrame is empty.")

    rates = history_df["rate"].astype(float).values
    current_rate = float(rates[-1])

    # Calculate 60-day trailing median rate
    last_60 = rates[-60:] if len(rates) >= 60 else rates
    median_60 = float(np.median(last_60))

    # Calculate 30-day market volatility
    volatility = _compute_volatility(rates)

    # Determine market condition relative to 60-day median
    if current_rate < median_60:
        diff_pct = ((median_60 - current_rate) / median_60) * 100.0
        condition = "rates below 60-day median"

        if volatility == "low":
            suggested_window = "next 3-5 days"
            reason = (
                f"Current rate ({current_rate:.2f} USD/t) is {diff_pct:.1f}% below the 60-day median "
                f"({median_60:.2f} USD/t) with low market volatility. Optimal window to lock in long-term or spot charters early."
            )
        elif volatility == "medium":
            suggested_window = "next 7-10 days"
            reason = (
                f"Current rate ({current_rate:.2f} USD/t) is {diff_pct:.1f}% below the 60-day median "
                f"({median_60:.2f} USD/t) with moderate volatility. Recommended to enter the chartering market within 7 to 10 days."
            )
        else:  # high volatility
            suggested_window = "next 5-7 days"
            reason = (
                f"Current rate ({current_rate:.2f} USD/t) is below the 60-day median, but high market volatility "
                f"indicates risk of sudden price jumps. Secure vessel capacity within 5 to 7 days."
            )
    else:
        diff_pct = ((current_rate - median_60) / median_60) * 100.0
        condition = "rates above 60-day median"

        if volatility == "high":
            suggested_window = "wait 14-21 days"
            reason = (
                f"Current rate ({current_rate:.2f} USD/t) is {diff_pct:.1f}% above the 60-day median "
                f"({median_60:.2f} USD/t) amidst high volatility. Defer spot chartering if possible to allow market correction."
            )
        else:
            suggested_window = "wait 10-14 days"
            reason = (
                f"Current rate ({current_rate:.2f} USD/t) is elevated {diff_pct:.1f}% above the 60-day median "
                f"({median_60:.2f} USD/t). Consider postponing charter commitments for 10-14 days until rates stabilize."
            )

    result = CharterTimingResult(
        condition=condition,
        suggested_window=suggested_window,
        reason=reason
    )

    return result.model_dump(by_alias=True)
