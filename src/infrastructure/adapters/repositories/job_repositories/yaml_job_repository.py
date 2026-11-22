import os
import re
from pathlib import Path
from typing import Any

import yaml

from application.ports.repositories.job_repository import JobRepository
from domain.destination import Destination
from domain.job import Job
from domain.location import Location
from domain.origin import Origin
from domain.schedule import Schedule
from domain.transformation import Transformation

_VARIABLE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


class YamlJobRepository(JobRepository):
    """Jobs guardados como ficheros YAML: uno por job, `<directory>/<nombre>.yaml`.

    El nombre del job es el nombre del fichero. Formato:

        origin:
          location:
            system: http         # el resto de claves de location son sus opciones
            url: https://...
          format: json
        transforms:              # opcional; before y after también lo son
          before:                # sobre los bytes leídos, antes del parser
            - name: simpsons.extract_results
          after:                 # sobre el DataFrame, antes del serializer
            - name: simpsons.select_columns
              options:           # argumentos de la función (opcional)
                columns: [name, age]
        destination:
          location:
            system: filesystem
            path: output/ventas.csv  # admite {name} y {timestamp} (ver RunJobService)
          format: csv
        schedule:                # opcional; cuándo se ejecuta en modo servidor
          cron: "0 6 * * *"
          timezone: Europe/Madrid  # opcional; por defecto, la hora local

    En cualquier texto del YAML, `${NOMBRE}` se sustituye al leer el job por esa variable de
    entorno (p. ej. del .env), para que las credenciales no estén en el fichero del job. Si la
    variable no está definida, el job no es válido. Como la sustitución se hace al leer, `save`
    escribe los valores ya sustituidos: guardar un job leído dejaría sus secretos en el YAML.
    """

    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def find(self, name: str) -> Job | None:
        path = self._path(name)
        if not path.is_file():
            return None
        return self._read(path)

    def find_all(self) -> list[Job]:
        if not self._directory.is_dir():
            return []
        return [self._read(path) for path in sorted(self._directory.glob("*.yaml"))]

    def save(self, job: Job) -> None:
        self._directory.mkdir(parents=True, exist_ok=True)
        data: dict[str, Any] = {"origin": _endpoint_to_dict(job.origin)}
        transforms = _transforms_to_dict(job)
        if transforms:
            data["transforms"] = transforms
        data["destination"] = _endpoint_to_dict(job.destination)
        if job.schedule is not None:
            data["schedule"] = _schedule_to_dict(job.schedule)
        text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
        self._path(job.name).write_text(text, encoding="utf-8")

    def delete(self, name: str) -> None:
        self._path(name).unlink(missing_ok=True)

    def _path(self, name: str) -> Path:
        return self._directory / f"{name}.yaml"

    def _read(self, path: Path) -> Job:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        try:
            data = _expand_variables(data)
            transforms = data.get("transforms") or {}
            return Job(
                name=path.stem,
                origin=Origin(*_endpoint_from_dict(data["origin"])),
                destination=Destination(*_endpoint_from_dict(data["destination"])),
                before=_transformations_from_list(transforms.get("before") or []),
                after=_transformations_from_list(transforms.get("after") or []),
                schedule=_schedule_from_dict(data.get("schedule")),
            )
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Job no válido en {path}: {exc!r}") from exc


def _expand_variables(value: Any) -> Any:
    """`value` con cada `${NOMBRE}` de sus textos sustituido por esa variable de entorno."""
    if isinstance(value, str):
        return _VARIABLE.sub(_variable_value, value)
    if isinstance(value, dict):
        return {key: _expand_variables(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_expand_variables(item) for item in value]
    return value


def _variable_value(match: re.Match[str]) -> str:
    name = match.group(1)
    value = os.environ.get(name)
    if value is None:
        raise ValueError(f"La variable de entorno '{name}' no está definida")
    return value


def _endpoint_from_dict(data: dict[str, Any]) -> tuple[Location, str]:
    options = dict(data["location"])
    system = str(options.pop("system"))
    return Location(system=system, options=options), str(data["format"])


def _endpoint_to_dict(endpoint: Origin | Destination) -> dict[str, Any]:
    location = {"system": endpoint.location.system, **endpoint.location.options}
    return {"location": location, "format": endpoint.format}


def _transformations_from_list(data: list[dict[str, Any]]) -> tuple[Transformation, ...]:
    return tuple(
        Transformation(name=str(item["name"]), options=dict(item.get("options") or {})) for item in data
    )


def _schedule_from_dict(data: dict[str, Any] | None) -> Schedule | None:
    if data is None:
        return None
    timezone = data.get("timezone")
    return Schedule(cron=str(data["cron"]), timezone=None if timezone is None else str(timezone))


def _schedule_to_dict(schedule: Schedule) -> dict[str, Any]:
    if schedule.timezone is None:
        return {"cron": schedule.cron}
    return {"cron": schedule.cron, "timezone": schedule.timezone}


def _transforms_to_dict(job: Job) -> dict[str, Any]:
    transforms = {}
    for stage, transformations in (("before", job.before), ("after", job.after)):
        if transformations:
            transforms[stage] = [
                {"name": t.name, **({"options": dict(t.options)} if t.options else {})}
                for t in transformations
            ]
    return transforms
