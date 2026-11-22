from application.ports.lister import Item, Lister
from domain.location import Location


class SingleLister(Lister):
    """El de los sistemas que no listan (http, garmin...): la propia location, una vez, sin nombre."""

    def __init__(self, location: Location) -> None:
        self._location = location

    def items(self) -> list[Item]:
        return [Item(self._location)]

    def done(self, item: Item) -> None:
        pass


class ListerFactory:
    """Crea el Lister que corresponde a `location.system`, construido con la location. Para un
    sistema sin Lister, SingleLister.

    El diccionario {system: clase Lister} se le pasa al arrancar la aplicación.
    """

    def __init__(self, listers: dict[str, type[Lister]]) -> None:
        self._listers = listers

    def create(self, location: Location) -> Lister:
        return self._listers.get(location.system, SingleLister)(location)
