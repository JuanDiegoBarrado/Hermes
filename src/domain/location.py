from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Location:
    """Dónde están (o dónde se escriben) los datos.

    `system` es el tipo de sistema ("filesystem", "http", "s3"...) y `options` lo que ese
    sistema necesita para localizarlos (una ruta, una URL, un bucket y una clave...).
    """

    system: str
    options: Mapping[str, Any] = field(default_factory=dict)
