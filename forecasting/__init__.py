"""
Forecasting & Analytics Module for Freight-Rate Forecasting System.

Provides synthetic data generation, Holt-Winters exponential smoothing time-series
forecasting, and data-driven charter timing recommendations.
"""

from .synthetic_data import generate_synthetic_rates
from .forecasting_model import forecast_freight_rate
from .charter_timing import get_charter_timing
from .schemas import ForecastHorizon, ForecastResult, CharterTimingResult

__all__ = [
    "generate_synthetic_rates",
    "forecast_freight_rate",
    "get_charter_timing",
    "ForecastHorizon",
    "ForecastResult",
    "CharterTimingResult",
]
