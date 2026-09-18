"""
Unit tests for the FastAPI internal forecasting service including validation and edge cases.
"""

import pytest
from fastapi.testclient import TestClient
from forecasting.api import app

client = TestClient(app)


def test_health_endpoint():
    """Test GET /internal/health returns HTTP 200 and {'status': 'ok'}."""
    response = client.get("/internal/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_forecast_endpoint_valid():
    """Test POST /internal/forecast returns combined forecast and charter timing response."""
    payload = {
        "cargo_tonnage": 50000,
        "commodity": "coal",
        "origin": "Australia",
        "destination_port": "Paradip",
        "required_date": "2026-10-15"
    }

    response = client.post("/internal/forecast", json=payload)
    assert response.status_code == 200

    data = response.json()

    # Assert top-level response keys
    assert "forecast" in data
    assert "charter_timing" in data

    # Assert forecast structure & sub-keys
    forecast = data["forecast"]
    assert "current_rate" in forecast
    assert "horizon" in forecast
    assert "volatility" in forecast
    assert isinstance(forecast["current_rate"], float)
    assert forecast["volatility"] in ["low", "medium", "high"]

    horizon = forecast["horizon"]
    assert "7d" in horizon
    assert "14d" in horizon
    assert "30d" in horizon

    # Assert charter_timing structure & sub-keys
    charter_timing = data["charter_timing"]
    assert "condition" in charter_timing
    assert "suggested_window" in charter_timing
    assert "reason" in charter_timing


def test_forecast_negative_cargo_tonnage():
    """Test POST /internal/forecast with negative cargo_tonnage returns HTTP 422."""
    payload = {
        "cargo_tonnage": -5,
        "commodity": "coal",
        "origin": "Australia",
        "destination_port": "Paradip",
        "required_date": "2026-10-15"
    }
    response = client.post("/internal/forecast", json=payload)
    assert response.status_code == 422
    assert "cargo_tonnage must be a positive number" in response.json().get("detail", "")


def test_forecast_zero_cargo_tonnage():
    """Test POST /internal/forecast with zero cargo_tonnage returns HTTP 422."""
    payload = {
        "cargo_tonnage": 0,
        "commodity": "coal",
        "origin": "Australia",
        "destination_port": "Paradip",
        "required_date": "2026-10-15"
    }
    response = client.post("/internal/forecast", json=payload)
    assert response.status_code == 422
    assert "cargo_tonnage must be a positive number" in response.json().get("detail", "")


def test_forecast_missing_cargo_tonnage():
    """Test POST /internal/forecast with missing cargo_tonnage returns HTTP 422."""
    payload = {
        "commodity": "coal",
        "origin": "Australia",
        "destination_port": "Paradip",
        "required_date": "2026-10-15"
    }
    response = client.post("/internal/forecast", json=payload)
    assert response.status_code == 422
    assert "detail" in response.json()


def test_forecast_empty_commodity():
    """Test POST /internal/forecast with empty commodity string returns HTTP 422."""
    payload = {
        "cargo_tonnage": 50000,
        "commodity": "",
        "origin": "Australia",
        "destination_port": "Paradip",
        "required_date": "2026-10-15"
    }
    response = client.post("/internal/forecast", json=payload)
    assert response.status_code == 422
    assert "commodity must not be empty" in response.json().get("detail", "")


def test_forecast_empty_origin():
    """Test POST /internal/forecast with whitespace/empty origin returns HTTP 422."""
    payload = {
        "cargo_tonnage": 50000,
        "commodity": "coal",
        "origin": "   ",
        "destination_port": "Paradip",
        "required_date": "2026-10-15"
    }
    response = client.post("/internal/forecast", json=payload)
    assert response.status_code == 422
    assert "origin must not be empty" in response.json().get("detail", "")


def test_forecast_empty_destination_port():
    """Test POST /internal/forecast with empty destination_port returns HTTP 422."""
    payload = {
        "cargo_tonnage": 50000,
        "commodity": "coal",
        "origin": "Australia",
        "destination_port": "",
        "required_date": "2026-10-15"
    }
    response = client.post("/internal/forecast", json=payload)
    assert response.status_code == 422
    assert "destination_port must not be empty" in response.json().get("detail", "")


def test_forecast_invalid_required_date():
    """Test POST /internal/forecast with malformed required_date returns HTTP 422."""
    payload = {
        "cargo_tonnage": 50000,
        "commodity": "coal",
        "origin": "Australia",
        "destination_port": "Paradip",
        "required_date": "not-a-date"
    }
    response = client.post("/internal/forecast", json=payload)
    assert response.status_code == 422
    assert "invalid required_date format" in response.json().get("detail", "")


def test_forecast_unusual_inputs():
    """Test POST /internal/forecast with unusual commodity ('wheat') and origin ('Brazil') returns HTTP 200."""
    payload = {
        "cargo_tonnage": 35000,
        "commodity": "wheat",
        "origin": "Brazil",
        "destination_port": "Santos",
        "required_date": "2026-11-20"
    }
    response = client.post("/internal/forecast", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "forecast" in data
    assert "charter_timing" in data
    assert "current_rate" in data["forecast"]
    assert "7d" in data["forecast"]["horizon"]
    assert "14d" in data["forecast"]["horizon"]
    assert "30d" in data["forecast"]["horizon"]
    assert "condition" in data["charter_timing"]
    assert "suggested_window" in data["charter_timing"]
    assert "reason" in data["charter_timing"]


def test_forecast_internal_error_handling(monkeypatch):
    """Test that unexpected server exceptions return HTTP 500 with proper error JSON structure."""
    import forecasting.api as api_module

    def mock_broken_rates(*args, **kwargs):
        raise RuntimeError("Simulated calculation failure")

    monkeypatch.setattr(api_module, "generate_synthetic_rates", mock_broken_rates)

    payload = {
        "cargo_tonnage": 50000,
        "commodity": "coal",
        "origin": "Australia",
        "destination_port": "Paradip",
        "required_date": "2026-10-15"
    }
    response = client.post("/internal/forecast", json=payload)
    assert response.status_code == 500
    json_data = response.json()
    assert json_data.get("error") == "Internal forecasting error"
    assert "Simulated calculation failure" in json_data.get("detail", "")

