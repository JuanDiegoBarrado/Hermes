"""Punto de arranque de Hermes: monta las piezas concretas y lanza la línea de comandos.

    python src/main.py run <job>
    python src/main.py serve [job ...]

Los jobs se leen de jobs/ y las transformaciones de transforms/ (en la raíz de Hermes);
las rutas relativas de los jobs (p. ej. output/...) son relativas a la carpeta desde la
que se ejecuta.

Configuración en el .env de la raíz de Hermes (una variable de entorno ya definida manda):
    HERMES_WAKEUP_SECONDS   en modo servidor, cada cuánto se despierta como mucho (por defecto: 900)

    Correo de aviso cuando falla un job en modo servidor. Si falta alguna (salvo SMTP_PORT),
    no se envía ningún correo:
    ALERT_EMAIL             a quién se avisa
    SMTP_HOST               servidor SMTP por el que se envía, como SMTP_USER, que es también el remitente
    SMTP_PORT               465 usa TLS, cualquier otro STARTTLS (por defecto: 587)
    SMTP_USER
    SMTP_PASSWORD           en Gmail: smtp.gmail.com, 587 y una contraseña de aplicación (no la de la cuenta)

    Las que usen los jobs con ${NOMBRE} (ver YamlJobRepository). Para entregar a Omnis:
    OMNIS_STORAGE_DATA_DIR  la URL del storage de Omnis, sin / al final (p. ej. http://localhost:9000)
    OMNIS_STORAGE_AUTH      base64 de "<usuario>:<contraseña>", con un usuario de STORAGE_USERS
    OMNIS_STORAGE_TEMP_DIR  la carpeta temp/ del storage de Omnis, sin / al final, de donde se leen
                            los Excels subidos (p. ej. ../Omnis/omnis-storage/data/temp)
"""

import logging
import os
import sys
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

from application.factories.lister_factory import ListerFactory
from application.factories.parser_factory import ParserFactory
from application.factories.reader_factory import ReaderFactory
from application.factories.serializer_factory import SerializerFactory
from application.factories.writer_factory import WriterFactory
from application.services.run_due_jobs_service import RunDueJobsService
from application.services.run_job_service import RunJobService
from infrastructure.adapters.listers.local_filesystem_lister import LocalFilesystemLister
from infrastructure.adapters.parsers.csv_parser import CsvParser
from infrastructure.adapters.parsers.json_parser import JsonParser
from infrastructure.adapters.parsers.xlsx_parser import XlsxParser
from infrastructure.adapters.parsers.yaml_parser import YamlParser
from infrastructure.adapters.notifiers.email_notifier import EmailNotifier
from infrastructure.adapters.readers.filesystem_reader import FilesystemReader
from infrastructure.adapters.readers.garmin_reader import GarminReader
from infrastructure.adapters.readers.http_reader import HttpReader
from infrastructure.adapters.readers.s3_reader import S3Reader
from infrastructure.adapters.repositories.job_repositories.yaml_job_repository import YamlJobRepository
from infrastructure.adapters.repositories.transformation_repositories.python_transformation_repository import (
    PythonTransformationRepository,
)
from infrastructure.adapters.serializers.csv_serializer import CsvSerializer
from infrastructure.adapters.serializers.json_serializer import JsonSerializer
from infrastructure.adapters.serializers.yaml_serializer import YamlSerializer
from infrastructure.adapters.writers.filesystem_writer import FilesystemWriter
from infrastructure.adapters.writers.http_writer import HttpWriter
from infrastructure.adapters.writers.s3_writer import S3Writer
from infrastructure.cli.app import main

ROOT = Path(__file__).resolve().parents[1]

# Lo que necesita el correo de aviso. SMTP_PORT es opcional (587 por defecto)
EMAIL_VARIABLES = ("ALERT_EMAIL", "SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD")


def wakeup_seconds() -> float:
    value = os.getenv("HERMES_WAKEUP_SECONDS", "900")
    try:
        seconds = float(value)
    except ValueError:
        seconds = 0
    if seconds <= 0:
        raise ValueError(f"HERMES_WAKEUP_SECONDS debe ser un número de segundos mayor que 0, no '{value}'")
    return seconds


def build_notifier() -> EmailNotifier | None:
    """El que avisa por correo, o None si no están todas las EMAIL_VARIABLES."""
    missing = [name for name in EMAIL_VARIABLES if not os.getenv(name)]
    if missing:
        if len(missing) < len(EMAIL_VARIABLES):
            logging.getLogger(__name__).warning("Correos de aviso desactivados: faltan %s", missing)
        return None
    return EmailNotifier(
        host=os.environ["SMTP_HOST"],
        port=int(os.getenv("SMTP_PORT") or 587),
        user=os.environ["SMTP_USER"],
        password=os.environ["SMTP_PASSWORD"],
        to=os.environ["ALERT_EMAIL"],
    )


def build_run_job_service(jobs: YamlJobRepository) -> RunJobService:
    return RunJobService(
        jobs=jobs,
        transformations=PythonTransformationRepository(ROOT / "transforms"),
        listers=ListerFactory({"filesystem": LocalFilesystemLister}),
        readers=ReaderFactory(
            {"filesystem": FilesystemReader, "http": HttpReader, "s3": S3Reader, "garmin": GarminReader}
        ),
        parsers=ParserFactory({"csv": CsvParser, "json": JsonParser, "yaml": YamlParser, "xlsx": XlsxParser}),
        serializers=SerializerFactory({"csv": CsvSerializer, "json": JsonSerializer, "yaml": YamlSerializer}),
        writers=WriterFactory({"filesystem": FilesystemWriter, "http": HttpWriter, "s3": S3Writer}),
    )


if __name__ == "__main__":
    load_dotenv(ROOT / ".env")
    wakeup = wakeup_seconds()
    jobs = YamlJobRepository(ROOT / "jobs")
    run_job = build_run_job_service(jobs)
    # Retraso a partir del cual se avisa: el bucle despierta a la hora de cada disparo, así que
    # pasarse de su tope de espera solo ocurre si el equipo estuvo suspendido o muy ocupado.
    run_due_jobs = RunDueJobsService(jobs, run_job, late_after=timedelta(seconds=wakeup), notifier=build_notifier())
    sys.exit(main(sys.argv[1:], run_job, run_due_jobs, wakeup))
