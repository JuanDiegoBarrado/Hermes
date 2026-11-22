import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from application.ports.repositories.job_repository import JobRepository
from application.services.run_job_service import RunJobService
from domain.schedule import Schedule

logger = logging.getLogger(__name__)


@dataclass
class _Planned:
    schedule: Schedule
    next_run: datetime


class RunDueJobsService:
    """Caso de uso: una pasada del modo servidor. Ejecuta los jobs con schedule a los que les toca.

    Guarda en memoria el próximo disparo de cada job. Se calcula la primera vez que se ve el
    job (al arrancar, o cuando se añade o le cambia el schedule), así que los jobs se releen
    en cada pasada y los cambios en sus YAML se aplican sin reiniciar.

    Si cuando se revisa un job han pasado varios disparos (el equipo estuvo suspendido, o un
    job tardó más que su intervalo), se ejecuta solo el último y los anteriores se registran
    como perdidos. Si el que se ejecuta lleva más de `late_after` de retraso, también se avisa.
    Lo que ocurre con el servidor parado no se sabe ni se registra.
    """

    def __init__(self, jobs: JobRepository, run_job: RunJobService, late_after: timedelta) -> None:
        self._jobs = jobs
        self._run_job = run_job
        self._late_after = late_after
        self._planned: dict[str, _Planned] = {}

    def execute(self, now: datetime) -> datetime | None:
        """Ejecuta, uno tras otro, los jobs pendientes en `now` (con zona horaria). Devuelve el
        próximo disparo de todos los jobs, o None si no hay ninguno con schedule."""
        self._refresh(now)
        due = sorted((p.next_run, name) for name, p in self._planned.items() if p.next_run <= now)
        for _, name in due:
            self._run(name, now)
        return min((p.next_run for p in self._planned.values()), default=None)

    def _refresh(self, now: datetime) -> None:
        """Sincroniza la planificación con los jobs que hay ahora."""
        schedules = {job.name: job.schedule for job in self._jobs.find_all() if job.schedule is not None}
        for name in self._planned.keys() - schedules.keys():
            del self._planned[name]
            logger.info("'%s' ya no tiene schedule: deja de planificarse", name)
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
        else:
            logger.info("Job '%s' ejecutado. Próximo disparo: %s", name, planned.next_run)
