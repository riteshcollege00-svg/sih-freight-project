"""
Unit tests for the FastAPI internal forecasting service.
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


def test_forecast_endpoint():
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
    assert len(charter_timing["condition"].strip()) > 0
    assert len(charter_timing["suggested_window"].strip()) > 0
    assert len(charter_timing["reason"].strip()) > 0
