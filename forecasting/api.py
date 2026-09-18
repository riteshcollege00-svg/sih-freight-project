"""
Internal FastAPI Service for Freight Rate Forecasting & Analytics.

Exposes endpoints for health checks and freight rate forecasting & charter timing
with input validation and graceful error handling.
"""

from datetime import datetime
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from forecasting.schemas import ForecastRequest, CombinedOutput
from forecasting.synthetic_data import generate_synthetic_rates
from forecasting.forecasting_model import forecast_freight_rate
from forecasting.charter_timing import get_charter_timing

app = FastAPI(
    title="Freight Rate Forecasting Service",
    description="Internal API service providing time-series freight rate forecasts and charter timing recommendations.",
    version="1.0.0"
)


@app.exception_handler(RequestValidationError)
def custom_validation_exception_handler(request, exc: RequestValidationError):
    """
    Format FastAPI Pydantic validation errors into clean HTTP 422 responses.
    """
    errors = exc.errors()
    error_msg = errors[0].get("msg", "Invalid input parameters") if errors else "Invalid request body"

    # Strip Pydantic's "Value error, " prefix if present
    if error_msg.startswith("Value error, "):
        error_msg = error_msg.replace("Value error, ", "")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": error_msg}
    )


@app.get("/internal/health", tags=["Health"])
def health_check():
    """
    Health check endpoint to quickly verify service status.
    """
    return {"status": "ok"}


@app.post("/internal/forecast", response_model=CombinedOutput, tags=["Forecasting"])
def get_forecast(request: ForecastRequest):
    """
    Generates time-series freight rate forecast and charter timing recommendation.
    """
    # Core execution wrapped in try/except for 500 safety
    try:
        start_date = datetime.now().strftime("%Y-%m-%d")

        # Generate synthetic historical rate data standing in for DB pipeline
        history_df = generate_synthetic_rates(
            commodity=request.commodity,
            origin=request.origin,
            destination_port=request.destination_port,
            start_date=start_date,
            num_days=180
        )

        as_of_date = history_df["date"].iloc[-1]

        # Compute forecast and charter timing recommendations
        forecast_res = forecast_freight_rate(
            commodity=request.commodity,
            origin=request.origin,
            destination_port=request.destination_port,
            as_of_date=as_of_date,
            history_df=history_df
        )

        charter_timing_res = get_charter_timing(
            commodity=request.commodity,
            origin=request.origin,
            destination_port=request.destination_port,
            history_df=history_df
        )

        return CombinedOutput(
            forecast=forecast_res,
            charter_timing=charter_timing_res
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal forecasting error",
                "detail": str(e)
            }
        )


# Run with: uvicorn forecasting.api:app --reload --port 8001
