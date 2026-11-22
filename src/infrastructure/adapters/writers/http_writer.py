import urllib.request

from application.ports.writer import Writer


class HttpWriter(Writer):
    """Envía los bytes como cuerpo de una petición. Opciones: `url`, `method` (POST), `headers` (opcional)."""

    def __init__(self, url: str, method: str = "POST", headers: dict[str, str] | None = None) -> None:
        self._url = url
        self._method = method
        self._headers = headers or {}

    def write(self, content: bytes) -> None:
        request = urllib.request.Request(self._url, data=content, headers=self._headers, method=self._method)
        with urllib.request.urlopen(request):
            pass
