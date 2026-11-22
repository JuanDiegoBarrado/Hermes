from typing import Any

import pandas as pd

ACTIVITY_COLUMNS = [
    "date",
    "activity_id",
    "name",
    "type",
    "start_time_local",
    "duration_min",
    "moving_duration_min",
    "distance_km",
    "avg_speed_kmh",
    "avg_pace_min_km",
    "calories",
    "avg_hr",
    "max_hr",
    "elevation_gain_m",
    "elevation_loss_m",
    "steps",
    "avg_running_cadence_spm",
    "avg_power_w",
    "normalized_power_w",
    "aerobic_training_effect",
    "anaerobic_training_effect",
    "training_effect_label",
    "training_load",
    "vo2max",
    "body_battery_change",
    "moderate_intensity_min",
    "vigorous_intensity_min",
    "hr_zone_1_min",
    "hr_zone_2_min",
    "hr_zone_3_min",
    "hr_zone_4_min",
    "hr_zone_5_min",
    "lap_count",
    "location",
]
ACTIVITY_INT_COLUMNS = [
    "activity_id",
    "calories",
    "avg_hr",
    "max_hr",
    "steps",
    "avg_power_w",
    "normalized_power_w",
    "body_battery_change",
    "moderate_intensity_min",
    "vigorous_intensity_min",
    "lap_count",
]

DAILY_SUMMARY_COLUMNS = [
    "date",
    "steps",
    "active_kcal",
    "resting_kcal",
    "total_kcal",
    "sleep_hours",
    "sleep_score",
    "stress_avg",
    "weight_kg",
    "body_fat_pct",
    "training_readiness",
    "training_readiness_level",
    "hrv_last_night_ms",
    "hrv_weekly_avg_ms",
    "hrv_status",
    "floors_ascended",
]
DAILY_SUMMARY_INT_COLUMNS = [
    "steps",
    "active_kcal",
    "resting_kcal",
    "total_kcal",
    "sleep_score",
    "stress_avg",
    "training_readiness",
    "hrv_last_night_ms",
    "hrv_weekly_avg_ms",
    "floors_ascended",
]


def activities(data: pd.DataFrame, activity_types: list[str] | None = None) -> pd.DataFrame:
    """Actividades de Garmin (reader garmin, dataset activities): una fila por actividad,
    con el agregado de la sesión. `activity_types` son los typeKey que se quedan
    (running, cycling, strength_training...); por defecto, todos."""
    wanted = {t.lower() for t in activity_types or []}
    rows = [
        _activity_row(a)
        for a in _records(data)
        if not wanted or (a.get("activityType") or {}).get("typeKey") in wanted
    ]
    rows.sort(key=lambda r: r["start_time_local"] or "")
    return _frame(rows, ACTIVITY_COLUMNS, ACTIVITY_INT_COLUMNS)


def daily_summary(data: pd.DataFrame) -> pd.DataFrame:
    """Resumen diario de salud de Garmin (reader garmin, dataset daily_summary): una fila por día.

    Para el día D, el sueño, la VFC y el training readiness son los de la noche que termina la
    mañana de D (lo mismo que muestra la app de Garmin para ese día).
    """
    return _frame([_daily_row(d) for d in _records(data)], DAILY_SUMMARY_COLUMNS, DAILY_SUMMARY_INT_COLUMNS)


def _activity_row(a: dict[str, Any]) -> dict[str, Any]:
    start_local = a.get("startTimeLocal") or None
    distance = a.get("distance")
    speed = a.get("averageSpeed")
    row = {
        "date": start_local[:10] if start_local else None,
        "activity_id": _int(a.get("activityId")),
        "name": a.get("activityName"),
        "type": (a.get("activityType") or {}).get("typeKey"),
        "start_time_local": start_local,
        "duration_min": _scale(a.get("duration"), 1 / 60, 2),
        "moving_duration_min": _scale(a.get("movingDuration"), 1 / 60, 2),
        "distance_km": _scale(distance, 1 / 1000, 3) if distance else None,
        "avg_speed_kmh": _scale(speed, 3.6, 2) if distance else None,
        "avg_pace_min_km": _pace(speed) if distance else None,
        "calories": _int(a.get("calories")),
        "avg_hr": _int(a.get("averageHR")),
        "max_hr": _int(a.get("maxHR")),
        "elevation_gain_m": _scale(a.get("elevationGain"), 1, 1),
        "elevation_loss_m": _scale(a.get("elevationLoss"), 1, 1),
        "steps": _int(a.get("steps")),
        "avg_running_cadence_spm": _scale(a.get("averageRunningCadenceInStepsPerMinute"), 1, 1),
        "avg_power_w": _int(a.get("avgPower")),
        "normalized_power_w": _int(a.get("normPower")),
        "aerobic_training_effect": _scale(a.get("aerobicTrainingEffect"), 1, 1),
        "anaerobic_training_effect": _scale(a.get("anaerobicTrainingEffect"), 1, 1),
        "training_effect_label": a.get("trainingEffectLabel"),
        "training_load": _scale(a.get("activityTrainingLoad"), 1, 1),
        "vo2max": _scale(a.get("vO2MaxValue"), 1, 1),
        "body_battery_change": _int(a.get("differenceBodyBattery")),
        "moderate_intensity_min": _int(a.get("moderateIntensityMinutes")),
        "vigorous_intensity_min": _int(a.get("vigorousIntensityMinutes")),
        "lap_count": _int(a.get("lapCount")),
        "location": a.get("locationName"),
    }
    for zone in range(1, 6):
        row[f"hr_zone_{zone}_min"] = _scale(a.get(f"hrTimeInZone_{zone}"), 1 / 60, 1)
    return row


