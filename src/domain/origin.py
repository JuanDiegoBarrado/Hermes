from dataclasses import dataclass

from domain.location import Location


@dataclass(frozen=True)
class Origin:
    """De dónde se leen los datos y en qué formato vienen ("csv", "json", "yaml"...)."""

    location: Location
    format: str
