from pathlib import Path

from application.ports.filesystem_lister import FilesystemLister


class LocalFilesystemLister(FilesystemLister):
    """FilesystemLister del sistema de ficheros local. Las rutas relativas lo son a la carpeta
    desde la que se ejecuta Hermes."""

    def _list(self, folder: str) -> list[str]:
        directory = Path(folder)
        if not directory.is_dir():
            return []
        return [entry.name for entry in directory.iterdir() if entry.is_file()]

    def _move(self, path: str, target: str) -> None:
        destination = Path(target)
        destination.parent.mkdir(parents=True, exist_ok=True)
        Path(path).replace(destination)
