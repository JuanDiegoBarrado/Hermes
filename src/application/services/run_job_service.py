from collections.abc import Callable
from functools import partial
from typing import Any

from application.factories.parser_factory import ParserFactory
from application.factories.reader_factory import ReaderFactory
from application.factories.serializer_factory import SerializerFactory
from application.factories.writer_factory import WriterFactory
from application.ports.repositories.job_repository import JobRepository
from application.ports.repositories.transformation_repository import TransformationRepository
from domain.transformation import Transformation


class RunJobService:
    """Caso de uso: ejecutar un job.

    Origen -> bytes -> [before] -> DataFrame -> [after] -> bytes -> destino.
    """

    def __init__(
        self,
        jobs: JobRepository,
        transformations: TransformationRepository,
        readers: ReaderFactory,
        parsers: ParserFactory,
        serializers: SerializerFactory,
        writers: WriterFactory,
    ) -> None:
        self._jobs = jobs
        self._transformations = transformations
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

        raw = self._readers.create(job.origin.location).read()
        for transform in before:
            raw = transform(raw)
        data = self._parsers.create(job.origin.format).parse(raw)

        for transform in after:
            data = transform(data)
        content = self._serializers.create(job.destination.format).serialize(data)
        self._writers.create(job.destination.location).write(content)

    def _resolve(self, transformation: Transformation) -> Callable[[Any], Any]:
        """La función de la transformación con sus argumentos ya puestos."""
        function = self._transformations.find(transformation.name)
        if function is None:
            raise LookupError(f"No existe la transformación '{transformation.name}'")
        return partial(function, **transformation.options)
