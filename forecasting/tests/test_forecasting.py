"""
Unit tests for the Forecasting & Analytics module.
"""

import pytest
import pandas as pd

from forecasting.synthetic_data import generate_synthetic_rates
from forecasting.forecasting_model import forecast_freight_rate
from forecasting.charter_timing import get_charter_timing
from forecasting.schemas import ForecastResult, CharterTimingResult, CombinedOutput


@pytest.fixture
def sample_synthetic_data():
    """Fixture providing synthetic freight rate data for coal Australia -> Paradip."""
    return generate_synthetic_rates(
        commodity="coal",
        origin="Australia",
        destination_port="Paradip",
        start_date="2024-01-01",
        num_days=180
    )


def test_generate_synthetic_rates_structure(sample_synthetic_data):
    """Test synthetic data generator output shape, columns, and reproducibility."""
    df = sample_synthetic_data
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["date", "rate"]
    assert len(df) == 180
    assert (df["rate"] > 0).all()

    # Test seed reproducibility
    df2 = generate_synthetic_rates(
        commodity="coal",
        origin="Australia",
        destination_port="Paradip",
        start_date="2024-01-01",
        num_days=180
    )
    pd.testing.assert_frame_equal(df, df2)


def test_forecast_freight_rate(sample_synthetic_data):
    """Test forecast_freight_rate model execution, keys, data types, and Pydantic validation."""
    history_df = sample_synthetic_data
    as_of_date = history_df["date"].iloc[-1]

    result = forecast_freight_rate(
        commodity="coal",
        origin="Australia",
        destination_port="Paradip",
        as_of_date=as_of_date,
        history_df=history_df
    )

    # Check top-level keys
    assert "current_rate" in result
    assert "horizon" in result
    assert "volatility" in result

    # Check types & values
    assert isinstance(result["current_rate"], float)
    assert result["current_rate"] > 0
    assert result["volatility"] in ["low", "medium", "high"]

    # Check horizon keys & values
    horizon = result["horizon"]
    assert "7d" in horizon
    assert "14d" in horizon
    assert "30d" in horizon
    assert isinstance(horizon["7d"], float)
    assert isinstance(horizon["14d"], float)
    assert isinstance(horizon["30d"], float)

    # Validate schema compatibility with Pydantic model
    validated_model = ForecastResult(**result)
    assert validated_model.current_rate == result["current_rate"]


def test_get_charter_timing(sample_synthetic_data):
    """Test get_charter_timing recommendation engine keys, non-empty strings, and schema."""
    history_df = sample_synthetic_data

    result = get_charter_timing(
        commodity="coal",
        origin="Australia",
        destination_port="Paradip",
        history_df=history_df
    )

    # Check top-level keys
    assert "condition" in result
    assert "suggested_window" in result
    assert "reason" in result

    # Assert non-empty string values
    assert isinstance(result["condition"], str) and len(result["condition"].strip()) > 0
    assert isinstance(result["suggested_window"], str) and len(result["suggested_window"].strip()) > 0
    assert isinstance(result["reason"], str) and len(result["reason"].strip()) > 0

    # Validate schema compatibility with Pydantic model
    validated_model = CharterTimingResult(**result)
    assert validated_model.condition == result["condition"]


def test_combined_schema_integration(sample_synthetic_data):
    """Test combined payload matching the full API contract."""
    history_df = sample_synthetic_data
    as_of_date = history_df["date"].iloc[-1]

    forecast_res = forecast_freight_rate(
        commodity="coal",
        origin="Australia",
        destination_port="Paradip",
        as_of_date=as_of_date,
        history_df=history_df
    )

    timing_res = get_charter_timing(
        commodity="coal",
        origin="Australia",
        destination_port="Paradip",
        history_df=history_df
    )

    combined_payload = {
        "forecast": forecast_res,
        "charter_timing": timing_res
    }

    # Validate against CombinedOutput Pydantic model
    validated_output = CombinedOutput(**combined_payload)
    dumped = validated_output.model_dump(by_alias=True)

    assert "forecast" in dumped
    assert "charter_timing" in dumped
    assert "7d" in dumped["forecast"]["horizon"]
