import argparse
import logging
import signal
import sys
import threading
from datetime import datetime

from application.services.run_due_jobs_service import RunDueJobsService
from application.services.run_job_service import RunJobService

logger = logging.getLogger(__name__)


def main(argv: list[str], run_job: RunJobService, run_due_jobs: RunDueJobsService, wakeup_seconds: float) -> int:
    """Línea de comandos de Hermes. Devuelve el código de salida.

        hermes run <job>     ejecuta ese job una vez
        hermes serve         modo servidor: ejecuta los jobs según su schedule hasta Ctrl+C
    """
    parser = argparse.ArgumentParser(prog="hermes")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="Ejecuta un job una vez")
    run.add_argument("job", help="Nombre del job (el de su fichero en jobs/, sin .yaml)")
    commands.add_parser("serve", help="Ejecuta los jobs según su schedule hasta Ctrl+C")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if args.command == "serve":
        _serve(run_due_jobs, wakeup_seconds)
        return 0
    try:
        run_job.execute(args.job)
    except LookupError as exc:
        print(exc, file=sys.stderr)
        return 1
    logger.info("Job '%s' ejecutado", args.job)
    return 0


def _serve(run_due_jobs: RunDueJobsService, wakeup_seconds: float) -> None:
    """Bucle del modo servidor: ejecuta lo que toca y espera hasta el próximo disparo, o
    `wakeup_seconds` como mucho, para volver a mirar el reloj (por si el equipo se suspendió
    o cambió la hora) y los jobs (por si se añadió o cambió alguno).

    Ctrl+C / SIGTERM: termina el job en curso y sale. Un segundo Ctrl+C corta en seco.
    """
    stop = threading.Event()

    def request_stop(*_: object) -> None:
        if stop.is_set():
            raise KeyboardInterrupt
        logger.info("Parada solicitada: se sale al terminar lo que esté en curso (Ctrl+C otra vez para cortar ya)")
        stop.set()

    for name in ("SIGINT", "SIGTERM", "SIGBREAK"):  # SIGBREAK = Ctrl+Pausa en Windows
        if hasattr(signal, name):
            signal.signal(getattr(signal, name), request_stop)

    logger.info("Servidor iniciado: se despierta como mucho cada %g s", wakeup_seconds)
    while not stop.is_set():
        try:
            next_run = run_due_jobs.execute(_now())
        except Exception:  # p. ej. un YAML mal escrito: se avisa y se reintenta en la próxima pasada
            logger.exception("Error al revisar los jobs")
            next_run = None
        if next_run is None:
            wait = wakeup_seconds
        else:
            wait = min(max((next_run - _now()).total_seconds(), 0), wakeup_seconds)
        # En Linux la señal corta la espera al momento; en Windows no (ver README).
        stop.wait(wait)
    logger.info("Servidor detenido")


def _now() -> datetime:
    return datetime.now().astimezone()
