## 🔒 Licence

Ce projet est sous licence propriétaire fermée.  
Toute utilisation ou distribution non autorisée est strictement interdite.

© 2025 Fabien Grolier — DYXIUM Invest / DIA-Core. Tous droits réservés.

# DIA-Core — Guide complet d’installation et d’exploitation 

## 1. Présentation

**DIA-Core** est un bot de trading algorithmique pour **day trading multi-actifs**.
Il intègre :
- Une stratégie adaptative de type “métamorphe” (proportionnelle au marché)
- Un moteur de gestion du risque avancé
- Une supervision en temps réel des ressources (OverloadGuard)
- Des alertes e-mail en cas de surcharge ou d’événement critique

**Modes d’exécution** :
- 'dry_run' — Simulation hors réseau
- 'paper' — Simulation en conditions réelles, sans fonds
- 'live' — Trading réel avec capital

**Important** :  
En cas de surcharge, **DIA-Core ne downgradera pas le modèle IA**.  
Il réduira temporairement le nombre de paires actives et enverra une alerte e-mail.

---

## 2. Prérequis

### Matériel minimal recommandé
- CPU 4 cœurs @ 2 GHz
- 8 Go RAM
- 20 Go SSD libre
- Connexion Internet stable

### Matériel optimal pour IA lourde
- CPU 8+ cœurs
- 32 Go RAM
- GPU NVIDIA RTX (CUDA) ou AMD ROCm
- SSD NVMe

### Logiciels
- Linux avec 'systemd'
- Python ≥ 3.11
- 'git', 'bash', 'systemctl'
- Accès sudo

---

## 3. Structure des répertoires

| Chemin | Rôle |
|--------|------|
| '/opt/dia-core' | Code source et venv |
| '/opt/dia-core/.venv' | Environnement Python |
| '/opt/dia-core/Config/config.json' | Configuration principale |
| '/opt/dia-core/.env' | Clés API et secrets |
| '/var/log/dia-core' | Logs JSON |
| '/etc/systemd/system/dia-core.service' | Service systemd |

---

## 4. Installation

Depuis la racine du projet :

'''bash
chmod +x scripts/installe_system.sh
sudo ./scripts/installe_system.sh
'''

Le script :
1. Crée l’utilisateur 'dia'
2. Déploie le code dans '/opt/dia-core'
3. Installe le venv et les dépendances
4. Configure les répertoires Config et Logs
5. Crée le service systemd et le démarre

---

## 5. Configuration

### Fichier 'Config/config.json'
Contient :
- Mode ('dry_run', 'paper', 'live')
- Paramètres exchange (paire, décimales, min_qty…)
- Paramètres de risque (max drawdown, risk per trade…)
- Répertoires de logs et cache

### Fichier '.env'
Stocke les secrets (exemple pour Kraken + Gmail) :
'''ini
KRAKEN_API_KEY=xxxxxxxx
KRAKEN_API_SECRET=xxxxxxxx
GMAIL_KEY=xxxxxxxx
'''
**⚠ Permissions** :
'''bash
sudo chown dia:dia /opt/dia-core/.env
sudo chmod 600 /opt/dia-core/.env
'''

---

## 6. Lancement & arrêt

- Démarrer :
'''bash
sudo systemctl start dia-core
'''

- Arrêter :
'''bash
sudo systemctl stop dia-core
'''

- Redémarrer :
'''bash
sudo systemctl restart dia-core
'''

- Activer au démarrage :
'''bash
sudo systemctl enable dia-core
'''

- Vérifier l’état :
'''bash
sudo systemctl status dia-core
'''

---

## 7. Vérification post-installation

Exécuter :
'''bash
chmod +x scripts/verify_install.sh
sudo ./scripts/verify_install.sh
'''

Ce script vérifie :
- Présence des fichiers et dossiers
- Permissions et ownership
- Version Python
- Validité du JSON
- Import des modules Python
- Statut du service

---

## 8. Mise à jour

'''bash
cd /opt/dia-core
sudo systemctl stop dia-core
sudo git pull
sudo -u dia /opt/dia-core/.venv/bin/pip install -r requirements.txt
sudo systemctl start dia-core
'''

💡 **Astuce** : tester la mise à jour en 'dry_run' avant de repasser en 'live'.

---

## 9. Logs & supervision

- Localisation : '/var/log/dia-core'
- Format : JSON structuré (rotation + .gz)
- Lire en direct :
'''bash
tail -f /var/log/dia-core/app.log
'''

Surveillance ressources (OverloadGuard) :
- Seuils CPU/RAM/latence configurables
- Réduction automatique du nombre de paires en cas de dépassement
- Envoi d’alerte e-mail

---

## 10. Sécurité

- Utiliser des clés API à permissions minimales
- Restreindre l’accès à '.env'
- Droits stricts sur '/opt/dia-core' et '/var/log/dia-core'
- Utilisateur 'dia' sans shell ('nologin')

---

## 11. Licence

'''
Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
All Rights Reserved — Usage without permission is prohibited
'''

---

## 12. Bonnes pratiques V3

- Activer les tests automatiques ('pytest') avant chaque mise en production
- Linter le code ('ruff') et vérifier le typage ('mypy --strict')
- Documenter les nouvelles fonctions avec des docstrings claires
- Surveiller les alertes e-mail et logs système

---
