import urllib.request

from application.ports.reader import Reader


class HttpReader(Reader):
    """Lee el cuerpo de la respuesta a un GET. Opciones: `url`, `headers` (opcional)."""

    def __init__(self, url: str, headers: dict[str, str] | None = None) -> None:
        self._url = url
        self._headers = headers or {}

    def read(self) -> bytes:
        request = urllib.request.Request(self._url, headers=self._headers, method="GET")
        with urllib.request.urlopen(request) as response:
            return response.read()
