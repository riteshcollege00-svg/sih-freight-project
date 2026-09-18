# Forecasting & Analytics Module

The **Forecasting & Analytics** module provides time-series freight-rate forecasting and data-driven charter-timing recommendations for the SIH bulk cargo logistics project. Using Holt-Winters exponential smoothing and 30-day Coefficient of Variation volatility analysis, it projects rates across 7, 14, and 30-day horizons and evaluates trailing 60-day medians to advise charterers on optimal vessel procurement windows.

---

## Quick Start (Local Setup)

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the FastAPI internal service:
   ```bash
   uvicorn forecasting.api:app --reload --port 8001
   ```

Interactive Swagger UI documentation is available at [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs).

---

## API Endpoints

### 1. `GET /internal/health`
Health check endpoint to verify service status.

**Response:**
```json
{
  "status": "ok"
}
```

### 2. `POST /internal/forecast`
Generates time-series freight rate forecasts and charter timing advice.

**Sample Request Body:**
```json
{
  "cargo_tonnage": 50000,
  "commodity": "coal",
  "origin": "Australia",
  "destination_port": "Paradip",
  "required_date": "2026-10-15"
}
```

**Sample Response Body:**
```json
{
  "forecast": {
    "current_rate": 14.2,
    "horizon": {
      "7d": 14.6,
      "14d": 15.1,
      "30d": 15.9
    },
    "volatility": "medium"
  },
  "charter_timing": {
    "condition": "rates below 60-day median",
    "suggested_window": "next 7-10 days",
    "reason": "Current rate (14.20 USD/t) is 4.5% below the 60-day median (14.87 USD/t) with moderate volatility. Recommended to enter the chartering market within 7 to 10 days."
  }
}
```

---

> [!NOTE]
> Currently uses synthetic data (`synthetic_data.py`). Once Member 1's PostgreSQL `freight_rates` table is ready, replace the call to `generate_synthetic_rates()` in `api.py` with a real DB query — the rest of the pipeline (`forecast_freight_rate`, `get_charter_timing`) does not need to change.

---

## Running Tests

Run the full pytest suite (domain logic + API endpoints):
```bash
pytest forecasting/tests/
```
