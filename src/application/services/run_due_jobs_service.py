import logging
import traceback
from dataclasses import dataclass
from datetime import datetime, timedelta

from application.ports.notifier import Notifier
from application.ports.repositories.job_repository import InvalidJobError, JobRepository
from application.services.run_job_service import RunJobService
from domain.schedule import Schedule

logger = logging.getLogger(__name__)


@dataclass
class _Planned:
    schedule: Schedule
    next_run: datetime


class RunDueJobsService:
    """Caso de uso: una pasada del modo servidor. Ejecuta los jobs con schedule a los que les toca.

    Sirve los jobs que se le piden por nombre o, si no se le pide ninguno, todos los que tienen
    `enabled`. Un job desactivado que no se puede leer (una variable de entorno que falta...) se
    ignora con un warning; uno activado (o pedido por su nombre) hace fallar la pasada.

    Guarda en memoria el próximo disparo de cada job. Se calcula la primera vez que se ve el
    job (al arrancar, o cuando se añade o le cambia el schedule), así que los jobs se releen
    en cada pasada y los cambios en sus YAML se aplican sin reiniciar.

    Si cuando se revisa un job han pasado varios disparos (el equipo estuvo suspendido, o un
    job tardó más que su intervalo), se ejecuta solo el último y los anteriores se registran
    como perdidos. Si el que se ejecuta lleva más de `late_after` de retraso, también se avisa.
    Lo que ocurre con el servidor parado no se sabe ni se registra.

    Si se le pasa un `notifier`, se le avisa de cada job que falla.
    """

    def __init__(
        self, jobs: JobRepository, run_job: RunJobService, late_after: timedelta, notifier: Notifier | None = None
    ) -> None:
        self._jobs = jobs
        self._run_job = run_job
        self._late_after = late_after
        self._notifier = notifier
        self._planned: dict[str, _Planned] = {}

    def execute(self, now: datetime, names: list[str] | None = None) -> datetime | None:
        """Ejecuta, uno tras otro, los jobs pendientes en `now` (con zona horaria): los de
        `names`, aunque no tengan `enabled`, o si es None los que lo tienen. Devuelve el próximo
        disparo de todos ellos, o None si no hay ninguno con schedule."""
        self._refresh(now, names)
        due = sorted((p.next_run, name) for name, p in self._planned.items() if p.next_run <= now)
        for _, name in due:
            self._run(name, now)
        return min((p.next_run for p in self._planned.values()), default=None)

    def _refresh(self, now: datetime, names: list[str] | None) -> None:
        """Sincroniza la planificación con los jobs que hay ahora."""
        schedules = {}
        for name in self._jobs.find_names() if names is None else names:
            try:
                job = self._jobs.find(name)
            except InvalidJobError as exc:
                if names is not None or exc.enabled:
                    raise
                logger.warning("Se ignora el job desactivado '%s', que no se puede leer: %s", name, exc)
                continue
            if job is None:
                logger.warning("No existe el job '%s'", name)
            elif job.schedule is not None and (names is not None or job.enabled):
                schedules[name] = job.schedule
        for name in self._planned.keys() - schedules.keys():
            del self._planned[name]
            logger.info("'%s' deja de planificarse (ya no tiene schedule o está desactivado)", name)
        for name, schedule in schedules.items():
            planned = self._planned.get(name)
            if planned is None or planned.schedule != schedule:
                self._planned[name] = _Planned(schedule, schedule.next_run(now))
                logger.info("'%s' planificado con '%s': próximo disparo %s", name, schedule.cron, self._planned[name].next_run)

    def _run(self, name: str, now: datetime) -> None:
        planned = self._planned[name]
        fires = []
        moment = planned.next_run
        while moment <= now:
            fires.append(moment)
            moment = planned.schedule.next_run(moment)
        planned.next_run = moment

        *missed, scheduled = fires
        if missed:
            logger.warning(
                "'%s': %d disparo(s) perdido(s), previstos entre %s y %s", name, len(missed), missed[0], missed[-1]
            )
        delay = now - scheduled
        if delay > self._late_after:
            logger.warning(
                "'%s' se ejecuta con %s de retraso (disparo previsto para %s)",
                name,
                timedelta(seconds=int(delay.total_seconds())),
                scheduled,
            )
        logger.info("Ejecutando '%s' (disparo previsto para %s)", name, scheduled)
        try:
            self._run_job.execute(name)
        except Exception:  # un job roto no para el servidor
            logger.exception("Falló el job '%s'", name)
            self._notify_failure(name, scheduled, traceback.format_exc())
        else:
            logger.info("Job '%s' ejecutado. Próximo disparo: %s", name, planned.next_run)

    def _notify_failure(self, name: str, scheduled: datetime, error: str) -> None:
        if self._notifier is None:
            return
        try:
            self._notifier.notify_failure(name, scheduled, error)
        except Exception:  # si el aviso falla, el servidor sigue
            logger.exception("No se pudo avisar del fallo del job '%s'", name)
