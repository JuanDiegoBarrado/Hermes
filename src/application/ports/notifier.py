from abc import ABC, abstractmethod
from datetime import datetime


class Notifier(ABC):
    """Avisa a alguien de que falló un job, por el canal que use cada implementación."""

    @abstractmethod
    def notify_failure(self, job: str, scheduled: datetime, error: str) -> None:
        """Avisa de que falló el job `job` en su disparo previsto para `scheduled`; `error` es
        el error tal cual (con su traceback)."""
