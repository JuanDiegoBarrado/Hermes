import datetime as dt
import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from garminconnect import Garmin, GarminConnectAuthenticationError, GarminConnectTooManyRequestsError

from application.ports.reader import Reader

logger = logging.getLogger(__name__)


class GarminReader(Reader):
    """Lee datos de Garmin Connect y los devuelve como JSON: una lista de objetos.

    Opciones:
      dataset     activities | daily_summary
      date        today | yesterday | AAAA-MM-DD, último día que se lee (por defecto: yesterday)
      days        nº de días que terminan en `date`, incluido (por defecto: 1)
      tokenstore  carpeta con los tokens de la sesión de Garmin (por defecto: ~/.garminconnect)

    - activities: las actividades de esos días, tal como las da Garmin.
    - daily_summary: un objeto por día con la respuesta de cada endpoint:
      {"date", "summary", "sleep", "hrv", "training_readiness", "weigh_ins"}.
    """

    def __init__(
        self, dataset: str, date: str = "yesterday", days: int = 1, tokenstore: str = "~/.garminconnect"
    ) -> None:
        if dataset not in ("activities", "daily_summary"):
            raise ValueError(f"Garmin: dataset debe ser activities o daily_summary, no '{dataset}'")
        self._dataset = dataset
        self._date = date
        self._days = days
        self._tokenstore = tokenstore

    def read(self) -> bytes:
        end = _resolve_date(self._date)
        start = end - dt.timedelta(days=self._days - 1)
        api = Garmin()
        api.login(str(Path(self._tokenstore).expanduser()))
        if self._dataset == "activities":
            records = api.get_activities_by_date(start.isoformat(), end.isoformat()) or []
        else:
            records = [_daily_summary(api, start + dt.timedelta(days=i)) for i in range(self._days)]
        return json.dumps(records, ensure_ascii=False).encode("utf-8")


def _daily_summary(api: Garmin, day: dt.date) -> dict[str, Any]:
    d = day.isoformat()
    return {
        "date": d,
        "summary": api.get_user_summary(d),  # obligatorio: si falla, falla el job
        "sleep": _optional(api.get_sleep_data, d),
        "hrv": _optional(api.get_hrv_data, d),
        "training_readiness": _optional(api.get_training_readiness, d),
        "weigh_ins": _optional(api.get_daily_weigh_ins, d),
    }


def _optional(method: Callable[[str], Any], day: str) -> Any:
    """Métricas que no todos los días/dispositivos tienen: si fallan, quedan a None."""
    try:
        return method(day)
    except (GarminConnectAuthenticationError, GarminConnectTooManyRequestsError):
        raise
    except Exception as exc:
        logger.warning("Garmin: sin %s para %s (%s)", method.__name__, day, exc)
        return None


def _resolve_date(spec: str) -> dt.date:
    value = str(spec).strip().lower()
    if value == "today":
        return dt.date.today()
    if value == "yesterday":
        return dt.date.today() - dt.timedelta(days=1)
    return dt.date.fromisoformat(value)
