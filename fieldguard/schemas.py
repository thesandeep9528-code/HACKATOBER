from __future__ import annotations

from pydantic import BaseModel, Field


class SensorContext(BaseModel):
    crop: str = Field(min_length=1, max_length=80)
    stage: str = Field(default="growing", min_length=1, max_length=40)
    soil_moisture_pct: float = Field(ge=0, le=100)
    temperature_c: float = Field(ge=-20, le=65)
    humidity_pct: float = Field(ge=0, le=100)
    rain_probability_pct: float = Field(default=0, ge=0, le=100)
    forecast_rain_mm: float = Field(default=0, ge=0, le=500)


class Esp32CaptureRequest(BaseModel):
    host: str = Field(min_length=7, max_length=45, description="Private IPv4/IPv6 address of the ESP32-CAM; port 80 is used.")


class AdvisoryResponse(BaseModel):
    irrigation_action: str
    reason: str
    sustainability_score: int = Field(ge=0, le=100)
    trace: list[str]


class PredictionResponse(BaseModel):
    label: str
    confidence: float = Field(ge=0, le=1)
    model_mode: str
    model_notice: str
    precautions: list[str]
    quality_warnings: list[str]
    alternatives: list[dict[str, float | str]]
