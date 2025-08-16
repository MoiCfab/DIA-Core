# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / D.I.A. Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : alerts/daily_reporter.py

Description :
Génère un rapport HTML professionnel basé sur les trades journaliers.
Utile pour suivi personnel, reporting client ou audit.

Utilisé par :
    - Exécution post-marché
    - Cron quotidien

Auteur : DYXIUM Invest / D.I.A. Core
"""

import os
import json
from typing import Any

import pandas as pd
from datetime import datetime, UTC
from jinja2 import Environment, FileSystemLoader

from src.dia_core.alerts.email_sender import EmailConfig, send_html_email


def compute_stats(df: pd.DataFrame) -> dict[str, Any]:
    """Calcule des statistiques simples."""
    df["pl"] = df.apply(
        lambda row: row["size"] * row["price"] * (1 if row["action"] == "sell" else -1), axis=1
    )
    df["cum_pl"] = df["pl"].cumsum()

    return {
        "total_trades": len(df),
        "total_pnl": round(df["pl"].sum(), 2),
        "max_drawdown": round((df["cum_pl"].cummax() - df["cum_pl"]).max(), 2),
        "trades": df.to_dict(orient="records"),
    }


class DailyReporter:
    """Génère un rapport HTML à partir d`un journal de trades."""

    def __init__(
        self,
        log_path: str = "logs/trade_log.jsonl",
        template_dir: str = "templates",
        output_dir: str = "logs/reports",
    ) -> None:
        """
        Initialise le générateur.

        Args:
            log_path: str: Fichier JSONL avec les trades
            template_dir: str: Dossier avec les templates HTML Jinja2
            output_dir: str: Dossier où sauvegarder les rapports
        """
        self.log_path = log_path
        self.output_dir = output_dir
        self.env = Environment(
            loader=FileSystemLoader(template_dir), autoescape=True  # ← protection XSS activée
        )

        os.makedirs(output_dir, exist_ok=True)

    def load_trades(self) -> pd.DataFrame:
        """Charge-les trades et filtre ceux du jour."""
        if not os.path.exists(self.log_path):
            return pd.DataFrame()

        with open(self.log_path, encoding="utf-8") as f:
            data = [json.loads(line) for line in f if line.strip()]

        df = pd.DataFrame(data)
        if df.empty:
            return df

        df["timestamp"] = pd.to_datetime(df["timestamp"])
        today = pd.Timestamp.now().normalize()
        return df[df["timestamp"].dt.normalize() == today]

    def generate_report(self) -> str:
        """Génère le rapport HTML et retourne le chemin."""
        df = self.load_trades()
        stats = compute_stats(df)
        template = self.env.get_template("report_template.html")

        rendered = template.render(date=datetime.now(UTC).isoformat(), stats=stats)

        output_file = os.path.join(self.output_dir, f"report_{datetime.now(UTC).date()}.html")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(rendered)

        config = EmailConfig(
            from_email=os.environ.get("EMAIL_FROM", ""),
            smtp_server=os.environ.get("EMAIL_SMTP_SERVER", "smtp.gmail.com"),
            smtp_port=int(os.environ.get("EMAIL_SMTP_PORT", "587")),
            username=os.environ.get("EMAIL_USER", ""),
            password=os.environ.get("EMAIL_PASS", ""),
        )
        success = send_html_email(
            subject=f"[DIA-Core] Rapport du {datetime.now(UTC).date()}",
            html_file_path=output_file,
            to_email=os.environ.get("EMAIL_TO", ""),
            config=config,
        )
        if success:
            print("📧 Rapport envoyé avec succès.")
        else:
            print("❌ Échec de l`envoi email.")

        return output_file
