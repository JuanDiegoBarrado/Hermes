from pathlib import Path

from application.ports.reader import Reader


class FilesystemReader(Reader):
    """Lee un fichero del sistema de ficheros. Opciones: `path`."""

    def __init__(self, path: str) -> None:
        self._path = Path(path)

    def read(self) -> bytes:
        return self._path.read_bytes()
