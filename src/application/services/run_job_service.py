import logging
import traceback
from collections.abc import Callable
from datetime import datetime, timezone
from functools import partial
from pathlib import PurePosixPath
from typing import Any

from application.factories.lister_factory import ListerFactory
from application.factories.parser_factory import ParserFactory
from application.factories.reader_factory import ReaderFactory
from application.factories.serializer_factory import SerializerFactory
from application.factories.writer_factory import WriterFactory
from application.ports.repositories.job_repository import JobRepository
from application.ports.repositories.transformation_repository import TransformationRepository
from domain.job import Job
from domain.location import Location
from domain.transformation import Transformation

logger = logging.getLogger(__name__)


class ItemsFailedError(Exception):
    """Fallaron algunos de los Items de un job que lee varios; los demás se procesaron."""


class RunJobService:
    """Caso de uso: ejecutar un job.

    Origen -> bytes -> [before] -> DataFrame -> [after] -> bytes -> destino.

    El Lister del sistema del origen dice qué se lee: ese recorrido se hace una vez por cada
    Item (en un sistema que no lista, uno: la propia location), y cada Item se marca como
    procesado en cuanto se escribe su salida. Si falla uno, los demás siguen y al final se lanza
    ItemsFailedError con el error de cada uno; si solo había uno, se lanza su propio error.

    En los textos de las opciones de la location del destino se sustituye, en cada escritura:
    - `{name}`: el nombre del Item sin extensión (el del fichero de origen). Solo si lo tiene.
    - `{timestamp}`: el momento de la escritura, como YYYYMMDDHHMMSS (UTC).
    """

    def __init__(
        self,
        jobs: JobRepository,
        transformations: TransformationRepository,
        listers: ListerFactory,
        readers: ReaderFactory,
        parsers: ParserFactory,
        serializers: SerializerFactory,
        writers: WriterFactory,
    ) -> None:
        self._jobs = jobs
        self._transformations = transformations
        self._listers = listers
        self._readers = readers
        self._parsers = parsers
        self._serializers = serializers
        self._writers = writers

    def execute(self, job_name: str) -> None:
        """Ejecuta el job con ese nombre. Lanza LookupError si no existe el job o alguna
        de sus transformaciones; esto último se comprueba antes de leer el origen."""
        job = self._jobs.find(job_name)
        if job is None:
            raise LookupError(f"No existe el job '{job_name}'")

        before = [self._resolve(t) for t in job.before]
        after = [self._resolve(t) for t in job.after]

        lister = self._listers.create(job.origin.location)
        items = lister.items()
        if not items:
            logger.info("Job '%s': no hay nada pendiente", job.name)
        failures = []
        for item in items:
            try:
                raw = self._readers.create(item.location).read()
                self._run(job, raw, before, after, item.name)
                lister.done(item)
            except Exception:
                if len(items) == 1:
                    raise
                logger.exception("Job '%s': falló '%s'", job.name, item.name)
                failures.append((item.name, traceback.format_exc()))
            else:
                if item.name is not None:
                    logger.info("Job '%s': '%s' procesado", job.name, item.name)
        if failures:
            names = ", ".join(f"'{name}'" for name, _ in failures)
            details = "\n".join(f"--- {name}\n{error}" for name, error in failures)
            raise ItemsFailedError(
                f"Job '{job.name}': fallaron {len(failures)} de {len(items)} ({names})\n\n{details}"
            )

    def _run(
        self,
        job: Job,
        raw: bytes,
        before: list[Callable[[Any], Any]],
        after: list[Callable[[Any], Any]],
        name: str | None,
    ) -> None:
        """Lo que va desde los bytes leídos hasta el destino. `name` es el del Item, si lo tiene."""
        for transform in before:
            raw = transform(raw)
        data = self._parsers.create(job.origin.format).parse(raw)

        for transform in after:
            data = transform(data)
        content = self._serializers.create(job.destination.format).serialize(data)
        self._writers.create(_destination(job.destination.location, name)).write(content)

    def _resolve(self, transformation: Transformation) -> Callable[[Any], Any]:
        """La función de la transformación con sus argumentos ya puestos."""
        function = self._transformations.find(transformation.name)
        if function is None:
            raise LookupError(f"No existe la transformación '{transformation.name}'")
        return partial(function, **transformation.options)


def _destination(location: Location, name: str | None) -> Location:
    """`location` con `{name}` y `{timestamp}` sustituidos en los textos de sus opciones."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

    def fill(value: Any) -> Any:
        if isinstance(value, str):
            if "{name}" in value:
                if name is None:
                    raise ValueError("'{name}' solo vale si lo que se lee tiene nombre (p. ej. un fichero)")
                value = value.replace("{name}", PurePosixPath(name).stem)
            return value.replace("{timestamp}", timestamp)
        if isinstance(value, dict):
            return {key: fill(item) for key, item in value.items()}
        if isinstance(value, list):
            return [fill(item) for item in value]
        return value

    return Location(system=location.system, options=fill(dict(location.options)))
