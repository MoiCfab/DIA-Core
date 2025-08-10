# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

from __future__ import annotations

import os
from contextlib import suppress

from dia_core.alerts.email_alerts import EmailAlerter, EmailConfig
from dia_core.alerts.formatters import SymbolSummary, render_markdown, render_subject, render_text
from dia_core.alerts.telegram_alerts import load_config_from_env as load_tg
from dia_core.alerts.telegram_alerts import send as tg_send


def _email_cfg_from_env() -> EmailConfig | None:
    host = os.getenv("SMTP_HOST")
    if not host:
        return None
    to = [e.strip() for e in os.getenv("EMAIL_TO", "").split(",") if e.strip()]
    if not to:
        return None
    return EmailConfig(
        smtp_host=host,
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        username=os.getenv("SMTP_USERNAME"),
        password=os.getenv("SMTP_PASSWORD"),
        use_tls=os.getenv("SMTP_USE_TLS", "1") != "0",
        sender=os.getenv("EMAIL_SENDER", "dia-core@localhost"),
        recipients=to,
    )


def notify_summary(mode: str, items: list[SymbolSummary]) -> None:
    if not items:
        return
    # Telegram
    tg = load_tg()
    if tg:
        with suppress(Exception):  # pragma: no cover
            tg_send(tg, render_markdown(mode, items))

    # Email (texte)
    ec = _email_cfg_from_env()
    if ec:
        with suppress(Exception):  # pragma: no cover
            subj = render_subject(mode, items)
            body = render_text(mode, items)
            EmailAlerter(ec).try_send(subj, body)
