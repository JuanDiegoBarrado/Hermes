from pathlib import Path

from application.ports.writer import Writer


class FilesystemWriter(Writer):
    """Escribe un fichero en el sistema de ficheros (crea las carpetas que falten). Opciones: `path`."""

    def __init__(self, path: str) -> None:
        self._path = Path(path)

    def write(self, content: bytes) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_bytes(content)
