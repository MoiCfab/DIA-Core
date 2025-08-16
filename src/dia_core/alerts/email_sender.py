# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / D.I.A. Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : alerts/email_sender.py

Description :
Permet d`envoyer un fichier HTML par mail via SMTP sécurisé.

Utilisé par :
    - daily_reporter.py

Auteur : DYXIUM Invest / D.I.A. Core
"""

import smtplib
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging

logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    from_email: str
    smtp_server: str
    smtp_port: int
    username: str
    password: str


def send_html_email(
    subject: str,
    html_file_path: str,
    to_email: str,
    config: EmailConfig,
) -> bool:
    """
    Envoie un fichier HTML en tant qu`email via SMTP.

    Args:
        subject: Sujet du mail
        html_file_path: Chemin vers le fichier HTML
        to_email: Destinataire
        config: EmailConfig

    Returns:
        bool: True si succès, False sinon
    """
    try:
        with open(html_file_path, encoding="utf-8") as f:
            html_content = f.read()

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = config.from_email or config.username
        msg["To"] = to_email
        part = MIMEText(html_content, "html")
        msg.attach(part)

        with smtplib.SMTP(config.smtp_server, config.smtp_port) as server:
            server.starttls()
            server.login(config.username, config.password)
            server.sendmail(msg["From"], [msg["To"]], msg.as_string())

        return True

    except (smtplib.SMTPException, OSError) as e:
        logger.error(f"[EmailSender] Erreur d`envoi : {e}")
        return False
