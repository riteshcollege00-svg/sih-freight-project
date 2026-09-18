"""
Synthetic Data Generator for Freight Rates.

Generates realistic historical freight rate time-series data with trend,
weekly seasonality/noise, and random volatility spikes. Accepts any commodity,
origin, and destination strings.
"""

import zlib
import numpy as np
import pandas as pd


def generate_synthetic_rates(
    commodity: str,
    origin: str,
    destination_port: str,
    start_date: str,
    num_days: int = 180,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generates synthetic historical freight rate data (in USD/tonne).

    Parameters:
    -----------
    commodity : str
        The bulk commodity type (e.g., 'coal', 'iron_ore', 'wheat').
    origin : str
        Origin port or country (e.g., 'Australia', 'Brazil').
    destination_port : str
        Destination port (e.g., 'Paradip', 'Santos').
    start_date : str
        Start date string in 'YYYY-MM-DD' format.
    num_days : int
        Total number of daily historical data points to generate (default 180).
    seed : int
        Fixed random seed for deterministic, reproducible results.

    Returns:
    --------
    pd.DataFrame
        DataFrame with columns ["date", "rate"].
    """
    # Use deterministic zlib Adler32 hashing across string inputs for process-independent reproducibility
    route_key = f"{commodity.strip().lower()}:{origin.strip().lower()}:{destination_port.strip().lower()}"
    route_hash = zlib.adler32(route_key.encode("utf-8")) % 10000

    np.random.seed(seed + route_hash)

    # Base parameters for freight rate (USD / tonne)
    base_rate = 15.0 + (route_hash % 15)  # Typical freight rate around 15-30 USD/tonne

    # 1. Linear trend (slow drift upward or downward over time)
    trend_slope = np.random.uniform(-0.02, 0.03)  # Daily slope
    trend = np.linspace(0, trend_slope * num_days, num_days)

    # 2. Weekly seasonality / noise (7-day periodic wave representing weekly port operations)
    t = np.arange(num_days)
    weekly_seasonality = 0.5 * np.sin(2 * np.pi * t / 7)
    daily_noise = np.random.normal(0, 0.3, num_days)

    # 3. Occasional volatility spikes (simulating port congestion, fuel price shocks, weather)
    spikes = np.zeros(num_days)
    num_spikes = int(num_days * 0.03)  # ~3% of days have spikes
    if num_spikes > 0:
        spike_indices = np.random.choice(num_days, size=num_spikes, replace=False)
        spikes[spike_indices] = np.random.uniform(1.5, 4.0, size=num_spikes) * np.random.choice([-1, 1], size=num_spikes)

    # Combine components
    rates = base_rate + trend + weekly_seasonality + daily_noise + spikes
    # Ensure rates remain strictly positive (minimum rate threshold of 5.0 USD/tonne)
    rates = np.maximum(rates, 5.0)
    rates = np.round(rates, 2)

    # Generate daily date range
    date_range = pd.date_range(start=start_date, periods=num_days, freq="D")
    date_strings = date_range.strftime("%Y-%m-%d")

    df = pd.DataFrame({
        "date": date_strings,
        "rate": rates
    })

    return df
