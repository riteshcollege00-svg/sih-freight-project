"""
Forecasting & Analytics Module for Freight-Rate Forecasting System.

Provides synthetic data generation, Holt-Winters exponential smoothing time-series
forecasting, data-driven charter timing recommendations, and a FastAPI internal service.
"""

from .synthetic_data import generate_synthetic_rates
from .forecasting_model import forecast_freight_rate
from .charter_timing import get_charter_timing
from .schemas import ForecastHorizon, ForecastResult, CharterTimingResult, ForecastRequest, CombinedOutput
from .api import app

__all__ = [
    "app",
    "generate_synthetic_rates",
    "forecast_freight_rate",
    "get_charter_timing",
    "ForecastHorizon",
    "ForecastResult",
    "CharterTimingResult",
    "ForecastRequest",
    "CombinedOutput",
]
