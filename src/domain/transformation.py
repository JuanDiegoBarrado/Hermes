from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Transformation:
    """Referencia a una transformación que aplica un job.

    `name` sigue la convención "<fichero>.<función>" (p. ej. "simpsons.select_columns") y
    `options` son los argumentos con los que se llama a esa función.
    """

    name: str
    options: Mapping[str, Any] = field(default_factory=dict)
