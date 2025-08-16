# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / D.I.A. Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du script : train_model.py

Description :
Entraîne un modèle IA de classification (buy / hold / sell) à partir
d`un CSV de features + target, et exporte un fichier .pkl utilisable
dans la politique IA du bot DIA-Core V4.

Auteur : DYXIUM Invest / D.I.A. Core
"""

import argparse
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib


def main() -> None:
    parser = argparse.ArgumentParser(description="Training IA DIA-Core V4")
    parser.add_argument("--csv", required=True, help="Fichier CSV (features + target)")
    parser.add_argument("--output", default="models/model.pkl", help="Chemin de sortie du modèle")
    args = parser.parse_args()

    # Chargement des données
    df = pd.read_csv(args.csv)
    x = df.drop(columns=["target"])
    y = df["target"]

    # Split pour évaluer rapidement
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

    # Entraînement modèle
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(x_train, y_train)

    # Évaluation rapide
    y_prediction = model.predict(x_test)
    print("📊 Rapport de classification :\n")
    print(classification_report(y_test, y_prediction))

    # Export modèle
    joblib.dump(model, args.output)
    print(f"✅ Modèle entraîné et sauvegardé : {args.output}")


if __name__ == "__main__":
    main()
