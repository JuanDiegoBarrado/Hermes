from abc import abstractmethod
from datetime import datetime, timezone
from fnmatch import fnmatchcase
from pathlib import PurePosixPath

from application.ports.lister import Item, Lister
from domain.location import Location

DONE_FOLDER = "done"


class FilesystemLister(Lister):
    """Lister de un sistema de ficheros (local, S3...). La location lleva `path` o `pattern`,
    una de las dos:

    - `path`: ese fichero. Se lee siempre y no se mueve.
    - `pattern`: los ficheros de una carpeta cuyo nombre encaje con él (`*`, `?`, `[...]`), p. ej.
      `input/gimnasio/*.xlsx`, por orden de nombre. Los comodines solo valen en el nombre, no en
      la carpeta, y no se miran subcarpetas. La carpeta es la landing zone del job: cada fichero
      procesado se mueve a su subcarpeta `done/`, como `<nombre>_<YYYYMMDDHHMMSS><extensión>`
      (UTC), así que en cada ejecución solo quedan los pendientes.

    Cada Item es la location con `path` en lugar de `pattern` (el resto de opciones se
    conservan), y su nombre es el del fichero, con extensión. Las rutas usan `/`. Cada sistema
    implementa listar y mover; lo demás es común.
    """

    def __init__(self, location: Location) -> None:
        options = dict(location.options)
        pattern = options.pop("pattern", None)
        if ("path" in options) == (pattern is not None):
            raise ValueError(f"La location '{location.system}' necesita 'path' o 'pattern', uno de los dos")
        self._system = location.system
        self._options = options
        self._pattern = None if pattern is None else PurePosixPath(pattern)

    def items(self) -> list[Item]:
        if self._pattern is None:
            return [self._item(self._options["path"])]
        folder = self._pattern.parent
        names = sorted(name for name in self._list(str(folder)) if fnmatchcase(name, self._pattern.name))
        return [self._item(str(folder / name)) for name in names]

    def done(self, item: Item) -> None:
        if self._pattern is None:
            return
        path = item.location.options["path"]
        file = PurePosixPath(path)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        self._move(path, str(file.parent / DONE_FOLDER / f"{file.stem}_{timestamp}{file.suffix}"))

    def _item(self, path: str) -> Item:
        return Item(Location(self._system, {**self._options, "path": path}), PurePosixPath(path).name)

    @abstractmethod
    def _list(self, folder: str) -> list[str]:
        """Los nombres de los ficheros que hay directamente en `folder` (sin subcarpetas). Si no
        existe, ninguno."""

    @abstractmethod
    def _move(self, path: str, target: str) -> None:
        """Mueve el fichero `path` a `target`, creando su carpeta si hace falta."""
