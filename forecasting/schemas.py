"""
Pydantic schemas matching the exact API contract for Forecasting & Analytics.
Includes field validators for strict input sanitization.
"""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ForecastRequest(BaseModel):
    """
    Request model for the internal forecast API endpoint.
    """
    model_config = ConfigDict(populate_by_name=True)

    cargo_tonnage: float = Field(..., description="Cargo tonnage in metric tonnes (e.g. 50000)")
    commodity: str = Field(..., description="Bulk commodity name (e.g. 'coal')")
    origin: str = Field(..., description="Origin port or country (e.g. 'Australia')")
    destination_port: str = Field(..., description="Destination port name (e.g. 'Paradip')")
    required_date: str = Field(..., description="Target required date in YYYY-MM-DD format (e.g. '2026-10-15')")

    @field_validator("cargo_tonnage")
    @classmethod
    def validate_cargo_tonnage(cls, value: float) -> float:
        if value is None or value <= 0:
            raise ValueError("cargo_tonnage must be a positive number")
        return value

    @field_validator("commodity", "origin", "destination_port")
    @classmethod
    def validate_non_empty_string(cls, value: str, info) -> str:
        if not value or not str(value).strip():
            raise ValueError(f"{info.field_name} must not be empty")
        return value.strip()

    @field_validator("required_date")
    @classmethod
    def validate_required_date(cls, value: str) -> str:
        if not value or not str(value).strip():
            raise ValueError("required_date must not be empty")
        try:
            datetime.strptime(value.strip(), "%Y-%m-%d")
        except ValueError:
            raise ValueError("invalid required_date format, expected YYYY-MM-DD")
        return value.strip()


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
