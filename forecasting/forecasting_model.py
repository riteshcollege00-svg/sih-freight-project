"""
Time-Series Freight Rate Forecasting Model.

Uses statsmodels' Holt-Winters Exponential Smoothing (with trend projection)
to forecast freight rates 7, 14, and 30 days ahead, and computes market volatility
based on the Coefficient of Variation over the last 30 days.
"""

from typing import Dict, Any
import numpy as np
import pandas as pd

from .schemas import ForecastResult, ForecastHorizon


def _compute_volatility(rates: np.ndarray) -> str:
    """
    Computes volatility category ('low', 'medium', 'high') based on the
    Coefficient of Variation (CV = std / mean) over the last 30 days.

    Thresholds:
    - CV < 5%   (< 0.05): 'low'
    - 5% <= CV <= 15% (0.05 to 0.15): 'medium'
    - CV > 15%  (> 0.15): 'high'
    """
    last_30 = rates[-30:] if len(rates) >= 30 else rates
    mean_val = float(np.mean(last_30))
    std_val = float(np.std(last_30, ddof=1)) if len(last_30) > 1 else 0.0

    if mean_val <= 0:
        return "low"

    cv = std_val / mean_val

    if cv < 0.05:
        return "low"
    elif cv <= 0.15:
        return "medium"
    else:
        return "high"


def forecast_freight_rate(
    commodity: str,
    origin: str,
    destination_port: str,
    as_of_date: str,
    history_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Projects freight rates 7, 14, and 30 days into the future from `as_of_date`.

    Parameters:
    -----------
    commodity : str
        Bulk commodity name.
    origin : str
        Origin port/country.
    destination_port : str
        Destination port name.
    as_of_date : str
        Cut-off date for historical data filtering ('YYYY-MM-DD').
    history_df : pd.DataFrame
        Historical DataFrame containing at least ["date", "rate"] columns.

    Returns:
    --------
    dict
        Dict matching exact ForecastResult JSON shape:
        {
            "current_rate": 14.2,
            "horizon": {"7d": 14.6, "14d": 15.1, "30d": 15.9},
            "volatility": "medium"
        }
    """
    # Clean and filter historical data up to as_of_date
    df = history_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    as_of_dt = pd.to_datetime(as_of_date)

    filtered_df = df[df["date"] <= as_of_dt].sort_values("date")

    if filtered_df.empty:
        # Fallback to entire history if as_of_date is prior to historical start
        filtered_df = df.sort_values("date")

    rates = filtered_df["rate"].astype(float).values

    if len(rates) == 0:
        raise ValueError("Historical rates DataFrame is empty.")

    current_rate = float(rates[-1])
    volatility = _compute_volatility(rates)

    # Perform forecasting: Try Holt-Winters Exponential Smoothing first
    f7, f14, f30 = None, None, None

    if len(rates) >= 14:
        try:
            from statsmodels.tsa.api import ExponentialSmoothing

            # Fit Holt's additive trend model (no seasonality needed for daily drift projection)
            model = ExponentialSmoothing(
                rates,
                trend="add",
                seasonal=None,
                initialization_method="estimated"
            )
            fit_model = model.fit(disp=False)
            predictions = fit_model.forecast(steps=30)

            f7 = float(predictions[6])   # 7 days ahead (index 6)
            f14 = float(predictions[13]) # 14 days ahead (index 13)
            f30 = float(predictions[29]) # 30 days ahead (index 29)
        except Exception:
            # Fall back to weighted moving average if statsmodels fails or encounters numerical instability
            f7, f14, f30 = None, None, None

    # Fallback to Weighted Moving Average (WMA) with linear trend extrapolation
    if f7 is None or f14 is None or f30 is None:
        window = min(len(rates), 14)
        weights = np.arange(1, window + 1)
        wma = np.sum(rates[-window:] * weights) / np.sum(weights)

        # Estimate trend over last window
        trend_per_day = (current_rate - rates[-window]) / window if window > 1 else 0.0

        f7 = wma + trend_per_day * 7
        f14 = wma + trend_per_day * 14
        f30 = wma + trend_per_day * 30

    # Ensure forecasted rates remain positive and reasonably bounded
    f7 = max(round(float(f7), 2), 1.0)
    f14 = max(round(float(f14), 2), 1.0)
    f30 = max(round(float(f30), 2), 1.0)
    current_rate = round(float(current_rate), 2)

    # Validate and construct output matching Pydantic schema
    forecast_data = ForecastResult(
        current_rate=current_rate,
        horizon=ForecastHorizon(**{"7d": f7, "14d": f14, "30d": f30}),
        volatility=volatility
    )

    return forecast_data.model_dump(by_alias=True)
