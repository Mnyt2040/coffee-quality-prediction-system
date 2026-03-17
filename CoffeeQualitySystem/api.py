"""Minimal FastAPI service exposing prediction and health endpoints.

This is optional and does not replace the Streamlit UI. It simply reuses the
existing CoffeeModel and Database components so you can integrate with other
systems programmatically.
"""

from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from models import coffee_model
from database import db


class PredictionRequest(BaseModel):
    data: Dict[str, Any]


app = FastAPI(title="Coffee Quality API", version="1.0.0")


@app.get("/health")
def health() -> Dict[str, Any]:
    """Basic health check including model status."""
    return {
        "status": "ok",
        "model": coffee_model.health_check(),
    }


@app.post("/predict")
def predict(req: PredictionRequest) -> Dict[str, Any]:
    """Run a prediction for a single sample."""
    result = coffee_model.predict(req.data)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result)
    # No user context here; persistence is handled only in the Streamlit app.
    return result

