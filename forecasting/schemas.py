"""
Pydantic schemas matching the exact API contract for Forecasting & Analytics.
"""

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class ForecastHorizon(BaseModel):
    """
    Represents projected freight rates across multiple time horizons (7, 14, and 30 days).
    Uses aliases ('7d', '14d', '30d') to strictly match the API JSON specification.
    """
    model_config = ConfigDict(populate_by_name=True)

    d7: float = Field(..., alias="7d", description="Projected rate 7 days ahead in USD/tonne")
    d14: float = Field(..., alias="14d", description="Projected rate 14 days ahead in USD/tonne")
    d30: float = Field(..., alias="30d", description="Projected rate 30 days ahead in USD/tonne")


class ForecastResult(BaseModel):
    """
    Represents the freight rate forecasting model output.
    """
    model_config = ConfigDict(populate_by_name=True)

    current_rate: float = Field(..., description="Latest recorded freight rate in USD/tonne")
    horizon: ForecastHorizon = Field(..., description="Forecasted rates for 7, 14, and 30 days")
    volatility: Literal["low", "medium", "high"] = Field(
        ..., description="30-day volatility classification ('low', 'medium', 'high')"
    )


class CharterTimingResult(BaseModel):
    """
    Represents actionable charter timing recommendations for charterers and shippers.
    """
    model_config = ConfigDict(populate_by_name=True)

    condition: str = Field(..., description="Current market condition relative to 60-day median")
    suggested_window: str = Field(..., description="Recommended chartering window (e.g. 'next 7-10 days')")
    reason: str = Field(..., description="Detailed English explanation backing the recommendation")


class CombinedOutput(BaseModel):
    """
    Combined output payload containing both forecast and charter timing data.
    """
    model_config = ConfigDict(populate_by_name=True)

    forecast: ForecastResult
    charter_timing: CharterTimingResult
