import base64
import urllib.request

from application.ports.writer import Writer


class HttpWriter(Writer):
    """Envía los bytes como cuerpo de una petición. Opciones: `url`, `method` (POST), `headers` (opcional)
    y `basic_auth` (opcional): "<usuario>:<contraseña>", que se envía como cabecera Authorization: Basic."""

    def __init__(
        self, url: str, method: str = "POST", headers: dict[str, str] | None = None, basic_auth: str | None = None
    ) -> None:
        self._url = url
        self._method = method
        self._headers = dict(headers or {})
        if basic_auth is not None:
            if ":" not in basic_auth:
                raise ValueError("basic_auth debe ser '<usuario>:<contraseña>'")
            self._headers["Authorization"] = "Basic " + base64.b64encode(basic_auth.encode("utf-8")).decode("ascii")

    def write(self, content: bytes) -> None:
        request = urllib.request.Request(self._url, data=content, headers=self._headers, method=self._method)
        with urllib.request.urlopen(request):
            pass
