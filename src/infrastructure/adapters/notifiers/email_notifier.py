import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage

from application.ports.notifier import Notifier


class EmailNotifier(Notifier):
    """Avisa por correo a `to` a través de un servidor SMTP, como `user`, que es también el
    remitente. El puerto 465 usa TLS implícito; cualquier otro, STARTTLS (lo habitual es el 587).
    """

    def __init__(self, host: str, port: int, user: str, password: str, to: str) -> None:
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._to = to

    def notify_failure(self, job: str, scheduled: datetime, error: str) -> None:
        message = EmailMessage()
        message["From"] = self._user
        message["To"] = self._to
        message["Subject"] = f"Hermes: falló el job {job}"
        message.set_content(f"Falló el job {job} (disparo previsto para {scheduled}).\n\nError:\n{error}")
        self._send(message)

    def _send(self, message: EmailMessage) -> None:
        context = ssl.create_default_context()
        if self._port == 465:
            with smtplib.SMTP_SSL(self._host, self._port, context=context, timeout=30) as smtp:
                smtp.login(self._user, self._password)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(self._host, self._port, timeout=30) as smtp:
                smtp.starttls(context=context)
                smtp.login(self._user, self._password)
                smtp.send_message(message)
