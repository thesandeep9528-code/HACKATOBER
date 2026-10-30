from __future__ import annotations

from fieldguard.schemas import SensorContext


GENERIC_PRECAUTIONS = [
    "Inspect nearby plants and isolate visibly affected material where practical.",
    "Remove fallen or heavily affected leaves using clean tools; do not compost diseased material.",
    "Avoid overhead watering and improve airflow around the crop.",
    "Confirm local, crop-specific treatment guidance before applying any pesticide.",
]


def precautions_for(label: str) -> list[str]:
    normalized = label.lower()
    advice = list(GENERIC_PRECAUTIONS)
    if "healthy" in normalized:
        return [
            "Continue regular scouting, especially after rain or humidity spikes.",
            "Water at soil level and keep tools clean between plots.",
        ]
    if "blight" in normalized:
        advice.insert(0, "Act early: remove symptomatic leaves and avoid handling plants while wet.")
    if "rust" in normalized or "mould" in normalized or "mold" in normalized:
        advice.insert(0, "Reduce leaf wetness and monitor lower leaves closely for spread.")
    if "bacterial" in normalized:
        advice.insert(0, "Disinfect tools between plants and avoid working the field when foliage is wet.")
    return advice


def irrigation_advice(context: SensorContext) -> tuple[str, str, list[str]]:
    trace = [
        f"soil_moisture_pct={context.soil_moisture_pct}",
        f"forecast_rain_mm={context.forecast_rain_mm}",
        f"rain_probability_pct={context.rain_probability_pct}",
    ]
    rain_likely = context.rain_probability_pct >= 60 and context.forecast_rain_mm >= 2
    if context.soil_moisture_pct < 25 and not rain_likely:
        return "IRRIGATE_NOW", "Soil moisture is low and meaningful rain is not forecast.", trace
    if context.soil_moisture_pct < 25 and rain_likely:
        return "CHECK_AGAIN_SOON", "Soil is dry, but likely rain may satisfy part of the need; re-check after the forecast window.", trace
    if rain_likely:
        return "DELAY_IRRIGATION", "Adequate soil moisture and likely measurable rain make irrigation unnecessary now.", trace
    return "MONITOR", "Current moisture does not require immediate irrigation.", trace


def sustainability_score(context: SensorContext, action: str) -> int:
    # Reproducible indicative score: 50 base, moisture stewardship ±, rain-aware decision +10,
    # heat stress -5. It is not a measured water-saving claim.
    score = 50
    score += 20 if 35 <= context.soil_moisture_pct <= 70 else -10
    if action == "DELAY_IRRIGATION" and context.rain_probability_pct >= 60:
        score += 10
    if context.temperature_c >= 35:
        score -= 5
    return max(0, min(100, score))
