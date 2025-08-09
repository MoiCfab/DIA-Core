from __future__ import annotations

import logging
import smtplib
import ssl
from collections.abc import Iterable
from dataclasses import dataclass
from email.message import EmailMessage


@dataclass
class EmailConfig:
    smtp_host: str
    smtp_port: int = 587
    username: str | None = None
    password: str | None = None
    use_tls: bool = True
    sender: str = "dia-core@localhost"
    recipients: Iterable[str] = ()
    timeout: float = 10.0


class EmailAlerter:
    """Alerte email simple, synchrone, sans dépendance externe.

    Usage:
        alerter = EmailAlerter(EmailConfig(...))
        alerter.send(
            subject="[DIA-Core] Surcharge CPU",
            body="CPU 95% sur 2 min, 3 paires désactivées",
        )
    """

    def __init__(self, cfg: EmailConfig) -> None:
        self.cfg = cfg

    def _build(self, subject: str, body: str) -> EmailMessage:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.cfg.sender
        msg["To"] = ", ".join(self.cfg.recipients)
        msg.set_content(body)
        return msg

    def send(self, subject: str, body: str) -> None:
        if not self.cfg.recipients:
            return
        msg = self._build(subject, body)
        context = ssl.create_default_context()

        if self.cfg.use_tls:  # 587 STARTTLS (Gmail)
            with smtplib.SMTP(
                self.cfg.smtp_host, self.cfg.smtp_port, timeout=self.cfg.timeout
            ) as s:
                s.ehlo()
                s.starttls(context=context)
                s.ehlo()
                if self.cfg.username and self.cfg.password:
                    s.login(self.cfg.username, self.cfg.password)
                s.send_message(msg)
        else:
            # SSL direct (ex: Gmail 465)
            with smtplib.SMTP_SSL(
                self.cfg.smtp_host, self.cfg.smtp_port, context=context, timeout=self.cfg.timeout
            ) as s:
                if self.cfg.username and self.cfg.password:
                    s.login(self.cfg.username, self.cfg.password)
                s.send_message(msg)

    def try_send(self, subject: str, body: str) -> bool:
        """Envoie et retourne True si succès, False si échec (loggue l'erreur)."""
        try:
            self.send(subject, body)
            return True
        except (smtplib.SMTPException, ssl.SSLError, OSError) as e:
            logging.getLogger(__name__).warning("Email non envoyé: %s", e)
            return False

    def send_test(self) -> bool:
        return self.try_send(
            "[DIA-Core] Test d'alerte email",
            "Ceci est un email de test envoyé par DIA-Core pour vérifier la configuration SMTP.",
        )
