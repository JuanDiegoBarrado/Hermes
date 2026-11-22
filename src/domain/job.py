from dataclasses import dataclass

from domain.destination import Destination
from domain.origin import Origin
from domain.schedule import Schedule
from domain.transformation import Transformation


@dataclass(frozen=True)
class Job:
    """Una extracción: leer de un origen y escribir en un destino.

    `before` se aplica, en orden, a los bytes leídos (antes del parser) y `after` al
    DataFrame (antes del serializer). `schedule` es cuándo se ejecuta en modo servidor;
    sin él, el job solo se ejecuta cuando se pide. Un job con `enabled` a False no se sirve
    en modo servidor (salvo que se pida por su nombre), pero se puede ejecutar a mano.
    """

    name: str
    origin: Origin
    destination: Destination
    before: tuple[Transformation, ...] = ()
    after: tuple[Transformation, ...] = ()
    schedule: Schedule | None = None
    enabled: bool = True
