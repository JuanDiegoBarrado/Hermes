from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from croniter import croniter


@dataclass(frozen=True)
class Schedule:
    """Cuándo se ejecuta un job en modo servidor.

    `cron` es una expresión cron de 5 campos (minuto hora día-del-mes mes día-de-la-semana),
    p. ej. "0 6 * * *" = todos los días a las 06:00. `timezone` es la zona horaria IANA en la
    que se interpreta (p. ej. "Europe/Madrid"); si no se indica, la hora local del sistema.
    """

    cron: str
    timezone: str | None = None

    def __post_init__(self) -> None:
        if not croniter.is_valid(self.cron):
            raise ValueError(f"Expresión cron no válida: '{self.cron}'")
        if self.timezone is not None:
            ZoneInfo(self.timezone)  # lanza si la zona no existe

    def next_run(self, after: datetime) -> datetime:
        """El primer disparo estrictamente posterior a `after`, con su zona horaria."""
        if self.timezone is not None:
            return croniter(self.cron, after.astimezone(ZoneInfo(self.timezone))).get_next(datetime)
        # Hora local: se calcula en hora de reloj y se localiza después, para respetar el cambio de hora.
        local = after.astimezone().replace(tzinfo=None)
        return croniter(self.cron, local).get_next(datetime).astimezone()
