# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / D.I.A. Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du script : runner_report.py

Description :
Génère un rapport quotidien au format HTML depuis les trades du jour,
et l`envoie par email si activé dans les variables d`environnement.

Utilisé pour : reporting journalier (manuel ou cron)

Auteur : DYXIUM Invest / D.I.A. Core
"""

from src.dia_core.alerts.daily_reporter import DailyReporter


def main() -> None:
    """Génère le rapport journalier (et l`envoie si activé)."""
    print("📊 Génération du rapport DIA-Core...")
    reporter = DailyReporter()
    html_path = reporter.generate_report()
    print(f"✅ Rapport HTML généré : {html_path}")


if __name__ == "__main__":
    main()
