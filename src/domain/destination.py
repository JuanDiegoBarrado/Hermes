from dataclasses import dataclass

from domain.location import Location


@dataclass(frozen=True)
class Destination:
    """Dónde se escriben los datos y en qué formato ("csv", "json", "yaml"...)."""

    location: Location
    format: str