def _daily_row(d: dict[str, Any]) -> dict[str, Any]:
    summary = d.get("summary") or {}
    sleep = (d.get("sleep") or {}).get("dailySleepDTO") or {}
    hrv = (d.get("hrv") or {}).get("hrvSummary") or {}
    readiness = _morning_readiness(d.get("training_readiness"))
    weigh_in = _latest_weigh_in(d.get("weigh_ins"))
    sleep_seconds = sleep.get("sleepTimeSeconds") or summary.get("sleepingSeconds")
    return {
        "date": d.get("date"),
        "steps": _int(summary.get("totalSteps")),
        "active_kcal": _int(summary.get("activeKilocalories")),
        "resting_kcal": _int(summary.get("bmrKilocalories")),
        "total_kcal": _int(summary.get("totalKilocalories")),
        "sleep_hours": _scale(sleep_seconds, 1 / 3600, 2),
        "sleep_score": _int(((sleep.get("sleepScores") or {}).get("overall") or {}).get("value")),
        "stress_avg": _non_negative(_int(summary.get("averageStressLevel"))),  # -1/-2 = sin datos
        "weight_kg": _scale(weigh_in.get("weight"), 1 / 1000, 2),  # Garmin da gramos
        "body_fat_pct": _scale(weigh_in.get("bodyFat"), 1, 1),
        "training_readiness": _int(readiness.get("score")),
        "training_readiness_level": readiness.get("level"),
        "hrv_last_night_ms": _int(hrv.get("lastNightAvg")),
        "hrv_weekly_avg_ms": _int(hrv.get("weeklyAvg")),
        "hrv_status": hrv.get("status"),
        "floors_ascended": _int(summary.get("floorsAscended")),
    }


def _morning_readiness(data: Any) -> dict[str, Any]:
    """El valor del informe de la mañana; si no está marcado, el primero del día."""
    entries = [data] if isinstance(data, dict) else list(data or [])
    entries = [e for e in entries if isinstance(e, dict)]
    if not entries:
        return {}
    for entry in entries:
        if entry.get("inputContext") == "AFTER_WAKEUP_RESET":
            return entry
    return min(entries, key=lambda e: str(e.get("timestamp") or ""))


def _latest_weigh_in(data: Any) -> dict[str, Any]:
    weigh_ins = [w for w in (data or {}).get("dateWeightList") or [] if w.get("weight")]
    if not weigh_ins:
        return {}
    return max(weigh_ins, key=lambda w: w.get("timestampGMT") or w.get("date") or 0)


def _records(data: pd.DataFrame) -> list[dict[str, Any]]:
    """Las filas como diccionarios, con los huecos (NaN) que mete pandas como None."""
    return data.astype(object).where(data.notna(), None).to_dict(orient="records")


def _frame(rows: list[dict[str, Any]], columns: list[str], int_columns: list[str]) -> pd.DataFrame:
    """Columnas fijas (la cabecera sale aunque no haya filas) y enteros que admiten vacíos,
    para que un entero con algún hueco no se escriba como 2472.0."""
    return pd.DataFrame(rows, columns=columns).astype({c: "Int64" for c in int_columns})


def _scale(value: Any, factor: float, ndigits: int) -> float | None:
    return None if value is None else round(float(value) * factor, ndigits)


def _int(value: Any) -> int | None:
    return None if value is None else int(round(float(value)))


def _non_negative(value: int | None) -> int | None:
    return value if value is not None and value >= 0 else None


def _pace(speed_m_s: float | None) -> str | None:
    """m/s -> 'M:SS' por km."""
    if not speed_m_s:
        return None
    minutes, seconds = divmod(int(round(1000 / speed_m_s)), 60)
    return f"{minutes}:{seconds:02d}"
