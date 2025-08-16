# 📌 Workflow Git — DIA-Core (solo clean)

## 1. Créer une nouvelle branche pour une feature ou un fix
> Nom court et clair : 'feat/' pour une fonctionnalité, 'fix/' pour une correction.

``` bash
git checkout -b feat/nom-de-la-feature

#emplacement de environnement
source .venv/bin/activate

# Ajouter tous les fichiers modifiés
git add .

# Commit clair (type: résumé)
git commit -m "feat: ajout gestion config avec pydantic-settings"

# test avant de fusionner
ruff check src tests --fix
black src tests
mypy src tests --strict --pretty --show-error-codes
pytest -q -vv
xenon --max-absolute A --max-modules A --max-average A src
pylint src --fail-under=10.0
radon cc -s src
bandit -r src
semgrep scan --config auto
pip-audit
deptry src

# Fusionner dans main quand c`est prêt
git checkout main
git merge feat/nom-de-la-feature
git push

#Supprimer la branche locale (optionnel)
git branch -d feat/nom-de-la-feature
